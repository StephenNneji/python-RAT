"""Test the inputs module."""

import pathlib
import pickle
from itertools import chain
from unittest import mock

import numpy as np
import pytest

import RATapi
import RATapi.wrappers
from RATapi.inputs import check_indices, make_cells, make_controls, make_input, make_problem
from RATapi.rat_core import Cells, Checks, Control, Limits, Priors, ProblemDefinition
from RATapi.utils.enums import (
    BoundHandling,
    Calculations,
    Display,
    Geometries,
    LayerModels,
    Parallel,
    Procedures,
    TypeOptions,
)
from tests.utils import dummy_function


@pytest.fixture
def standard_layers_project():
    """Add parameters to the default project for a non polarised calculation."""
    test_project = RATapi.Project(
        data=RATapi.ClassList([RATapi.models.Data(name="Test Data", data=np.array([[1.0, 1.0, 1.0]]))]),
    )
    test_project.parameters.append(name="Test Thickness")
    test_project.parameters.append(name="Test SLD")
    test_project.parameters.append(name="Test Roughness")
    test_project.custom_files.append(
        name="Test Custom File",
        filename="python_test.py",
        function_name="dummy_function",
        language="python",
    )
    test_project.layers.append(
        name="Test Layer",
        thickness="Test Thickness",
        SLD="Test SLD",
        roughness="Test Roughness",
    )
    test_project.contrasts.append(
        name="Test Contrast",
        data="Test Data",
        background="Background 1",
        bulk_in="SLD Air",
        bulk_out="SLD D2O",
        scalefactor="Scalefactor 1",
        resolution="Resolution 1",
        model=["Test Layer"],
    )
    return test_project


@pytest.fixture
def domains_project():
    """Add parameters to the default project for a domains calculation."""
    test_project = RATapi.Project(
        calculation=Calculations.Domains,
        data=RATapi.ClassList([RATapi.models.Data(name="Test Data", data=np.array([[1.0, 1.0, 1.0]]))]),
    )
    test_project.parameters.append(name="Test Thickness")
    test_project.parameters.append(name="Test SLD")
    test_project.parameters.append(name="Test Roughness")
    test_project.custom_files.append(name="Test Custom File", filename="matlab_test.m", language="matlab")
    test_project.layers.append(
        name="Test Layer",
        thickness="Test Thickness",
        SLD="Test SLD",
        roughness="Test Roughness",
    )
    test_project.domain_contrasts.append(name="up", model=["Test Layer"])
    test_project.domain_contrasts.append(name="down", model=["Test Layer"])
    test_project.contrasts.append(
        name="Test Contrast",
        data="Test Data",
        background="Background 1",
        bulk_in="SLD Air",
        bulk_out="SLD D2O",
        scalefactor="Scalefactor 1",
        resolution="Resolution 1",
        domain_ratio="Domain Ratio 1",
        model=["down", "up"],
    )
    return test_project


@pytest.fixture
def custom_xy_project():
    """Add parameters to the default project for a non polarised calculation and use the custom xy model."""
    test_project = RATapi.Project(model=LayerModels.CustomXY)
    test_project.parameters.append(name="Test Thickness")
    test_project.parameters.append(name="Test SLD")
    test_project.parameters.append(name="Test Roughness")
    test_project.custom_files.append(name="Test Custom File", filename="cpp_test.dll", language="cpp")
    test_project.contrasts.append(
        name="Test Contrast",
        data="Simulation",
        background="Background 1",
        bulk_in="SLD Air",
        bulk_out="SLD D2O",
        scalefactor="Scalefactor 1",
        resolution="Resolution 1",
        model=["Test Custom File"],
    )
    return test_project


