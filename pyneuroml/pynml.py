#!/usr/bin/env python
"""

Python wrapper around jnml command.

Thanks to Werner van Geit for an initial version of a python wrapper for jnml.

"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
import sys
import logging

from pyneuroml import __version__
from pyneuroml import JNEUROML_VERSION
from pyneuroml.swc.ExportSWC import convert_to_swc
from pyneuroml.utils import *

import neuroml


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

version_string = "pyNeuroML v{} (libNeuroML v{}, jNeuroML v{})".format(
    __version__, neuroml.__version__, JNEUROML_VERSION
)


def parse_arguments():
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
        metavar="<LEMS/NeuroML 2 file(s)>",
        help="LEMS/NeuroML 2 file(s) to process",
    )

    mut_exc_opts_grp = parser.add_argument_group(
        title="Mutually-exclusive options",
        description="Only one of these options can be selected",
    )
    mut_exc_opts = mut_exc_opts_grp.add_mutually_exclusive_group(
        required=False
    )  # noqa: E501

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
            "        do not generate gtaphical elements in NEURON,\n"
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
            "    <LEMS file>\n"
            "        the LEMS file to use"
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
        "-swc",
        action="store_true",
        help=("Export all Cells from a NeuroML file to SWC format"),
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
            "toLEMS format using values for duration & dt\n"
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

    return parser.parse_args()


def evaluate_arguments(args):
    logger.debug("    ====  Args: %s" % args)
    global DEFAULTS

    if args.version:
        print(version_string)
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
                sys.exit(-1)

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
                sys.exit(-1)

            other_args = [(a if a != "-netpyne" else "") for a in args.netpyne]
            post_args = "-netpyne %s" % " ".join(other_args)

        elif args.svg:
            confirm_neuroml_file(f)
            post_args = "-svg"
        elif args.png:
            confirm_neuroml_file(f)
            post_args = "-png"
        elif args.swc:
            confirm_neuroml_file(f)
            convert_to_swc(f)
            exit()
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
                    print("Engine selected: {}".format(engine))
                except KeyError as e:
                    print(
                        "Unknown value for engine: {}. Please use one of {}".format(
                            e, engines
                        )
                    )
                    sys.exit(-1)

                # if a valid engine was provided, we try the level again
                try:
                    level = int(level[:-1])
                    print("Level selected: {}".format(level))
                except ValueError:
                    print("Incorrect value for level: {}.".format(level[:-1]))
                    sys.exit(-1)

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

            exit()
        elif args.validate:
            confirm_neuroml_file(f)
            pre_args = "-validate"
            exit_on_fail = True
        elif args.validatev1:
            confirm_neuroml_file(f)
            pre_args = "-validatev1"
            exit_on_fail = True

        run_jneuroml(
            pre_args,
            f,
            post_args,
            max_memory=args.java_max_memory,
            exit_on_fail=exit_on_fail,
        )


def main(args=None):
    """Main"""

    if args is None:
        args = parse_arguments()

    evaluate_arguments(args)


if __name__ == "__main__":
    main()
