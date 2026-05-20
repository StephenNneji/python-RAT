"""Runs RAT from the MATLAB API."""

import json
import tempfile
import warnings
from pathlib import Path

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
if any(strcmpi(controls.procedure, {{procedures.DE.value, procedures.Simplex.value}}))
    disp("hello")
    useLivePlot(1);
end
for i=1:project.customFile.rowCount
    addpath(project.customFile.varTable{{i, 5}});
end
[project, results] = RAT(project, controls);

projectToJson(project, '{project}');
resultsToJson(results, '{result}');
close all
end
"""


def run_matlab_directly(project, controls, matlab_rat_path, stdout=None, stderr=None):
    """Run User provided MATLAB RAT for the given project and controls inputs.

    Parameters
    ----------
    project : RAT.Project or dict
        The project model (or equivalent json dict), which defines the physical system under study.
    controls : RAT.Controls or dict
        The controls model (or equivalent json dict), which defines algorithmic properties.
    matlab_rat_path : str
        The path to MATLAB RAT folder.
    stdout : io.TextIOBase, optional
        Text stream for MATLAB console output
    stderr : io.TextIOBase, optional
        Text stream for MATLAB console error output
    """
    if MatlabWrapper.loader is None:
        raise ImportError(MatlabWrapper.loader_error_message) from None

    engine = MatlabWrapper.loader.result()

    with tempfile.TemporaryDirectory() as tmp:
        project_file = Path(tmp, "project.json")
        control_file = Path(tmp, "controls.json")
        result_file = Path(tmp, "results.json")
        runner_file = Path(tmp, "executeRAT.m")

        with open(runner_file, "w") as f:
            f.write(
                RUNNER.format(project=project_file, control=control_file, result=result_file, rat_path=matlab_rat_path)
            )

        controls.save(control_file) if not isinstance(controls, dict) else control_file.write_text(json.dumps(controls))

        with warnings.catch_warnings():  # Avoid warning about relative paths
            warnings.simplefilter("ignore")
            project.save(project_file) if not isinstance(project, dict) else project_file.write_text(
                json.dumps(project)
            )

        engine.addpath(tmp, nargout=0)
        engine.executeRAT(nargout=0, stdout=stdout, stderr=stderr)
        engine.rmpath(tmp, nargout=0)

        project = Project.load(project_file)
        results = Results.load(result_file)
    return project, results
