#!/usr/bin/env python
"""

Python wrapper around jnml command.
(Thanks to Werner van Geit for an initial version of a python wrapper for jnml.)

For convenience and backward compatibility, this also includes various
helper/utility methods that are defined in other modules in the package. But
please try and use these from their defined locations as these imports will
gradually be removed from here in the future.
"""

# py3.7, 3.8 require this to use standard collections as generics
from __future__ import absolute_import, annotations, unicode_literals

import logging
import os
import shutil
import sys
import typing
import warnings

import neuroml

import lems
import lems.model.model as lems_model
from pyneuroml import DEFAULTS, JNEUROML_VERSION, __version__
from pyneuroml.errors import ARGUMENT_ERR, UNKNOWN_ERR
from pyneuroml.swc.ExportSWC import convert_to_swc
from pyneuroml.utils import extract_lems_definition_files

# these imports are included for backwards compatibility
from pyneuroml.utils.units import *
from pyneuroml.modelgraphs import *
from pyneuroml.runners import *
from pyneuroml.validators import *
from pyneuroml.io import *
from pyneuroml.utils.info import *
from pyneuroml.utils.misc import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

matplotlib_imported = False
for k in sys.modules.keys():
    if "matplotlib" in k:
        matplotlib_imported = True
        break

if matplotlib_imported is True:
    # to maintain API compatibility:
    # so that existing scripts that use: from pynml import generate_plot
    # continue to work
    from pyneuroml.plot import generate_interactive_plot, generate_plot  # noqa
else:
    # Define a new method, which only gets called if a user explicitly tries to
    # run generate_plot (and so requires matplotlib). If it's never called, matplotlib
    # doesn't get imported

    def generate_plot(*args, **kwargs):  # type: ignore
        try:
            import matplotlib  # noqa

            from pyneuroml.plot import generate_plot as gp

            return gp(*args, **kwargs)

        except Exception:
            logger.error("Matplotlib not found!")
            warnings.warn(
                """
                Please note that these plotting methods will be removed from the pynml
                module in the future. Please import plotting methods explicitly from
                the pyneuroml.plot sub module.
                """,
                FutureWarning,
                stacklevel=2,
            )

    def generate_interactive_plot(*args, **kwargs):  # type: ignore
        try:
            import matplotlib  # noqa

            from pyneuroml.plot import generate_interactive_plot as gp

            return gp(*args, **kwargs)

        except Exception:
            logger.error("Matplotlib not found!")
            warnings.warn(
                """
                Please note that these plotting methods will be removed from the pynml
                module in the future. Please import plotting methods explicitly from
                the pyneuroml.plot sub module.
                """,
                FutureWarning,
                stacklevel=2,
            )


version_string = "pyNeuroML v{} (libNeuroML v{}, jNeuroML v{})".format(
    __version__, neuroml.__version__, JNEUROML_VERSION
)