@pytest.fixture
def standard_layers_problem():
    """The expected problem object from "standard_layers_project"."""
    problem = ProblemDefinition()
    problem.TF = Calculations.NonPolarised
    problem.modelType = LayerModels.StandardLayers
    problem.geometry = Geometries.AirSubstrate
    problem.useImaginary = False
    problem.params = [3.0, 0.0, 0.0, 0.0]
    problem.bulkIn = [0.0]
    problem.bulkOut = [6.35e-06]
    problem.qzshifts = []
    problem.scalefactors = [0.23]
    problem.domainRatio = []
    problem.backgroundParams = [1e-06]
    problem.resolutionParams = [0.03]
    problem.contrastBulkIns = [1]
    problem.contrastBulkOuts = [1]
    problem.contrastQzshifts = []
    problem.contrastScalefactors = [1]
    problem.contrastBackgroundParams = [1]
    problem.contrastBackgroundActions = [1]
    problem.contrastResolutionParams = [1]
    problem.contrastCustomFiles = [float("NaN")]
    problem.contrastDomainRatios = [0]
    problem.resample = [False]
    problem.dataPresent = [1]
    problem.oilChiDataPresent = [0]
    problem.numberOfContrasts = 1
    problem.numberOfLayers = 1
    problem.numberOfDomainContrasts = 0
    problem.fitParams = [3.0]
    problem.otherParams = [0.0, 0.0, 0.0, 1e-06, 0.23, 0.0, 6.35e-06, 0.03]
    problem.fitLimits = [[1.0, 5.0]]
    problem.otherLimits = [
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [1e-07, 1e-05],
        [0.02, 0.25],
        [0.0, 0.0],
        [6.2e-06, 6.35e-06],
        [0.01, 0.05],
    ]

    return problem


@pytest.fixture
def domains_problem():
    """The expected problem object from "standard_layers_project"."""
    problem = ProblemDefinition()
    problem.TF = Calculations.Domains
    problem.modelType = LayerModels.StandardLayers
    problem.geometry = Geometries.AirSubstrate
    problem.useImaginary = False
    problem.params = [3.0, 0.0, 0.0, 0.0]
    problem.bulkIn = [0.0]
    problem.bulkOut = [6.35e-06]
    problem.qzshifts = []
    problem.scalefactors = [0.23]
    problem.domainRatio = [0.5]
    problem.backgroundParams = [1e-06]
    problem.resolutionParams = [0.03]
    problem.contrastBulkIns = [1]
    problem.contrastBulkOuts = [1]
    problem.contrastQzshifts = []
    problem.contrastScalefactors = [1]
    problem.contrastBackgroundParams = [1]
    problem.contrastBackgroundActions = [1]
    problem.contrastResolutionParams = [1]
    problem.contrastCustomFiles = [float("NaN")]
    problem.contrastDomainRatios = [1]
    problem.resample = [False]
    problem.dataPresent = [1]
    problem.oilChiDataPresent = [0]
    problem.numberOfContrasts = 1
    problem.numberOfLayers = 1
    problem.numberOfDomainContrasts = 2
    problem.fitParams = [3.0]
    problem.otherParams = [0.0, 0.0, 0.0, 1e-06, 0.23, 0.0, 6.35e-06, 0.03, 0.5]
    problem.fitLimits = [[1.0, 5.0]]
    problem.otherLimits = [
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [1e-07, 1e-05],
        [0.02, 0.25],
        [0.0, 0.0],
        [6.2e-06, 6.35e-06],
        [0.01, 0.05],
        [0.4, 0.6],
    ]

    return problem


@pytest.fixture
def custom_xy_problem():
    """The expected problem object from "custom_xy_project"."""
    problem = ProblemDefinition()
    problem.TF = Calculations.NonPolarised
    problem.modelType = LayerModels.CustomXY
    problem.geometry = Geometries.AirSubstrate
    problem.useImaginary = False
    problem.params = [3.0, 0.0, 0.0, 0.0]
    problem.bulkIn = [0.0]
    problem.bulkOut = [6.35e-06]
    problem.qzshifts = []
    problem.scalefactors = [0.23]
    problem.domainRatio = []
    problem.backgroundParams = [1e-06]
    problem.resolutionParams = [0.03]
    problem.contrastBulkIns = [1]
    problem.contrastBulkOuts = [1]
    problem.contrastQzshifts = []
    problem.contrastScalefactors = [1]
    problem.contrastBackgroundParams = [1]
    problem.contrastBackgroundActions = [1]
    problem.contrastResolutionParams = [1]
    problem.contrastCustomFiles = [1]
    problem.contrastDomainRatios = [0]
    problem.resample = [False]
    problem.dataPresent = [0]
    problem.oilChiDataPresent = [0]
    problem.numberOfContrasts = 1
    problem.numberOfLayers = 0
    problem.numberOfDomainContrasts = 0
    problem.fitParams = [3.0]
    problem.otherParams = [0.0, 0.0, 0.0, 1e-06, 0.23, 0.0, 6.35e-06, 0.03]
    problem.fitLimits = [[1.0, 5.0]]
    problem.otherLimits = [
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [1e-07, 1e-05],
        [0.02, 0.25],
        [0.0, 0.0],
        [6.2e-06, 6.35e-06],
        [0.01, 0.05],
    ]

    return problem


