"""Runs RAT from the MATLAB API."""

import json
import tempfile
import warnings
from pathlib import Path

import numpy as np

from ..events import EventTypes, PlotEventData, ProgressEventData, notify
from ..outputs import Results
from ..project import Project
from ..wrappers import MatlabWrapper

RUNNER = """function executeRAT()

cur_dir = pwd;
cd('{rat_path}');
addPaths;
cd(cur_dir);

project = jsonToProject('{project}');
controls = jsonToControls('{control}');
customControls = customControl();
customControls.update(controls);
customControls.filePath = '{ipc_path}';

for i=1:project.customFile.rowCount
    addpath(project.customFile.varTable{{i, 5}});
end
eventManager.register(eventTypes.Message, @(x) logger('{msg_log_path}', x));
eventManager.register(eventTypes.Progress, @(x) logger('{progress_log_path}', x));
eventManager.register(eventTypes.Plot, @(x) logger('{plot_log_path}', x));
global RAT_PROGRESS_UPDATE_FREQ RAT_PROGRESS_UPDATE_COUNT
RAT_PROGRESS_UPDATE_FREQ = {progress_event_freq};
RAT_PROGRESS_UPDATE_COUNT = -1;

[project, results] = RAT(project, customControls);

projectToJson(project, '{project}');
resultsToJson(results, '{result}');
eventManager.clear();
close all
end
"""


CONTROL = """classdef customControl < controlsClass
   properties(Hidden = true)
        filePath = ''
   end
   methods
      function update(obj, controls)
        propNames = properties(controls);
        for i = 1:length(propNames)
          obj.(propNames{i}) = controls.(propNames{i});
        end
      end 
      function path = getIPCFilePath(obj)
        path = obj.filePath;
      end 
   end
end
"""

LOGGER = """function logger(logPath, data)

    if isstruct(data)
        entry = plotDataToJson(data);
    elseif iscell(data)
        global RAT_PROGRESS_UPDATE_FREQ RAT_PROGRESS_UPDATE_COUNT;
        RAT_PROGRESS_UPDATE_COUNT = RAT_PROGRESS_UPDATE_COUNT + 1;
        if rem(RAT_PROGRESS_UPDATE_COUNT, RAT_PROGRESS_UPDATE_FREQ) ~= 0
            return
        end
        entry = [data{1}, ',', num2str(data{2})];
    else
        entry = strip(data, 'right');
    end
    fid = fopen(logPath, "a");
    cleanup = onCleanup(@() fclose(fid));
    fprintf(fid, "%s\\n", entry);
end

function encoded = plotDataToJson(data)
    % Encodes the results into a json file...
    tmpResults = struct();
    for fn = fieldnames(data)'
       tmpResults.(fn{1}) = data.(fn{1});
    end
    
    tmpResults.reflectivity = correctCellArray(tmpResults.reflectivity);
    tmpResults.shiftedData = correctCellArray(tmpResults.shiftedData);
    tmpResults.sldProfiles = makeCellJson(tmpResults.sldProfiles);
    tmpResults.resampledLayers = makeCellJson(tmpResults.resampledLayers);
    
    encoded = jsonencode(tmpResults,ConvertInfAndNaN=false);
    encoded = strrep(encoded, ']"', ']');
    encoded = strrep(encoded, '"[', '[');
end

function outputArray = makeCellJson(cellArray)
    % The jsonencode function flattens 2d cell arrays this is a workaround to
    % avoid flattening by converting to a string array with is not flattened. 
    [row, col] = size(cellArray, [1, 2]);
    outputArray = strings([row, col]);
    for i=1:row
        for j=1:col
            entry = cellArray{i, j};
            if size(entry, 1) == 1
                entry = {entry};
            end
            if col == 1
                entry = {entry};
            end
            outputArray(i, j) = jsonencode(entry);
        end
    end
    if row == 1
        outputArray = {outputArray};
    end

end

function cellArray = correctCellArray(cellArray)
    % Corrects array with single row so its written as 2D array in json 
    [row, col] = size(cellArray, [1, 2]);
    for i=1:row
        for j=1:col
            if size(cellArray{i, j}, 1) == 1
               cellArray{i, j} = {cellArray{i, j}};
            end
        end
    end
end
"""


