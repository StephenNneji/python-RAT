"""Runs RAT from the MATLAB API."""

import os
import tempfile
import warnings
from pathlib import Path

from ..outputs import Results
from ..project import Project
from ..wrappers import MatlabWrapper

RUNNER = """function executeRAT()
project = jsonToProject('{project}');
controls = jsonToControls('{control}');
[project, results] = RAT(project, controls);

projectToJson(project, '{project}');
resultsToJson(results, '{result}');
end
"""


def run_matlab_directly(project, controls, matlab_rat_path):
    """Run User provided MATLAB RAT for the given project and controls inputs.

    Parameters
    ----------
    project : RAT.Project
        The project model, which defines the physical system under study.
    controls : RAT.Controls
        The controls model, which defines algorithmic properties.
    matlab_rat_path : str
        The path to MATLAB RAT folder.
    """
    if MatlabWrapper.loader is None:
        raise ImportError(MatlabWrapper.loader_error_message) from None

    engine = MatlabWrapper.loader.result()
    cur_dir = os.getcwd()

    with tempfile.TemporaryDirectory() as tmp:
        project_file = Path(tmp, "project.json")
        control_file = Path(tmp, "controls.json")
        result_file = Path(tmp, "results.json")
        runner_file = Path(tmp, "executeRAT.m")

        with open(runner_file, "w") as f:
            f.write(RUNNER.format(project=project_file, control=control_file, result=result_file))

        with warnings.catch_warnings():  # Avoid warning about relative paths
            warnings.simplefilter("ignore")
            project.save(project_file)
        controls.save(control_file)

        engine.cd(matlab_rat_path, nargout=0)
        engine.eval("addPaths", nargout=0)
        engine.cd(cur_dir, nargout=0)

        engine.addpath(tmp, nargout=0)
        for file in project.custom_files:
            engine.addpath(str(file.path), nargout=0)

        engine.executeRAT(nargout=0)

        project = Project.load(project_file)
        results = Results.load(result_file)
    return project, results