@pytest.fixture
def standard_layers_cells():
    """The expected cells object from "standard_layers_project"."""
    cells = Cells()
    cells.f1 = [[0, 1]]
    cells.f2 = [np.array([[1.0, 1.0, 1.0]])]
    cells.f3 = [[1.0, 1.0]]
    cells.f4 = [[1.0, 1.0]]
    cells.f5 = [[1]]
    cells.f6 = [[2, 3, 4, float("nan"), 2]]
    cells.f7 = ["Substrate Roughness", "Test Thickness", "Test SLD", "Test Roughness"]
    cells.f8 = ["Background Param 1"]
    cells.f9 = ["Scalefactor 1"]
    cells.f10 = []
    cells.f11 = ["SLD Air"]
    cells.f12 = ["SLD D2O"]
    cells.f13 = ["Resolution Param 1"]
    cells.f14 = [dummy_function]
    cells.f15 = [TypeOptions.Constant]
    cells.f16 = [TypeOptions.Constant]
    cells.f17 = [[[]]]
    cells.f18 = []
    cells.f19 = []
    cells.f20 = []
    cells.f21 = ["D2O"]

    return cells


@pytest.fixture
def domains_cells():
    """The expected cells object from "domains_project"."""
    cells = Cells()
    cells.f1 = [[0, 1]]
    cells.f2 = [np.array([[1.0, 1.0, 1.0]])]
    cells.f3 = [[1.0, 1.0]]
    cells.f4 = [[1.0, 1.0]]
    cells.f5 = [[2, 1]]
    cells.f6 = [[2, 3, 4, float("nan"), 2]]
    cells.f7 = ["Substrate Roughness", "Test Thickness", "Test SLD", "Test Roughness"]
    cells.f8 = ["Background Param 1"]
    cells.f9 = ["Scalefactor 1"]
    cells.f10 = []
    cells.f11 = ["SLD Air"]
    cells.f12 = ["SLD D2O"]
    cells.f13 = ["Resolution Param 1"]
    cells.f14 = [dummy_function]
    cells.f15 = [TypeOptions.Constant]
    cells.f16 = [TypeOptions.Constant]
    cells.f17 = [[[]]]
    cells.f18 = [[0, 1], [0, 1]]
    cells.f19 = [[1], [1]]
    cells.f20 = ["Domain Ratio 1"]
    cells.f21 = ["D2O"]

    return cells


@pytest.fixture
def custom_xy_cells():
    """The expected cells object from "custom_xy_project"."""
    cells = Cells()
    cells.f1 = [[0, 1]]
    cells.f2 = [np.empty([0, 3])]
    cells.f3 = [[0.0, 0.0]]
    cells.f4 = [[0.005, 0.7]]
    cells.f5 = [[]]
    cells.f6 = []
    cells.f7 = ["Substrate Roughness", "Test Thickness", "Test SLD", "Test Roughness"]
    cells.f8 = ["Background Param 1"]
    cells.f9 = ["Scalefactor 1"]
    cells.f10 = []
    cells.f11 = ["SLD Air"]
    cells.f12 = ["SLD D2O"]
    cells.f13 = ["Resolution Param 1"]
    cells.f14 = [dummy_function]
    cells.f15 = [TypeOptions.Constant]
    cells.f16 = [TypeOptions.Constant]
    cells.f17 = [[[]]]
    cells.f18 = []
    cells.f19 = []
    cells.f20 = []
    cells.f21 = ["D2O"]

    return cells