def run_matlab_directly(
    project, controls, matlab_rat_path, ipc_path="", stdout=None, stderr=None, progress_event_freq=10
):
    """Run User provided MATLAB RAT for the given project and controls inputs.

    Parameters
    ----------
    project : RAT.Project or dict
        The project model (or equivalent json dict), which defines the physical system under study.
    controls : RAT.Controls or dict
        The controls model (or equivalent json dict), which defines algorithmic properties.
    matlab_rat_path : str
        The path to MATLAB RAT folder.
    ipc_path : str, optional
        IPC path for MATLAB to use.
    stdout : io.TextIOBase, optional
        Text stream for MATLAB console output.
    stderr : io.TextIOBase, optional
        Text stream for MATLAB console error output.
     progress_event_freq : int, default: 10
        Update frequency of the progress event.
    """
    if MatlabWrapper.loader is None:
        raise ImportError(MatlabWrapper.loader_error_message) from None

    engine = MatlabWrapper.loader.result()

    with tempfile.TemporaryDirectory() as tmp:
        project_file = Path(tmp, "project.json")
        control_file = Path(tmp, "controls.json")
        result_file = Path(tmp, "results.json")
        runner_file = Path(tmp, "executeRAT.m")
        custom_controls_file = Path(tmp, "customControl.m")
        msg_log_file = Path(tmp, "runner_msg_log.txt")
        progress_log_file = Path(tmp, "runner_progress_log.txt")
        plot_log_file = Path(tmp, "runner_plot_log.txt")
        Path(tmp, "logger.m").write_text(LOGGER)
        with open(custom_controls_file, "w") as f:
            f.write(CONTROL)

        with open(runner_file, "w") as f:
            f.write(
                RUNNER.format(
                    project=project_file,
                    control=control_file,
                    result=result_file,
                    rat_path=matlab_rat_path,
                    ipc_path=ipc_path,
                    msg_log_path=msg_log_file,
                    progress_log_path=progress_log_file,
                    plot_log_path=plot_log_file,
                    progress_event_freq=progress_event_freq,
                )
            )

        controls.save(control_file) if not isinstance(controls, dict) else control_file.write_text(json.dumps(controls))

        with warnings.catch_warnings():  # Avoid warning about relative paths
            warnings.simplefilter("ignore")
            project.save(project_file) if not isinstance(project, dict) else project_file.write_text(
                json.dumps(project)
            )

        engine.addpath(tmp, nargout=0)
        future = engine.executeRAT(nargout=0, stdout=stdout, stderr=stderr, background=True)
        msg_cur_line = 0
        plot_cur_line = 0
        progress_cur_line = 0
        while not future.done():
            if msg_log_file.exists():
                with open(msg_log_file, encoding="utf-8") as handle:
                    handle.seek(msg_cur_line)
                    text = handle.read()
                    msg_cur_line = handle.tell()
                    if text:
                        notify(EventTypes.Message, text)
            if progress_log_file.exists():
                with open(progress_log_file, encoding="utf-8") as handle:
                    handle.seek(progress_cur_line)
                    lines = handle.readlines()
                    progress_cur_line = handle.tell()
                    if lines:
                        msg, percent = lines[-1].strip().rsplit(",", 1)
                        progress_data = ProgressEventData()
                        progress_data.message = msg
                        progress_data.percent = float(percent)
                        notify(EventTypes.Progress, progress_data)
            if plot_log_file.exists():
                with open(plot_log_file, encoding="utf-8") as handle:
                    handle.seek(plot_cur_line)
                    lines = handle.readlines()
                    plot_cur_line = handle.tell()
                    if lines:
                        plot_data = PlotEventData()
                        plot_json = json.loads(lines[-1])
                        plot_data.modelType = plot_json["modelType"]
                        plot_data.reflectivity = [np.array(ref) for ref in plot_json["reflectivity"]]
                        plot_data.shiftedData = [np.array(sd) for sd in plot_json["shiftedData"]]
                        plot_data.sldProfiles = [
                            [np.array(prof) for prof in profiles] for profiles in plot_json["sldProfiles"]
                        ]
                        plot_data.resampledLayers = [
                            [np.array(lay) for lay in layers] for layers in plot_json["resampledLayers"]
                        ]
                        plot_data.dataPresent = plot_json["dataPresent"]
                        plot_data.subRoughs = plot_json["subRoughs"]
                        plot_data.resample = plot_json["resample"]
                        plot_data.contrastNames = plot_json["contrastNames"]
                        notify(EventTypes.Plot, plot_data)
        engine.rmpath(tmp, nargout=0)
        if future.result() is not None:
            raise RuntimeError(future.result())

        project = Project.load(project_file)
        results = Results.load(result_file)
    return project, results
