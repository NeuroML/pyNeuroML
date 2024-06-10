"""
A Neurotune based model optimizer for NeuroML models.

This module provides the `run_optimisation` function that pyNeuroML users can
use to optimise their NeuroML models. It uses the evolutionary computation
framework provided by Neurotune, which is based on the Inspyred optimisation
library's Evolutionary Computation class `inspyred.ec.EvolutionaryComputation`:

- https://neurotune.readthedocs.io/en/latest/index.html
- https://github.com/aarongarrett/inspyred/

It currently supports the jNeuroML and Neuron (via jNeuroML) simulators.

This module also provides the `pynml-tune` command line utility.
Please see the output of `pynml-tune -h` for more information on `pynml-tune`.
"""

from __future__ import annotations, unicode_literals

import argparse
import logging
import os
import os.path
import pprint
import time
import typing
from collections import OrderedDict

from matplotlib import pyplot as plt

from pyneuroml import print_v
from pyneuroml.utils.cli import build_namespace

pp = pprint.PrettyPrinter(indent=4)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


try:
    from neurotune import evaluators, optimizers, utils

    from pyneuroml.tune.NeuroMLController import NeuroMLController
except ImportError:
    logger.warning("Please install optional dependencies to use neurotune features:")
    logger.warning("pip install pyneuroml[tune]")

try:
    from pyelectro import analysis
except ImportError:
    logger.warning("Please install optional dependencies to use analysis features:")
    logger.warning("pip install pyneuroml[analysis]")


DEFAULTS = {
    "simTime": 500,
    "dt": 0.025,
    "analysisStartTime": 0,
    "populationSize": 20,
    "maxEvaluations": 20,
    "numSelected": 10,
    "numOffspring": 20,
    "mutationRate": 0.5,
    "numElites": 1,
    "numParallelEvaluations": 1,
    "cleanup": True,
    "seed": 12345,
    "simulator": "jNeuroML",
    "knownTargetValues": "{}",
    "nogui": False,
    "showPlotAlready": True,
    "saveToFile": False,
    "saveToFileScatter": False,
    "saveToFileHist": False,
    "saveToFileOutput": False,
    "verbose": False,
    "dryRun": False,
    "extraReportInfo": None,
}