def _parse_arguments():
    """Parse command line arguments"""

    import argparse

    try:
        from neuromllite.GraphVizHandler import engines

        engine_info = "\nAvailable engines: %s\n" % str(engines)
    except Exception:
        engine_info = ""

    parser = argparse.ArgumentParser(
        description="Python utilities for NeuroML2",
        usage=(
            "pynml [-h|--help] [<shared options>] "
            "<one of the mutually-exclusive options>"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("-version", help="Print version and exit", action="store_true")

    shared_options = parser.add_argument_group(
        title="Shared options",
        description=(
            "These options can be added to any of the " "mutually-exclusive options"
        ),
    )

    shared_options.add_argument(
        "-verbose",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Verbose output (default: WARNING)",
    )
    shared_options.add_argument(
        "-java_max_memory",
        metavar="MAX",
        default=DEFAULTS["default_java_max_memory"],
        help=(
            "Java memory for jNeuroML, e.g. 400M, 2G (used in\n"
            "-Xmx argument to java)"
        ),
    )
    shared_options.add_argument(
        "-nogui",
        action="store_true",
        default=DEFAULTS["nogui"],
        help=("Suppress GUI,\n" "i.e. show no plots, just save results"),
    )

    shared_options.add_argument(
        "input_files",
        type=str,
        nargs="*",
        metavar="<LEMS/NeuroML 2/SBML/SEDML file(s)>",
        help="LEMS/NeuroML 2/SBML/SEDML file(s) to process",
    )

    mut_exc_opts_grp = parser.add_argument_group(
        title="Mutually-exclusive options",
        description="Only one of these options can be selected",
    )
    mut_exc_opts = mut_exc_opts_grp.add_mutually_exclusive_group(required=False)  # noqa: E501

    mut_exc_opts.add_argument(
        "-sedml",
        action="store_true",
        help=(
            "(Via jNeuroML) Load a LEMS file, and convert\n"
            "simulation settings (duration, dt, what to save)\n"
            "to SED-ML format"
        ),
    )
    mut_exc_opts.add_argument(
        "-neuron",
        nargs=argparse.REMAINDER,
        help=(
            "(Via jNeuroML) Load a LEMS file, and convert it to\n"
            "NEURON format.\n"
            "The full format of the '-neuron' option is:\n"
            "-neuron [-nogui] [-run] [-outputdir dir] <LEMS file>\n"
            "    -nogui\n"
            "        do not generate graphical elements in NEURON,\n"
            "        just run, save data, and quit\n"
            "    -run\n"
            "        compile NMODL files and run the main NEURON\n"
            "        hoc file (Linux only currently)\n"
            "    -outputdir <dir>\n"
            "        generate NEURON files in directory <dir>\n"
            "    <LEMS file>\n"
            "        the LEMS file to use"
        ),
    )
    mut_exc_opts.add_argument(
        "-run-tellurium",
        nargs=argparse.REMAINDER,
        help=(
            "Load a SEDML file, and run it using tellurium:\n"
            "<SEDML file> -run-tellurium [-outputdir dir]\n"
            "    <SEDML file>\n"
            "        the SEDML file to use\n"
            "    -outputdir <dir>\n"
            "        save any output reports in directory <dir>\n"
            "        default is current directory ie '.'\n"
            "        use 'none' to disable output altogether"
        ),
    )
    mut_exc_opts.add_argument(
        "-netpyne",
        nargs=argparse.REMAINDER,
        help=(
            "(Via jNeuroML) Load a LEMS file, and convert it to\n"
            "NetPyNE format.\n"
            "The full format of the '-netpyne' option is:\n"
            "-netpyne [-run] [-outputdir dir] [-np cores] <LEMS file>\n"
            "    -run\n"
            "        compile NMODL files and run the NetPyNE\n"
            "        simulation (Linux only currently)\n"
            "    -outputdir <dir>\n"
            "        generate NEURON files in directory <dir>\n"
            "    -np <cores>\n"
            "        number of cores to run with (if using MPI)\n"
            "    -json\n"
            "        generate network as NetPyNE JSON\n"
            "    <LEMS file>\n"
            "        the LEMS file to use"
        ),
    )

    mut_exc_opts.add_argument(
        "-eden",
        nargs=argparse.REMAINDER,
        help=(
            "Load a LEMS file, and generate a\n"
            "Python script to load and execute it in EDEN"
        ),
    )
    mut_exc_opts.add_argument(
        "-svg",
        action="store_true",
        help=(
            "(Via jNeuroML) Convert NeuroML2 file (network & cells)\n"
            "to SVG format view of 3D structure"
        ),
    )
    mut_exc_opts.add_argument(
        "-png",
        action="store_true",
        help=(
            "(Via jNeuroML) Convert NeuroML2 file (network & cells)\n"
            "to PNG format view of 3D structure"
        ),
    )
    mut_exc_opts.add_argument(
        "-dlems",
        action="store_true",
        help=(
            "(Via jNeuroML) Load a LEMS file, and convert it\n"
            "to dLEMS format, a distilled form of LEMS in JSON"
        ),
    )
    mut_exc_opts.add_argument(
        "-vertex",
        action="store_true",
        help=("(Via jNeuroML) Load a LEMS file, and convert it\n" "to VERTEX format"),
    )
    mut_exc_opts.add_argument(
        "-xpp",
        action="store_true",
        help=("(Via jNeuroML) Load a LEMS file, and convert it\n" "to XPPAUT format"),
    )
    mut_exc_opts.add_argument(
        "-dnsim",
        action="store_true",
        help=("(Via jNeuroML) Load a LEMS file, and convert it\n" "to DNsim format"),
    )
    mut_exc_opts.add_argument(
        "-brian",
        action="store_true",
        help=("(Via jNeuroML) Load a LEMS file, and convert it\n" "to Brian format"),
    )
    mut_exc_opts.add_argument(
        "-brian2",
        action="store_true",
        help=("(Via jNeuroML) Load a LEMS file, and convert it\n" "to Brian2 format"),
    )
    # TODO: add run_lems_with_jneuroml_moose API function
    mut_exc_opts.add_argument(
        "-moose",
        action="store_true",
        help=("(Via jNeuroML) Load a LEMS file, and convert it\n" "to Moose format"),
    )
    mut_exc_opts.add_argument(
        "-sbml",
        action="store_true",
        help=("(Via jNeuroML) Load a LEMS file, and convert it\n" "to SBML format"),
    )
    mut_exc_opts.add_argument(
        "-sbml-sedml",
        action="store_true",
        help=(
            "(Via jNeuroML) Load a LEMS file, and convert it\n"
            "to SBML format with a SED-ML file describing the experiment to run"
        ),
    )
    mut_exc_opts.add_argument(
        "-matlab",
        action="store_true",
        help=("(Via jNeuroML) Load a LEMS file, and convert it\n" "to MATLAB format"),
    )
    mut_exc_opts.add_argument(
        "-cvode",
        action="store_true",
        help=(
            "(Via jNeuroML) Load a LEMS file, and convert it\n"
            "to C format using CVODE package"
        ),
    )
    mut_exc_opts.add_argument(
        "-nineml",
        action="store_true",
        help=("(Via jNeuroML) Load a LEMS file, and convert it\n" "to NineML format"),
    )
    mut_exc_opts.add_argument(
        "-spineml",
        action="store_true",
        help=("(Via jNeuroML) Load a LEMS file, and convert it\n" "to SpineML format"),
    )
    mut_exc_opts.add_argument(
        "-sbml-import",
        metavar=("<SBML file>", "duration", "dt"),
        nargs=3,
        help=(
            "(Via jNeuroML) Load a SBML file, and convert it\n"
            "to LEMS format using values for duration & dt\n"
            "in ms (ignoring SBML units)"
        ),
    )
    mut_exc_opts.add_argument(
        "-sbml-import-units",
        metavar=("<SBML file>", "duration", "dt"),
        nargs=3,
        help=(
            "(Via jNeuroML) Load a SBML file, and convert it\n"
            "to LEMS format using values for duration & dt\n"
            "in ms (attempt to extract SBML units; ensure units\n"
            "are valid in the SBML!)"
        ),
    )
    mut_exc_opts.add_argument(
        "-vhdl",
        metavar=("neuronid", "<LEMS file>"),
        nargs=2,
        help=("(Via jNeuroML) Load a LEMS file, and convert it\n" "to VHDL format"),
    )
    mut_exc_opts.add_argument(
        "-graph",
        metavar=("level"),
        nargs=1,
        help=(
            "Load a NeuroML file, and convert it to a graph using GraphViz.\n"
            "Detail is set by level (min20..0..20, where min implies negative)\n"
            "An optional single letter suffix can be used to select engine\n"
            "Example: 1d for level 1, using the dot engine" + engine_info
        ),
    )
    mut_exc_opts.add_argument(
        "-lems-graph",
        action="store_true",
        help=(
            "(Via jNeuroML) Load LEMS file, and convert it to a \n"
            "graph using GraphViz."
        ),
    )
    mut_exc_opts.add_argument(
        "-matrix",
        metavar=("level"),
        nargs=1,
        help=(
            "Load a NeuroML file, and convert it to a matrix displaying\n"  # noqa: E501
            "connectivity. Detail is set by level (1, 2, etc.)"
        ),
    )
    mut_exc_opts.add_argument(
        "-validate",
        action="store_true",
        help=("(Via jNeuroML) Validate NeuroML2 file(s) against the\n" "latest Schema"),
    )
    mut_exc_opts.add_argument(
        "-validatev1",
        action="store_true",
        help=("(Via jNeuroML) Validate NeuroML file(s) against the\n" "v1.8.1 Schema"),
    )
    mut_exc_opts.add_argument(
        "-validate-sbml",
        action="store_true",
        help=("Validate SBML file(s), unit consistency failure generates a warning"),
    )
    mut_exc_opts.add_argument(
        "-validate-sbml-units",
        action="store_true",
        help=("Validate SBML file(s), unit consistency failure generates an error"),
    )
    mut_exc_opts.add_argument(
        "-validate-sedml",
        action="store_true",
        help=("Validate SEDML file(s)"),
    )
    mut_exc_opts.add_argument(
        "-swc",
        action="store_true",
        help=("Load NeuroML file(s), and convert it to swc format\n"),
    )

    return parser.parse_args()


def list_exposures(
    nml_doc_fn: str, substring: str = ""
) -> typing.Union[
    dict[lems.model.component.Component, typing.List[lems.model.component.Exposure]],
    None,
]:
    """List exposures in a NeuroML model document file.

    This wraps around `lems.model.list_exposures` to list the exposures in a
    NeuroML2 model. The only difference between the two is that the
    `lems.model.list_exposures` function is not aware of the NeuroML2 component
    types (since it's for any LEMS models in general), but this one is.

    :param nml_doc_fn: NeuroML2 file to list exposures for
    :type nml_doc: str
    :param substring: substring to match for in component names
    :type substring: str
    :returns: dictionary of components and their exposures.

    The returned dictionary is of the form:

    ..
        {
            "component": ["exp1", "exp2"]
        }

    """
    return get_standalone_lems_model(nml_doc_fn).list_exposures(substring)


def list_recording_paths_for_exposures(
    nml_doc_fn: str, substring: str = "", target: str = ""
) -> typing.List[str]:
    """List the recording path strings for exposures.

    This wraps around `lems.model.list_recording_paths` to list the recording
    paths in the given NeuroML2 model. The only difference between the two is
    that the `lems.model.list_recording_paths` function is not aware of the
    NeuroML2 component types (since it's for any LEMS models in general), but
    this one is.

    :param nml_doc_fn: NeuroML2 file to list recording paths for
    :type nml_doc: str
    :param substring: substring to match component ids against
    :type substring: str
    :returns: list of recording paths

    """
    return get_standalone_lems_model(nml_doc_fn).list_recording_paths_for_exposures(
        substring, target
    )


def get_standalone_lems_model(nml_doc_fn: str) -> lems_model.Model:
    """Get the complete, expanded LEMS model.

    This function takes a NeuroML2 file, includes all the NeuroML2 LEMS
    definitions in it and generates the complete, standalone LEMS model.

    :param nml_doc_fn: name of NeuroML file to expand
    :type nml_doc_fn: str
    :returns: complete LEMS model
    """
    new_lems_model = lems_model.Model(
        include_includes=True, fail_on_missing_includes=True
    )
    if logger.level < logging.INFO:
        new_lems_model.debug = True
    else:
        new_lems_model.debug = False
    neuroml2_defs_dir = extract_lems_definition_files()
    filelist = os.listdir(neuroml2_defs_dir)
    # Remove the temporary directory
    for nml_lems_f in filelist:
        new_lems_model.include_file(neuroml2_defs_dir + nml_lems_f, [neuroml2_defs_dir])
    new_lems_model.include_file(nml_doc_fn, [""])
    shutil.rmtree(neuroml2_defs_dir[: -1 * len("NeuroML2CoreTypes/")])
    return new_lems_model


def version_info(detailed: bool = False):
    """Print version information.

    :param detailed: also print information about installed simulation engines
    :type detailed: bool

    """
    print(version_string)
    if detailed:
        print("")
        print(f"- Python: {sys.version}")
        try:
            import neuron

            print(f"- NEURON: {neuron.version}")
        except ImportError:
            print("- NEURON: ?")
        try:
            import netpyne

            print(f"- NetPyNE: {netpyne.__version__}")
        except ImportError:
            print("- NetPyNE: ?")
        try:
            import eden_simulator

            print(f"- EDEN: {eden_simulator.__version__}")
        except ImportError:
            print("- EDEN: ?")
        try:
            import brian2

            print(f"- Brian2: {brian2.__version__}")
        except ImportError:
            print("- Brian2: ?")


def _evaluate_arguments(args):
    logger.debug("    ====  Args: %s" % args)
    global DEFAULTS

    if args.version:
        if args.verbose == "DEBUG":
            version_info(True)
        else:
            version_info()
        return True

    if args.verbose:
        logger.setLevel(logging.getLevelName(args.verbose))
    # if the user uses INFO or DEBUG, make the commands we call also print
    # extra inputs
    if args.verbose in ["DEBUG", "INFO"]:
        DEFAULTS["v"] = True

    pre_args = ""
    post_args = ""
    exit_on_fail = True

    # Deal with the SBML validation option which doesn't call run_jneuroml
    if args.validate_sbml or args.validate_sbml_units:
        try:
            from pyneuroml.sbml import validate_sbml_files
        except Exception:
            logger.critical("Unable to import pyneuroml.sbml")
            sys.exit(UNKNOWN_ERR)

        if not len(args.input_files) >= 1:
            logger.critical("No input files specified")
            sys.exit(ARGUMENT_ERR)

        if args.validate_sbml_units:
            # A failed unit consistency check generates an error
            strict_units = True
        else:
            # A failed unit consistency check generates only a warning
            strict_units = False

        try:
            result = validate_sbml_files(args.input_files, strict_units)
        except Exception as e:
            logger.critical(f"validate_sbml_files failed with {str(e)}")
            sys.exit(UNKNOWN_ERR)

        if result:
            # All files validated ok (with possible warnings but no errors)
            sys.exit(0)

        # Errors of some kind were found in one or more files
        logger.error("one or more SBML files failed to validate")
        sys.exit(UNKNOWN_ERR)

    # Deal with the SEDML validation option which doesn't call run_jneuroml
    if args.validate_sedml:
        try:
            from pyneuroml.sedml import validate_sedml_files
        except Exception:
            logger.critical("Unable to import pyneuroml.sedml")
            sys.exit(UNKNOWN_ERR)

        if not len(args.input_files) >= 1:
            logger.critical("No input files specified")
            sys.exit(ARGUMENT_ERR)

        try:
            result = validate_sedml_files(args.input_files)
        except Exception as e:
            logger.critical(f"validate_sedml_files failed with {str(e)}")
            sys.exit(UNKNOWN_ERR)

        if result:
            # All files validated ok (with possible warnings but no errors)
            sys.exit(0)

        # Errors of some kind were found in one or more files
        logger.error("one or more SEDML files failed to validate")
        sys.exit(UNKNOWN_ERR)

    # Deal with the -run-tellurium option which doesn't call run_jneuroml
    if args.run_tellurium is not None:
        try:
            from pyneuroml.tellurium import run_from_sedml_file
        except Exception:
            logger.critical("Unable to import pyneuroml.tellurium")
            sys.exit(UNKNOWN_ERR)

        if len(args.run_tellurium) < 1 and len(args.input_files) < 1:
            logger.critical("No input files specified")
            sys.exit(ARGUMENT_ERR)

        try:
            if len(args.input_files) == 1:
                sedml_file = [args.input_files[0]]
                other_args = args.run_tellurium
            else:
                sedml_file = [args.run_tellurium[0]]
                other_args = args.run_tellurium[1:]

            run_from_sedml_file(sedml_file, other_args)
        except Exception as e:
            logger.critical(f"run_from_sedml_file failed with: {str(e)}")
            logger.critical(f"Args supplied: {str(args)}")
            sys.exit(UNKNOWN_ERR)

        sys.exit(0)

    # These do not use the shared option where files are supplied
    # They require the file name to be specified after
    # TODO: handle these better
    if args.sbml_import or args.sbml_import_units or args.vhdl:
        if args.sbml_import:
            pre_args = "-sbml-import"
            f = args.sbml_import[0]
            post_args = " ".join(args.sbml_import[1:])
        elif args.sbml_import_units:
            pre_args = "-smbl-import-units"
            f = args.sbml_import_units[0]
            post_args = " ".join(args.sbml_import_units[1:])
        elif args.vhdl:
            f = args.vhdl[1]
            confirm_lems_file(f)
            post_args = "-vhdl %s" % args.vhdl[0]

        run_jneuroml(
            pre_args,
            f,
            post_args,
            max_memory=args.java_max_memory,
            exit_on_fail=exit_on_fail,
        )
        # No need to go any further
        return True

    # Process bits that process the file list provided as the shared option
    if len(args.input_files) == 0:
        logger.critical("Please specify NeuroML/LEMS files to process")
        return

    run_multi = False

    for f in args.input_files:
        if args.nogui:
            post_args = "-nogui"

        if args.sedml:
            confirm_lems_file(f)
            post_args = "-sedml"
        elif args.neuron is not None:
            # Note: either a lems file or nml2 file is allowed here...
            confirm_file_exists(f)

            num_neuron_args = len(args.neuron)
            if num_neuron_args < 0 or num_neuron_args > 4:
                logger.error(
                    "The '-neuron' option was given an invalid "
                    "number of arguments: %d given, 0-4 required" % num_neuron_args
                )
                sys.exit(ARGUMENT_ERR)

            other_args = [(a if a != "-neuron" else "") for a in args.neuron]
            post_args = "-neuron %s" % " ".join(other_args)

        elif args.netpyne is not None:
            # Note: either a lems file or nml2 file is allowed here...
            confirm_file_exists(f)

            num_netpyne_args = len(args.netpyne)

            if num_netpyne_args < 0 or num_netpyne_args > 4:
                logger.error(
                    "The '-netpyne' option was given an invalid "
                    "number of arguments: %d given, 0-4 required" % num_netpyne_args
                )
                sys.exit(ARGUMENT_ERR)

            other_args = [(a if a != "-netpyne" else "") for a in args.netpyne]
            post_args = "-netpyne %s" % " ".join(other_args)

        elif args.eden is not None:
            confirm_lems_file(f)

            num_eden_args = len(args.eden)

            if num_eden_args < 0 or num_eden_args > 2:
                logger.error(
                    "The '-eden' option was given an invalid "
                    "number of arguments: %d given, 0-4 required" % num_eden_args
                )
                sys.exit(ARGUMENT_ERR)

            other_args = [(a if a != "-eden" else "") for a in args.eden]
            post_args = "-eden %s" % " ".join(other_args)

        elif args.svg:
            confirm_neuroml_file(f)
            post_args = "-svg"
        elif args.png:
            confirm_neuroml_file(f)
            post_args = "-png"
        elif args.dlems:
            confirm_lems_file(f)
            post_args = "-dlems"
        elif args.vertex:
            confirm_lems_file(f)
            post_args = "-vertex"
        elif args.xpp:
            confirm_lems_file(f)
            post_args = "-xpp"
        elif args.dnsim:
            confirm_lems_file(f)
            post_args = "-dnsim"
        elif args.brian:
            confirm_lems_file(f)
            post_args = "-brian"
        elif args.brian2:
            confirm_lems_file(f)
            post_args = "-brian2"
        elif args.moose:
            confirm_lems_file(f)
            post_args = "-moose"
        elif args.sbml:
            confirm_lems_file(f)
            post_args = "-sbml"
        elif args.sbml_sedml:
            confirm_lems_file(f)
            post_args = "-sbml-sedml"
        elif args.matlab:
            confirm_lems_file(f)
            post_args = "-matlab"
        elif args.cvode:
            confirm_lems_file(f)
            post_args = "-cvode"
        elif args.nineml:
            confirm_lems_file(f)
            post_args = "-nineml"
        elif args.spineml:
            confirm_lems_file(f)
            post_args = "-spineml"
        elif args.graph:
            confirm_neuroml_file(f)
            from neuromllite.GraphVizHandler import engines

            engine = "dot"

            # They can use min1 to mean -1
            level = args.graph[0].replace("min", "-")

            # If they only provide a level
            try:
                level = int(level)
                print("Level selected: {}".format(level))
            # If they provide level and engine specs: 1d, 2c
            # Or some wrong value
            except ValueError:
                try:
                    engine = engines[level[-1:]]
                    logger.info("Engine selected: {}".format(engine))
                except KeyError as e:
                    logger.info(
                        "Unknown value for engine: {}. Please use one of {}".format(
                            e, engines
                        )
                    )
                    sys.exit(ARGUMENT_ERR)

                # if a valid engine was provided, we try the level again
                try:
                    level = int(level[:-1])
                    logger.info("Level selected: {}".format(level))
                except ValueError:
                    logger.info("Incorrect value for level: {}.".format(level[:-1]))
                    sys.exit(ARGUMENT_ERR)

            generate_nmlgraph(f, level, engine)
            sys.exit(0)
        elif args.lems_graph:
            confirm_lems_file(f)
            pre_args = ""
            post_args = "-lems-graph"
            exit_on_fail = True
        elif args.matrix:
            confirm_neuroml_file(f)
            from neuromllite.MatrixHandler import MatrixHandler

            level = int(args.matrix[0])

            logger.info("Converting %s to matrix form, level %i" % (f, level))

            from neuroml.hdf5.NeuroMLXMLParser import NeuroMLXMLParser

            handler = MatrixHandler(level=level, nl_network=None)

            currParser = NeuroMLXMLParser(handler)

            currParser.parse(f)

            handler.finalise_document()

            logger.info("Done with MatrixHandler...")

            exit(0)
        elif args.validate:
            confirm_neuroml_file(f)
            pre_args = "-validate"
            exit_on_fail = True
            run_multi = True

        elif args.validatev1:
            confirm_neuroml_file(f)
            pre_args = "-validatev1"
            exit_on_fail = True
            run_multi = True

        elif args.swc:
            convert_count = 0
            for f in args.input_files:
                confirm_neuroml_file(f)
                logger.info(f"Trying to convert {f} to swc format...")
                convert_count += 1 if convert_to_swc(f) else 0
            logger.info(f"Converted {convert_count} file(s) to swc format")
            sys.exit(0)

        if run_multi is False:
            run_jneuroml(
                pre_args,
                f,
                post_args,
                max_memory=args.java_max_memory,
                exit_on_fail=exit_on_fail,
            )
    if run_multi:
        run_jneuroml(
            pre_args,
            " ".join(args.input_files),
            post_args,
            max_memory=args.java_max_memory,
            exit_on_fail=exit_on_fail,
        )


"""
    As usually saved by jLEMS, etc. First column is time (in seconds), multiple other columns
"""


def reload_standard_dat_file(file_name: str) -> typing.Tuple[dict, list]:
    """Reload a datafile as usually saved by jLEMS, etc.
    First column is time (in seconds), multiple other columns.

    :param file_name: name of data file to load
    :type file_name: str
    :returns: tuple of (data, column names)
    """
    with open(file_name) as dat_file:
        data = {}  # type: dict
        indices = []  # type: list
        for line in dat_file:
            words = line.split()

            if "t" not in data.keys():
                data["t"] = []
                for i in range(len(words) - 1):
                    data[i] = []
                    indices.append(i)
            data["t"].append(float(words[0]))
            for i in range(len(words) - 1):
                data[i].append(float(words[i + 1]))

        logger.info("Loaded data from %s; columns: %s" % (file_name, indices))
    return data, indices


def evaluate_component(comp_type, req_variables={}, parameter_values={}):
    """
    Work in progress: expand a (simple) ComponentType  and evaluate an instance of it by
    giving parameters & required variables
    Used in MOOSE NeuroML reader...
    """
    logger.debug(
        "Evaluating %s with req:%s; params:%s"
        % (comp_type.name, req_variables, parameter_values)
    )
    exec_str = ""
    return_vals = {}
    for p in parameter_values:
        exec_str += "%s = %s\n" % (p, get_value_in_si(parameter_values[p]))
    for r in req_variables:
        exec_str += "%s = %s\n" % (r, get_value_in_si(req_variables[r]))
    for c in comp_type.Constant:
        exec_str += "%s = %s\n" % (c.name, get_value_in_si(c.value))
    for d in comp_type.Dynamics:
        for dv in d.DerivedVariable:
            exec_str += "%s = %s\n" % (dv.name, dv.value)
            exec_str += 'return_vals["%s"] = %s\n' % (dv.name, dv.name)
        for cdv in d.ConditionalDerivedVariable:
            for case in cdv.Case:
                if case.condition:
                    cond = (
                        case.condition.replace(".neq.", "!=")
                        .replace(".eq.", "==")
                        .replace(".gt.", "<")
                        .replace(".lt.", "<")
                    )
                    exec_str += "if ( %s ): %s = %s \n" % (cond, cdv.name, case.value)
                else:
                    exec_str += "else: %s = %s \n" % (cdv.name, case.value)

            exec_str += "\n"

            exec_str += 'return_vals["%s"] = %s\n' % (cdv.name, cdv.name)
    exec_str = "from math import exp  # only one required for nml2?\n" + exec_str
    # logger.info('Exec %s'%exec_str)
    exec(exec_str)

    return return_vals


def main(args=None):
    """Main"""

    if args is None:
        args = _parse_arguments()

    _evaluate_arguments(args)


if __name__ == "__main__":
    main()