@pytest.fixture
def non_polarised_limits():
    """The expected limits object from "standard_layers_project" and "custom_xy_project"."""
    limits = Limits()
    limits.param = [[1.0, 5.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]
    limits.backgroundParam = [[1e-7, 1e-5]]
    limits.qzshift = []
    limits.scalefactor = [[0.02, 0.25]]
    limits.bulkIn = [[0.0, 0.0]]
    limits.bulkOut = [[6.2e-6, 6.35e-6]]
    limits.resolutionParam = [[0.01, 0.05]]
    limits.domainRatio = []

    return limits


@pytest.fixture
def domains_limits():
    """The expected limits object from "domains_project"."""
    limits = Limits()
    limits.param = [[1.0, 5.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]
    limits.backgroundParam = [[1e-7, 1e-5]]
    limits.qzshift = []
    limits.scalefactor = [[0.02, 0.25]]
    limits.bulkIn = [[0.0, 0.0]]
    limits.bulkOut = [[6.2e-6, 6.35e-6]]
    limits.resolutionParam = [[0.01, 0.05]]
    limits.domainRatio = [[0.4, 0.6]]

    return limits


@pytest.fixture
def non_polarised_priors():
    """The expected priors object from "standard_layers_project" and "custom_xy_project"."""
    priors = Priors()
    priors.param = [
        ["Substrate Roughness", RATapi.utils.enums.Priors.Uniform, 0.0, np.inf],
        ["Test Thickness", RATapi.utils.enums.Priors.Uniform, 0.0, np.inf],
        ["Test SLD", RATapi.utils.enums.Priors.Uniform, 0.0, np.inf],
        ["Test Roughness", RATapi.utils.enums.Priors.Uniform, 0.0, np.inf],
    ]
    priors.backgroundParam = [["Background Param 1", RATapi.utils.enums.Priors.Uniform, 0.0, np.inf]]
    priors.qzshift = []
    priors.scalefactor = [["Scalefactor 1", RATapi.utils.enums.Priors.Uniform, 0.0, np.inf]]
    priors.bulkIn = [["SLD Air", RATapi.utils.enums.Priors.Uniform, 0.0, np.inf]]
    priors.bulkOut = [["SLD D2O", RATapi.utils.enums.Priors.Uniform, 0.0, np.inf]]
    priors.resolutionParam = [["Resolution Param 1", RATapi.utils.enums.Priors.Uniform, 0.0, np.inf]]
    priors.domainRatio = []
    priors.priorNames = [
        "Substrate Roughness",
        "Test Thickness",
        "Test SLD",
        "Test Roughness",
        "Background Param 1",
        "Scalefactor 1",
        "SLD Air",
        "SLD D2O",
        "Resolution Param 1",
    ]
    priors.priorValues = [
        [1, 0.0, np.inf],
        [1, 0.0, np.inf],
        [1, 0.0, np.inf],
        [1, 0.0, np.inf],
        [1, 0.0, np.inf],
        [1, 0.0, np.inf],
        [1, 0.0, np.inf],
        [1, 0.0, np.inf],
        [1, 0.0, np.inf],
    ]

    return priors


@pytest.fixture
def domains_priors():
    """The expected priors object from "domains_project"."""
    priors = Priors()
    priors.param = [
        ["Substrate Roughness", RATapi.utils.enums.Priors.Uniform, 0.0, np.inf],
        ["Test Thickness", RATapi.utils.enums.Priors.Uniform, 0.0, np.inf],
        ["Test SLD", RATapi.utils.enums.Priors.Uniform, 0.0, np.inf],
        ["Test Roughness", RATapi.utils.enums.Priors.Uniform, 0.0, np.inf],
    ]
    priors.backgroundParam = [["Background Param 1", RATapi.utils.enums.Priors.Uniform, 0.0, np.inf]]
    priors.qzshift = []
    priors.scalefactor = [["Scalefactor 1", RATapi.utils.enums.Priors.Uniform, 0.0, np.inf]]
    priors.bulkIn = [["SLD Air", RATapi.utils.enums.Priors.Uniform, 0.0, np.inf]]
    priors.bulkOut = [["SLD D2O", RATapi.utils.enums.Priors.Uniform, 0.0, np.inf]]
    priors.resolutionParam = [["Resolution Param 1", RATapi.utils.enums.Priors.Uniform, 0.0, np.inf]]
    priors.domainRatio = [["Domain Ratio 1", RATapi.utils.enums.Priors.Uniform, 0.0, np.inf]]
    priors.priorNames = [
        "Substrate Roughness",
        "Test Thickness",
        "Test SLD",
        "Test Roughness",
        "Background Param 1",
        "Scalefactor 1",
        "SLD Air",
        "SLD D2O",
        "Resolution Param 1",
        "Domain Ratio 1",
    ]
    priors.priorValues = [
        [1, 0.0, np.inf],
        [1, 0.0, np.inf],
        [1, 0.0, np.inf],
        [1, 0.0, np.inf],
        [1, 0.0, np.inf],
        [1, 0.0, np.inf],
        [1, 0.0, np.inf],
        [1, 0.0, np.inf],
        [1, 0.0, np.inf],
        [1, 0.0, np.inf],
    ]

    return priors


@pytest.fixture
def standard_layers_controls():
    """The expected controls object for input to the compiled RAT code given the default inputs and
    "standard_layers_project".
    """
    controls = Control()
    controls.procedure = Procedures.Calculate
    controls.parallel = Parallel.Single
    controls.calcSldDuringFit = False
    controls.resampleMinAngle = 0.9
    controls.resampleNPoints = 50.0
    controls.display = Display.Iter
    controls.xTolerance = 1.0e-6
    controls.funcTolerance = 1.0e-6
    controls.maxFuncEvals = 10000
    controls.maxIterations = 1000
    controls.updateFreq = 1
    controls.updatePlotFreq = 20
    controls.populationSize = 20
    controls.fWeight = 0.5
    controls.crossoverProbability = 0.8
    controls.strategy = 4
    controls.targetValue = 1.0
    controls.numGenerations = 500
    controls.nLive = 150
    controls.nMCMC = 0.0
    controls.propScale = 0.1
    controls.nsTolerance = 0.1
    controls.nSamples = 20000
    controls.nChains = 10
    controls.jumpProbability = 0.5
    controls.pUnitGamma = 0.2
    controls.boundHandling = BoundHandling.Reflect
    controls.adaptPCR = True
    controls.checks.fitParam = [1, 0, 0, 0]
    controls.checks.fitBackgroundParam = [0]
    controls.checks.fitQzshift = []
    controls.checks.fitScalefactor = [0]
    controls.checks.fitBulkIn = [0]
    controls.checks.fitBulkOut = [0]
    controls.checks.fitResolutionParam = [0]
    controls.checks.fitDomainRatio = []

    return controls


@pytest.fixture
def custom_xy_controls():
    """The expected controls object for input to the compiled RAT code given the default inputs and
    "custom_xy_project".
    """
    controls = Control()
    controls.procedure = Procedures.Calculate
    controls.parallel = Parallel.Single
    controls.calcSldDuringFit = True
    controls.resampleMinAngle = 0.9
    controls.resampleNPoints = 50.0
    controls.display = Display.Iter
    controls.xTolerance = 1.0e-6
    controls.funcTolerance = 1.0e-6
    controls.maxFuncEvals = 10000
    controls.maxIterations = 1000
    controls.updateFreq = 1
    controls.updatePlotFreq = 20
    controls.populationSize = 20
    controls.fWeight = 0.5
    controls.crossoverProbability = 0.8
    controls.strategy = 4
    controls.targetValue = 1.0
    controls.numGenerations = 500
    controls.nLive = 150
    controls.nMCMC = 0.0
    controls.propScale = 0.1
    controls.nsTolerance = 0.1
    controls.nSamples = 20000
    controls.nChains = 10
    controls.jumpProbability = 0.5
    controls.pUnitGamma = 0.2
    controls.boundHandling = BoundHandling.Reflect
    controls.adaptPCR = True
    controls.checks.fitParam = [1, 0, 0, 0]
    controls.checks.fitBackgroundParam = [0]
    controls.checks.fitQzshift = []
    controls.checks.fitScalefactor = [0]
    controls.checks.fitBulkIn = [0]
    controls.checks.fitBulkOut = [0]
    controls.checks.fitResolutionParam = [0]
    controls.checks.fitDomainRatio = []

    return controls


@pytest.fixture
def test_checks():
    """The expected checks object from "standard_layers_project", "domains_project" and "custom_xy_project"."""
    checks = Checks()
    checks.fitParam = [1, 0, 0, 0]
    checks.fitBackgroundParam = [0]
    checks.fitQzshift = []
    checks.fitScalefactor = [0]
    checks.fitBulkIn = [0]
    checks.fitBulkOut = [0]
    checks.fitResolutionParam = [0]
    checks.fitDomainRatio = []

    return checks


@pytest.mark.parametrize(
    ["test_project", "test_problem", "test_cells", "test_limits", "test_priors", "test_controls"],
    [
        (
            "standard_layers_project",
            "standard_layers_problem",
            "standard_layers_cells",
            "non_polarised_limits",
            "non_polarised_priors",
            "standard_layers_controls",
        ),
        (
            "custom_xy_project",
            "custom_xy_problem",
            "custom_xy_cells",
            "non_polarised_limits",
            "non_polarised_priors",
            "custom_xy_controls",
        ),
        (
            "domains_project",
            "domains_problem",
            "domains_cells",
            "domains_limits",
            "domains_priors",
            "standard_layers_controls",
        ),
    ],
)
def test_make_input(test_project, test_problem, test_cells, test_limits, test_priors, test_controls, request) -> None:
    """When converting the "project" and "controls", we should obtain the five input objects required for the compiled
    RAT code.
    """
    test_project = request.getfixturevalue(test_project)
    test_problem = request.getfixturevalue(test_problem)
    test_cells = request.getfixturevalue(test_cells)
    test_limits = request.getfixturevalue(test_limits)
    test_priors = request.getfixturevalue(test_priors)
    test_controls = request.getfixturevalue(test_controls)

    parameter_fields = [
        "param",
        "backgroundParam",
        "scalefactor",
        "qzshift",
        "bulkIn",
        "bulkOut",
        "resolutionParam",
        "domainRatio",
    ]

    problem, cells, limits, priors, controls = make_input(test_project, RATapi.Controls())
    problem = pickle.loads(pickle.dumps(problem))
    check_problem_equal(problem, test_problem)
    cells = pickle.loads(pickle.dumps(cells))
    check_cells_equal(cells, test_cells)

    limits = pickle.loads(pickle.dumps(limits))
    for limit_field in parameter_fields:
        assert (getattr(limits, limit_field) == getattr(test_limits, limit_field)).all()

    priors = pickle.loads(pickle.dumps(priors))
    for prior_field in parameter_fields:
        assert getattr(priors, prior_field) == getattr(test_priors, prior_field)

    assert priors.priorNames == test_priors.priorNames
    assert (priors.priorValues == test_priors.priorValues).all()

    controls = pickle.loads(pickle.dumps(controls))
    check_controls_equal(controls, test_controls)


@pytest.mark.parametrize(
    ["test_project", "test_problem"],
    [
        ("standard_layers_project", "standard_layers_problem"),
        ("custom_xy_project", "custom_xy_problem"),
        ("domains_project", "domains_problem"),
    ],
)
def test_make_problem(test_project, test_problem, request) -> None:
    """The problem object should contain the relevant parameters defined in the input project object."""
    test_project = request.getfixturevalue(test_project)
    test_problem = request.getfixturevalue(test_problem)

    problem = make_problem(test_project)
    check_problem_equal(problem, test_problem)


@pytest.mark.parametrize(
    "test_problem",
    [
        "standard_layers_problem",
        "custom_xy_problem",
        "domains_problem",
    ],
)
def test_check_indices(test_problem, request) -> None:
    """The check_indices routine should not raise errors for a properly defined ProblemDefinition object."""
    test_problem = request.getfixturevalue(test_problem)

    check_indices(test_problem)


@pytest.mark.parametrize(
    ["test_problem", "index_list", "bad_value"],
    [
        ("standard_layers_problem", "contrastBulkIns", [0.0]),
        ("standard_layers_problem", "contrastBulkIns", [2.0]),
        ("standard_layers_problem", "contrastBulkOuts", [0.0]),
        ("standard_layers_problem", "contrastBulkOuts", [2.0]),
        ("standard_layers_problem", "contrastScalefactors", [0.0]),
        ("standard_layers_problem", "contrastScalefactors", [2.0]),
        ("standard_layers_problem", "contrastBackgroundParams", [0.0]),
        ("standard_layers_problem", "contrastBackgroundParams", [2.0]),
        ("standard_layers_problem", "contrastResolutionParams", [0.0]),
        ("standard_layers_problem", "contrastResolutionParams", [2.0]),
        ("custom_xy_problem", "contrastBulkIns", [0.0]),
        ("custom_xy_problem", "contrastBulkIns", [2.0]),
        ("custom_xy_problem", "contrastBulkOuts", [0.0]),
        ("custom_xy_problem", "contrastBulkOuts", [2.0]),
        ("custom_xy_problem", "contrastScalefactors", [0.0]),
        ("custom_xy_problem", "contrastScalefactors", [2.0]),
        ("custom_xy_problem", "contrastBackgroundParams", [0.0]),
        ("custom_xy_problem", "contrastBackgroundParams", [2.0]),
        ("custom_xy_problem", "contrastResolutionParams", [0.0]),
        ("custom_xy_problem", "contrastResolutionParams", [2.0]),
        ("domains_problem", "contrastBulkIns", [0.0]),
        ("domains_problem", "contrastBulkIns", [2.0]),
        ("domains_problem", "contrastBulkOuts", [0.0]),
        ("domains_problem", "contrastBulkOuts", [2.0]),
        ("domains_problem", "contrastScalefactors", [0.0]),
        ("domains_problem", "contrastScalefactors", [2.0]),
        ("domains_problem", "contrastDomainRatios", [0.0]),
        ("domains_problem", "contrastDomainRatios", [2.0]),
        ("domains_problem", "contrastBackgroundParams", [0.0]),
        ("domains_problem", "contrastBackgroundParams", [2.0]),
        ("domains_problem", "contrastResolutionParams", [0.0]),
        ("domains_problem", "contrastResolutionParams", [2.0]),
    ],
)
def test_check_indices_error(test_problem, index_list, bad_value, request) -> None:
    """The check_indices routine should raise an IndexError if a contrast list contains an index that is out of the
    range of the corresponding parameter list in a ProblemDefinition object.
    """
    param_list = {
        "contrastBulkIns": "bulkIn",
        "contrastBulkOuts": "bulkOut",
        "contrastScalefactors": "scalefactors",
        "contrastDomainRatios": "domainRatio",
        "contrastBackgroundParams": "backgroundParams",
        "contrastResolutionParams": "resolutionParams",
    }

    test_problem = request.getfixturevalue(test_problem)
    setattr(test_problem, index_list, bad_value)

    with pytest.raises(
        IndexError,
        match=f'The problem field "{index_list}" contains: {bad_value[0]}, which lie '
        f'outside of the range of "{param_list[index_list]}"',
    ):
        check_indices(test_problem)


@pytest.mark.parametrize(
    ["test_project", "test_cells"],
    [
        ("standard_layers_project", "standard_layers_cells"),
        ("custom_xy_project", "custom_xy_cells"),
        ("domains_project", "domains_cells"),
    ],
)
def test_make_cells(test_project, test_cells, request) -> None:
    """The cells object should be populated according to the input project object."""
    test_project = request.getfixturevalue(test_project)
    test_cells = request.getfixturevalue(test_cells)
    cells = make_cells(test_project)
    check_cells_equal(cells, test_cells)


def test_get_python_handle():
    path = pathlib.Path(__file__).parent.resolve()
    assert RATapi.inputs.get_python_handle("utils.py", "dummy_function", path).__code__ == dummy_function.__code__


def test_make_controls(standard_layers_controls, test_checks) -> None:
    """The controls object should contain the full set of controls parameters, with the appropriate set defined by the
    input controls.
    """
    controls = make_controls(RATapi.Controls(), test_checks)
    check_controls_equal(controls, standard_layers_controls)


def check_problem_equal(actual_problem, expected_problem) -> None:
    """Compare two instances of the "problem" object for equality."""
    scalar_fields = [
        "TF",
        "modelType",
        "geometry",
        "useImaginary",
        "numberOfContrasts",
        "numberOfLayers",
        "numberOfDomainContrasts",
    ]

    array_fields = [
        "params",
        "backgroundParams",
        "qzshifts",
        "scalefactors",
        "bulkIn",
        "bulkOut",
        "resolutionParams",
        "domainRatio",
        "contrastBackgroundParams",
        "contrastBackgroundActions",
        "contrastQzshifts",
        "contrastScalefactors",
        "contrastBulkIns",
        "contrastBulkOuts",
        "contrastResolutionParams",
        "contrastDomainRatios",
        "resample",
        "dataPresent",
        "oilChiDataPresent",
        "fitParams",
        "otherParams",
        "fitLimits",
        "otherLimits",
    ]

    for scalar_field in scalar_fields:
        assert getattr(actual_problem, scalar_field) == getattr(expected_problem, scalar_field)
    for array_field in array_fields:
        assert (getattr(actual_problem, array_field) == getattr(expected_problem, array_field)).all()

    # Need to account for "NaN" entries in contrastCustomFiles field
    assert (actual_problem.contrastCustomFiles == expected_problem.contrastCustomFiles).all() or [
        "NaN" if np.isnan(el) else el for el in actual_problem.contrastCustomFiles
    ] == ["NaN" if np.isnan(el) else el for el in expected_problem.contrastCustomFiles]


def check_cells_equal(actual_cells, expected_cells) -> None:
    """Compare two instances of the "cells" object for equality."""
    assert actual_cells.f1 == expected_cells.f1

    # Need to test equality of the numpy arrays separately
    for a, b in zip(actual_cells.f2, expected_cells.f2):
        assert (a == b).all()

    # f6 may contain "NaN" values, so consider separately
    assert actual_cells.f6 == expected_cells.f6 or [
        "NaN" if np.isnan(el) else el for entry in actual_cells.f6 for el in entry
    ] == ["NaN" if np.isnan(el) else el for entry in expected_cells.f6 for el in entry]

    mocked_matlab_future = mock.MagicMock()
    mocked_engine = mock.MagicMock()
    mocked_matlab_future.result.return_value = mocked_engine
    with (
        mock.patch.object(
            RATapi.wrappers.MatlabWrapper,
            "loader",
            mocked_matlab_future,
        ),
        mock.patch.object(RATapi.rat_core, "DylibEngine", mock.MagicMock()),
        mock.patch.object(
            RATapi.inputs,
            "get_python_handle",
            mock.MagicMock(return_value=dummy_function),
        ),
        mock.patch.object(
            RATapi.wrappers.MatlabWrapper,
            "getHandle",
            mock.MagicMock(return_value=dummy_function),
        ),
        mock.patch.object(RATapi.wrappers.DylibWrapper, "getHandle", mock.MagicMock(return_value=dummy_function)),
    ):
        assert list(actual_cells.f14) == expected_cells.f14

    for index in chain(range(3, 6), range(7, 14), range(15, 21)):
        field = f"f{index}"
        assert getattr(actual_cells, field) == getattr(expected_cells, field)


def check_controls_equal(actual_controls, expected_controls) -> None:
    """Compare two instances of the "controls" object used as input for the compiled RAT code for equality."""
    controls_fields = [
        "procedure",
        "parallel",
        "calcSldDuringFit",
        "resampleMinAngle",
        "resampleNPoints",
        "display",
        "xTolerance",
        "funcTolerance",
        "maxFuncEvals",
        "maxIterations",
        "updateFreq",
        "updatePlotFreq",
        "populationSize",
        "fWeight",
        "crossoverProbability",
        "strategy",
        "targetValue",
        "numGenerations",
        "nLive",
        "nMCMC",
        "propScale",
        "nsTolerance",
        "nSamples",
        "nChains",
        "jumpProbability",
        "pUnitGamma",
        "boundHandling",
        "adaptPCR",
    ]
    checks_fields = [
        "fitParam",
        "fitBackgroundParam",
        "fitQzshift",
        "fitScalefactor",
        "fitBulkIn",
        "fitBulkOut",
        "fitResolutionParam",
        "fitDomainRatio",
    ]

    for field in controls_fields:
        assert getattr(actual_controls, field) == getattr(expected_controls, field)
    for field in checks_fields:
        assert (getattr(actual_controls.checks, field) == getattr(expected_controls.checks, field)).all()