def process_args() -> argparse.Namespace:
    """
    Parse command-line arguments for pynml-tune.
    """
    parser = argparse.ArgumentParser(
        description=(
            "A script to tune a NeuroML 2 model against a number of target properties. This corresponds to the pyneuroml.tune.NeuroMLTuner.run_optimisation function in the Python API"
        )
    )

    parser.add_argument(
        "prefix", type=str, metavar="<prefix>", help="Prefix for optimisation run"
    )

    parser.add_argument(
        "neuromlFile",
        type=str,
        metavar="<neuromlFile>",
        help="NeuroML2 file containing model",
    )

    parser.add_argument(
        "target", type=str, metavar="<target>", help="Target in NeuroML2 model"
    )

    parser.add_argument(
        "parameters",
        type=str,
        metavar="<parameters>",
        help="List of parameter to adjust",
    )

    parser.add_argument(
        "maxConstraints",
        type=str,
        metavar="<max_constraints>",
        help="Max values for parameters",
    )

    parser.add_argument(
        "minConstraints",
        type=str,
        metavar="<min_constraints>",
        help="Min values for parameters",
    )

    parser.add_argument(
        "targetData",
        type=str,
        metavar="<targetData>",
        help="List of name/value pairs for properties extracted from data to judge fitness against",
    )

    parser.add_argument(
        "weights",
        type=str,
        metavar="<weights>",
        help="Weights to assign to each target name/value pair",
    )

    parser.add_argument(
        "-simTime",
        type=float,
        metavar="<simTime>",
        default=DEFAULTS["simTime"],
        help="Simulation duration",
    )

    parser.add_argument(
        "-dt",
        type=float,
        metavar="<dt>",
        default=DEFAULTS["dt"],
        help="Simulation timestep",
    )

    parser.add_argument(
        "-analysisStartTime",
        type=float,
        metavar="<analysisStartTime>",
        default=DEFAULTS["analysisStartTime"],
        help="Analysis start time",
    )

    parser.add_argument(
        "-populationSize",
        type=int,
        metavar="<populationSize>",
        default=DEFAULTS["populationSize"],
        help="Population size",
    )

    parser.add_argument(
        "-maxEvaluations",
        type=int,
        metavar="<maxEvaluations>",
        default=DEFAULTS["maxEvaluations"],
        help="Maximum evaluations",
    )

    parser.add_argument(
        "-numSelected",
        type=int,
        metavar="<numSelected>",
        default=DEFAULTS["numSelected"],
        help="Number selected",
    )

    parser.add_argument(
        "-numOffspring",
        type=int,
        metavar="<numOffspring>",
        default=DEFAULTS["numOffspring"],
        help="Number offspring",
    )

    parser.add_argument(
        "-mutationRate",
        type=float,
        metavar="<mutationRate>",
        default=DEFAULTS["mutationRate"],
        help="Mutation rate",
    )

    parser.add_argument(
        "-numElites",
        type=int,
        metavar="<numElites>",
        default=DEFAULTS["numElites"],
        help="Number of elites",
    )

    parser.add_argument(
        "-numParallelEvaluations",
        type=int,
        metavar="<numParallelEvaluations>",
        default=DEFAULTS["numParallelEvaluations"],
        help="Number of evaluations to run in parallel",
    )

    parser.add_argument(
        "-seed",
        type=int,
        metavar="<seed>",
        default=DEFAULTS["seed"],
        help="Seed for optimiser",
    )

    parser.add_argument(
        "-simulator",
        type=str,
        metavar="<simulator>",
        default=DEFAULTS["simulator"],
        help="Simulator to run (options: 'jNeuroML', 'jNeuroML_NEURON')",
    )

    parser.add_argument(
        "-knownTargetValues",
        type=str,
        metavar="<knownTargetValues>",
        help="List of name/value pairs which represent the known values of the target parameters",
    )

    parser.add_argument(
        "-nogui",
        action="store_true",
        default=DEFAULTS["nogui"],
        help="Should GUI elements be supressed?",
    )

    parser.add_argument(
        "-showPlotAlready",
        action="store_true",
        default=DEFAULTS["showPlotAlready"],
        help="Should generated plots be suppressed until show() called?",
    )

    parser.add_argument(
        "-saveToFile",
        action="store_true",
        default=DEFAULTS["saveToFile"],
        help="Name of file to save generated fitness plot to, default: skip.",
    )

    parser.add_argument(
        "-saveToFileScatter",
        action="store_true",
        default=DEFAULTS["saveToFileScatter"],
        help="Name of file to save generated scatter plot to, default: skip.",
    )

    parser.add_argument(
        "-saveToFileHist",
        action="store_true",
        default=DEFAULTS["saveToFileHist"],
        help="Name of file to save generated histogram plot to, default: skip.",
    )

    parser.add_argument(
        "-saveToFileOutput",
        action="store_true",
        default=DEFAULTS["saveToFileOutput"],
        help="Name of file to save generated output plot to, default: skip.",
    )

    parser.add_argument(
        "-verbose",
        action="store_true",
        default=DEFAULTS["verbose"],
        help="Verbose mode",
    )

    parser.add_argument(
        "-dryRun",
        action="store_true",
        default=DEFAULTS["dryRun"],
        help="Dry run; just print setup information",
    )

    parser.add_argument(
        "-extraReportInfo",
        type=str,
        metavar="<extraReportInfo>",
        default=DEFAULTS["extraReportInfo"],
        help='Extra tag/value pairs can be put into the report.json:  -extraReportInfo=["tag":"value"]',
    )

    parser.add_argument(
        "-cleanup",
        action="store_true",
        default=DEFAULTS["cleanup"],
        help="Should (some) generated files, e.g. *.dat, be deleted as optimisation progresses?",
    )

    return parser.parse_args()


def run_optimisation(**kwargs: typing.Any) -> typing.Optional[dict]:
    """Run an optimisation.

    The list of parameters here matches the output of `pynml-tune -h`:

    :param prefix: prefix for tuning test files
    :type prefix: str
    :param neuroml_file: path to main NeuroML file containing the model
    :type neuroml_file: str
    :param target: id of target NeuroML component in model (usually `Network`)
    :type target: str
    :param parameters: list of parameters to adjust
    :type parameters: list(str)
    :param max_constraints: maximum values allowed for parameters
    :type max_constraints: list(float)
    :param min_constraints: minimum values allowed for parameters
    :type min_constraints: list(float)
    :param target_data: name/value pairs for properties extracted from data to judge fitness against
    :type target_data: dict
    :param weights: weights to assign to each target name/value pair
    :type weights: dict
    :param known_target_values: known values of target parameters
    :type known_target_values: dict
    :param sim_time: simulation duration
    :type sim_time: float
    :param dt: simulation timestep
    :type dt: float
    :param population_size: size of population for optimisation
    :type population_size: int
    :param max_evaluations: number of maximum evaluations
    :type max_evaluations: int
    :param num_selected: number selected in each evolution
    :type num_selected: int
    :param num_offspring: number of off sprint in each evolution
    :type num_offspring: int
    :param mutation_rate: the mutation rate for each evolution
    :type mutation_rate: float
    :param num_elites: number of elites
    :type num_elites: int
    :param seed: seed value
    :type seed: int
    :param simulator: simulator to use, currently supported values "jNeuroML", "jNeuroML_NEURON"
    :type simulator: str
    :param nogui: toggle jNeuroML GUI
    :type nogui: bool
    :param show_plot_already: whether plots should be shown as generated
    :type show_plot_already: bool
    :param save_to_file: file name to store fitness plot to, False not to save
    :type save_to_file: str or bool
    :param save_to_file_scatter: file name to store scatter plot to, False to not save
    :type save_to_file_scatter: str or bool
    :param save_to_file_hist: file name to store histogram plot to , False to not save
    :type save_to_file_hist: str or bool
    :param save_to_file_output: file name to store output plot to, False to not save
    :type save_to_file_output: str or bool
    :param dry_run: only print setup information, do not run the optimisation
    :type dry_run: bool
    :param extra_report_info: any extra tag/value pairs to be included in the report
    :type extra_report_info: dict
    :param num_parallel_evaluations: number of parallel evaluations
    :type num_parallel_evaluations: int
    :param cleanup: remove temporary files after completion
    :type cleanup: bool

    :returns: a report of the optimisation in a dictionary.

    """
    a = build_namespace(DEFAULTS, **kwargs)
    return _run_optimisation(a)


def _run_optimisation(a: argparse.Namespace) -> typing.Optional[dict]:
    """Run optimisation.

    Internal function that actually runs the optimisation after
    `run_optimisation` has constructed the necessary namespace.

    The list of parameters here matches the output of `pynml-tune -h`:

    :param prefix: prefix for tuning test files
    :type prefix: str
    :param neuroml_file: path to main NeuroML file containing the model
    :type neuroml_file: str
    :param target: id of target NeuroML component in model (usually `Network`)
    :type target: str
    :param parameters: list of parameters to adjust
    :type parameters: list(str)
    :param max_constraints: maximum values allowed for parameters
    :type max_constraints: list(float)
    :param min_constraints: minimum values allowed for parameters
    :type min_constraints: list(float)
    :param target_data: name/value pairs for properties extracted from data to judge fitness against
    :type target_data: dict
    :param weights: weights to assign to each target name/value pair
    :type weights: dict
    :param known_target_values: known values of target parameters
    :type known_target_values: dict
    :param sim_time: simulation duration
    :type sim_time: float
    :param dt: simulation timestep
    :type dt: float
    :param population_size: size of population for optimisation
    :type population_size: int
    :param max_evaluations: number of maximum evaluations
    :type max_evaluations: int
    :param num_selected: number selected in each evolution
    :type num_selected: int
    :param num_offspring: number of off sprint in each evolution
    :type num_offspring: int
    :param mutation_rate: the mutation rate for each evolution
    :type mutation_rate: float
    :param num_elites: number of elites
    :type num_elites: int
    :param seed: seed value
    :type seed: int
    :param simulator: simulator to use, currently supported values "jNeuroML", "jNeuroML_NEURON"
    :type simulator: str
    :param nogui: toggle jNeuroML GUI
    :type nogui: bool
    :param show_plot_already: whether plots should be shown as generated
    :type show_plot_already: bool
    :param save_to_file: file name to store fitness plots to, False to not save
    :type save_to_file: str or bool
    :param save_to_file_scatter: file name to store scatter plot to, False to not save
    :type save_to_file_scatter: str or bool
    :param save_to_file_hist: file name to store histogram plots to, False to not save
    :type save_to_file_hist: str or bool
    :param save_to_file_output: file name to store output plot to, False to not save
    :type save_to_file_output: str or bool
    :param dry_run: only print setup information, do not run the optimisation
    :type dry_run: bool
    :param extra_report_info: any extra tag/value pairs to be included in the report
    :type extra_report_info: dict
    :param num_parallel_evaluations: number of parallel evaluations
    :type num_parallel_evaluations: int
    :param cleanup: remove temporary files after completion
    :type cleanup: bool

    :returns: a report of the optimisation in a dictionary.

    """
    if isinstance(a.parameters, str):
        a.parameters = parse_list_arg(a.parameters)
    if isinstance(a.min_constraints, str):
        a.min_constraints = parse_list_arg(a.min_constraints)
    if isinstance(a.max_constraints, str):
        a.max_constraints = parse_list_arg(a.max_constraints)
    if isinstance(a.target_data, str):
        a.target_data = parse_dict_arg(a.target_data)
    if isinstance(a.weights, str):
        a.weights = parse_dict_arg(a.weights)
    if isinstance(a.known_target_values, str):
        a.known_target_values = parse_dict_arg(a.known_target_values)
    if isinstance(a.extra_report_info, str):
        a.extra_report_info = parse_dict_arg(a.extra_report_info)

    print_v(
        "====================================================================================="
    )
    print_v("Starting run_optimisation with: ")
    keys = sorted(a.__dict__.keys())

    for key in keys:
        value = a.__dict__[key]
        print_v("  %s = %s%s" % (key, " " * (30 - len(key)), value))
    print_v(
        "====================================================================================="
    )

    if a.dry_run:
        print_v("Dry run; not running optimization...")
        return None

    ref = a.prefix

    run_dir = "NT_%s_%s" % (ref, time.ctime().replace(" ", "_").replace(":", "."))
    os.mkdir(run_dir)

    my_controller = NeuroMLController(
        ref,
        a.neuroml_file,
        a.target,
        a.sim_time,
        a.dt,
        simulator=a.simulator,
        generate_dir=run_dir,
        num_parallel_evaluations=a.num_parallel_evaluations,
        cleanup=a.cleanup,
    )

    peak_threshold = 0

    analysis_var = {
        "peak_delta": 0,
        "baseline": 0,
        "dvdt_threshold": 0,
        "peak_threshold": peak_threshold,
    }

    sim_var = OrderedDict()

    # make an evaluator, using automatic target evaluation:
    my_evaluator = evaluators.NetworkEvaluator(
        controller=my_controller,
        analysis_start_time=a.analysis_start_time,
        analysis_end_time=a.sim_time,
        parameters=a.parameters,
        analysis_var=analysis_var,
        weights=a.weights,
        targets=a.target_data,
    )

    # make an optimizer
    my_optimizer = optimizers.CustomOptimizerA(
        a.max_constraints,
        a.min_constraints,
        my_evaluator,
        population_size=a.population_size,
        max_evaluations=a.max_evaluations,
        num_selected=a.num_selected,
        num_offspring=a.num_offspring,
        num_elites=a.num_elites,
        mutation_rate=a.mutation_rate,
        seeds=None,
        verbose=a.verbose,
    )

    start = time.time()
    # run the optimizer
    best_candidate, fitness = my_optimizer.optimize(
        do_plot=False, seed=a.seed, summary_dir=run_dir
    )

    secs = time.time() - start

    reportj = {}  # type: dict[str, typing.Union[str, float, dict]]
    info = (
        "Ran %s evaluations (pop: %s) in %f seconds (%f mins total; %fs per eval)\n\n"
        % (
            a.max_evaluations,
            a.population_size,
            secs,
            secs / 60.0,
            (secs / a.max_evaluations),
        )
    )
    report = "----------------------------------------------------\n\n" + info

    reportj["comment"] = info
    reportj["time"] = secs

    for key, value in zip(a.parameters, best_candidate):
        sim_var[key] = value

    best_candidate_t, best_candidate_v = my_controller.run_individual(
        sim_var, show=False, cleanup=False
    )

    best_candidate_analysis = analysis.NetworkAnalysis(
        best_candidate_v,
        best_candidate_t,
        analysis_var,
        start_analysis=a.analysis_start_time,
        end_analysis=a.sim_time,
    )

    best_cand_analysis_full = best_candidate_analysis.analyse()
    best_cand_analysis = best_candidate_analysis.analyse(a.weights.keys())

    report += "---------- Best candidate ------------------------------------------\n"
    report += pp.pformat(best_cand_analysis_full) + "\n\n"
    report += "TARGETS: \n"
    report += pp.pformat(a.target_data) + "\n\n"
    report += "TUNED VALUES:\n"
    report += pp.pformat(best_cand_analysis) + "\n\n"
    report += "FITNESS: %f\n\n" % fitness
    report += "FITTEST: %s\n\n" % pp.pformat(dict(sim_var))

    print_v(report)

    reportj["fitness"] = fitness
    reportj["fittest vars"] = dict(sim_var)
    reportj["best_cand_analysis_full"] = best_cand_analysis_full
    reportj["best_cand_analysis"] = best_cand_analysis
    reportj["parameters"] = a.parameters
    reportj["analysis_var"] = analysis_var
    reportj["target_data"] = a.target_data
    reportj["weights"] = a.weights
    reportj["analysis_start_time"] = a.analysis_start_time
    reportj["population_size"] = a.population_size
    reportj["max_evaluations"] = a.max_evaluations
    reportj["num_selected"] = a.num_selected
    reportj["num_offspring"] = a.num_offspring
    reportj["mutation_rate"] = a.mutation_rate
    reportj["num_elites"] = a.num_elites
    reportj["seed"] = a.seed
    reportj["simulator"] = a.simulator

    reportj["sim_time"] = a.sim_time
    reportj["dt"] = a.dt

    reportj["run_directory"] = run_dir
    reportj["reference"] = ref

    if a.extra_report_info:
        for key in a.extra_report_info:
            reportj[key] = a.extra_report_info[key]

    report_file = open("%s/report.json" % run_dir, "w")
    report_file.write(pp.pformat(reportj))
    report_file.close()

    plot_file = open("%s/plotgens.py" % run_dir, "w")
    plot_file.write(
        "from neurotune.utils import plot_generation_evolution\nimport os\n"
    )
    plot_file.write("\n")
    plot_file.write("parameters = %s\n" % a.parameters)
    plot_file.write("\n")
    plot_file.write(
        "curr_dir = os.path.dirname(__file__) if len(os.path.dirname(__file__))>0 else '.'\n"
    )
    plot_file.write(
        "plot_generation_evolution(parameters, individuals_file_name = '%s/ga_individuals.csv'%curr_dir)\n"
    )
    plot_file.close()

    if not a.nogui:
        added = []
        # print("Plotting saved data from %s which are relevant for targets: %s"%(best_candidate_v.keys(), a.target_data.keys()))

        plt.figure()
        plt.get_current_fig_manager().set_window_title(
            "Simulation of fittest individual from run: %s" % ref
        )

        for tref in best_candidate_v.keys():  # a.target_data.keys():
            ref = tref.split(":")[0]
            if ref not in added:
                added.append(ref)
                logging.debug(" - Adding plot of: %s" % ref)
                plt.plot(
                    best_candidate_t,
                    best_candidate_v[ref],
                    label="%s - %i evaluations" % (ref, a.max_evaluations),
                )

        plt.legend()

        # plt.ylim(-80.0,80.0)
        plt.xlim(0.0, a.sim_time)
        plt.title("Models %s" % a.prefix)
        plt.xlabel("Time (ms)")
        plt.ylabel("Membrane potential(mV)")

        if a.save_to_file_output:
            plt.savefig(a.save_to_file_output, dpi=300, bbox_inches="tight")

        utils.plot_generation_evolution(
            sim_var.keys(),
            individuals_file_name="%s/ga_individuals.csv" % run_dir,
            target_values=a.known_target_values,
            show_plot_already=a.show_plot_already,
            save_to_file=a.save_to_file,
            save_to_file_scatter=a.save_to_file_scatter,
            save_to_file_hist=a.save_to_file_hist,
            title_prefix=ref,
        )

        if a.show_plot_already:
            plt.show()

    return reportj


def run_2stage_optimization(
    prefix,
    neuroml_file,
    target,
    parameters,
    max_constraints_1,
    max_constraints_2,
    min_constraints_1,
    min_constraints_2,
    delta_constraints,
    weights_1,
    weights_2,
    target_data_1,
    target_data_2,
    sim_time,
    dt,
    population_size_1,
    population_size_2,
    max_evaluations_1,
    max_evaluations_2,
    num_selected_1,
    num_selected_2,
    num_offspring_1,
    num_offspring_2,
    mutation_rate,
    num_elites,
    simulator,
    nogui,
    show_plot_already,
    seed,
    known_target_values,
    save_to_file_1=False,
    save_to_file_scatter_1=False,
    save_to_file_hist_1=False,
    save_to_file_output_1=False,
    save_to_file_2=False,
    save_to_file_scatter_2=False,
    save_to_file_hist_2=False,
    save_to_file_output_2=False,
    dry_run=False,
    extra_report_info={},
    num_parallel_evaluations=1,
    cleanup=True,
):
    """Run a two stage optimisation.

    This wraps around the `run_optimisation` function to allow a two stage
    optimisation so parameters can be tuned in two sets. For example, it may be
    useful to first tune the passive membrane properties of a cell, and then
    move on to the active entities.

    In order to mark parameters as being optimised in the first stage, please
    set their maximum and minimum constraints for the second tuning stage as
    'x' (instead of providing values). The tuner will then use fitted values
    from the first tuning for these parameters in the second stage.

    :param prefix: prefix for tuning test files
    :type prefix: str
    :param neuroml_file: path to main NeuroML file containing the model
    :type neuroml_file: str
    :param target: id of target NeuroML component in model (usually `Network`)
    :type target: str
    :param parameters: list of parameters to adjust
    :type parameters: list(str)
    :param max_constraints_1: maximum values allowed for parameters for stage 1 tuning
    :type max_constraints_1: list(float)
    :param min_constraints_1: minimum values allowed for parameters for stage 1 tuning
    :type min_constraints_1: list(float)
    :param max_constraints_2: maximum values allowed for parameters for stage 2 tuning
    :type max_constraints_2: list(float, 'x')
    :param min_constraints_2: minimum values allowed for parameters for stage 2 tuning
    :type min_constraints_2: list(float, 'x') to judge fitness against for stage 1 tuning
    :param delta_constraints: value in [0, 1) that allows re-scaling of the maximum/minimum constraints of values fitted in stage 1 being used for stage 2
    :type delta_constraints: float
    :param weights_1: weights to assign to each target name/value pair for stage 1 tuning
    :type weights_1: dict
    :param weights_2: weights to assign to each target name/value pair for stage 2 tuning
    :type weights_2: dict
    :param target_data_1: name/value pairs for properties extracted from data for stage 1 tuning
    :type target_data_1: dict
    :param target_data_2: name/value pairs for properties extracted from data for stage 2 tuning
    :type target_data_2: dict
    :param sim_time: simulation duration
    :type sim_time: float
    :param dt: simulation timestep
    :type dt: float
    :param population_size_1: size of population for stage 1 tuning
    :type population_size_1: int
    :param population_size_2: size of population for stage 2 tuning
    :type population_size_2: int
    :param max_evaluations_1: number of maximum evaluations for stage 1 tuning
    :type max_evaluations_1: int
    :param max_evaluations_2: number of maximum evaluations for stage 2 tuning
    :type max_evaluations_2: int
    :param num_selected_1: number selected in each evolution for stage 1 tuning
    :type num_selected_1: int
    :param num_selected_2: number selected in each evolution for stage 2 tuning
    :type num_selected_2: int
    :param num_offspring_1: number of off sprint in each evolution for stage 1 tuning
    :type num_offspring_1: int
    :param num_offspring_2: number of off sprint in each evolution for stage 2 tuning
    :type num_offspring_2: int
    :param mutation_rate: the mutation rate for each evolution
    :type mutation_rate: float
    :param num_elites: number of elites
    :type num_elites: int
    :param simulator: simulator to use, currently supported values "jNeuroML", "jNeuroML_NEURON"
    :type simulator: str
    :param nogui: toggle jNeuroML GUI
    :type nogui: bool
    :param show_plot_already: whether plots should be shown as generated
    :type show_plot_already: bool
    :param seed: seed value
    :type seed: int
    :param known_target_values: known values of target parameters
    :type known_target_values: dict
    :param save_to_file_1: file name to store stage 1 fitness plot to, False not to save
    :type save_to_file_1: str or bool
    :param save_to_file_scatter_1: file name to store stage 1 scatter plot to, False to not save
    :type save_to_file_scatter_1: str or bool
    :param save_to_file_hist_1: file name to store stage 1 histogram plot to , False to not save
    :type save_to_file_hist_1: str or bool
    :param save_to_file_output_1: file name to store stage 1 output plot to, False to not save
    :type save_to_file_output_1: str or bool
    :param save_to_file_2: file name to store stage 2 fitness plot to, False not to save
    :type save_to_file_2: str or bool
    :param save_to_file_scatter_2: file name to store stage 2 scatter plot to, False to not save
    :type save_to_file_scatter_2: str or bool
    :param save_to_file_hist_2: file name to store stage 2 histogram plot to , False to not save
    :type save_to_file_hist_2: str or bool
    :param save_to_file_output_2: file name to store stage 2 output plot to, False to not save
    :type save_to_file_output_2: str or bool
    :param dry_run: only print setup information, do not run the optimisation
    :type dry_run: bool
    :param extra_report_info: any extra tag/value pairs to be included in the report
    :type extra_report_info: dict
    :param num_parallel_evaluations: number of parallel evaluations
    :type num_parallel_evaluations: int
    :param cleanup: remove temporary files after completion
    :type cleanup: bool

    :returns: a report of the optimisation in a dictionary.

    """

    mut_rat_1 = mutation_rate[0] if isinstance(mutation_rate, list) else mutation_rate

    report1 = run_optimisation(
        prefix="%s_STAGE1" % prefix,
        neuroml_file=neuroml_file,
        target=target,
        parameters=parameters,
        max_constraints=max_constraints_1,
        min_constraints=min_constraints_1,
        weights=weights_1,
        target_data=target_data_1,
        sim_time=sim_time,
        dt=dt,
        population_size=population_size_1,
        max_evaluations=max_evaluations_1,
        num_selected=num_selected_1,
        num_offspring=num_offspring_1,
        mutation_rate=mut_rat_1,
        num_elites=num_elites,
        simulator=simulator,
        nogui=nogui,
        show_plot_already=False,
        save_to_file=save_to_file_1,
        save_to_file_scatter=save_to_file_scatter_1,
        save_to_file_hist=save_to_file_hist_1,
        save_to_file_output=save_to_file_output_1,
        seed=seed,
        known_target_values=known_target_values,
        dry_run=dry_run,
        extra_report_info=extra_report_info,
        num_parallel_evaluations=num_parallel_evaluations,
        cleanup=cleanup,
    )

    for pi in range(len(parameters)):
        param = parameters[pi]
        if max_constraints_2[pi] == "x":
            max_constraints_2[pi] = report1["fittest vars"][param] * (
                1 + delta_constraints
            )
        if min_constraints_2[pi] == "x":
            min_constraints_2[pi] = report1["fittest vars"][param] * (
                1 - delta_constraints
            )

    mut_rat_2 = mutation_rate[1] if isinstance(mutation_rate, list) else mutation_rate

    report2 = run_optimisation(
        prefix="%s_STAGE2" % prefix,
        neuroml_file=neuroml_file,
        target=target,
        parameters=parameters,
        max_constraints=max_constraints_2,
        min_constraints=min_constraints_2,
        weights=weights_2,
        target_data=target_data_2,
        sim_time=sim_time,
        dt=dt,
        population_size=population_size_2,
        max_evaluations=max_evaluations_2,
        num_selected=num_selected_2,
        num_offspring=num_offspring_2,
        mutation_rate=mut_rat_2,
        num_elites=num_elites,
        simulator=simulator,
        nogui=nogui,
        show_plot_already=show_plot_already,
        save_to_file=save_to_file_2,
        save_to_file_scatter=save_to_file_scatter_2,
        save_to_file_hist=save_to_file_hist_2,
        save_to_file_output=save_to_file_output_2,
        seed=seed,
        known_target_values=known_target_values,
        dry_run=dry_run,
        extra_report_info=extra_report_info,
        num_parallel_evaluations=num_parallel_evaluations,
    )

    return report1, report2


def main(args=None):
    if args is None:
        args = process_args()
    run_optimisation(a=args)


def parse_dict_arg(dict_arg: str) -> typing.Optional[dict[str, typing.Any]]:
    """Parse string arguments to dictionaries

    :param dict_arg: string containing list key/value pairs
    :type dict_arg: str
    :returns: dictionary composed of key/value pairs from the provided string
    """
    if not dict_arg:
        return None
    ret = {}  # type: dict[str, typing.Any]
    entries = str(dict_arg[1:-1]).split(",")
    for e in entries:
        if len(e) > 0:
            key = e[: e.rfind(":")]
            value = e[e.rfind(":") + 1 :]
            try:
                ret[key] = float(value)
            except TypeError:
                ret[key] = value
    # print("Command line argument %s parsed as: %s"%(dict_arg,ret))
    return ret


def parse_list_arg(str_list_arg: str) -> typing.Optional[list[typing.Any]]:
    """Parse string arguments to a list

    :param str_list_arg: string containing list
    :type str_list_arg: str
    :returns: list composed of values from the provided string
    """
    if not str_list_arg:
        return None
    ret = []  # type: list[typing.Any]
    entries = str(str_list_arg[1:-1]).split(",")
    for e in entries:
        try:
            ret.append(float(e))
        except ValueError:
            ret.append(e)
    # print("Command line argument %s parsed as: %s"%(str_list_arg,ret))
    return ret


if __name__ == "__main__":
    main()
