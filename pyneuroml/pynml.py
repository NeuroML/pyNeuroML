#!/usr/bin/env python
"""

Python wrapper around jnml command.
Also a number of helper functions for
handling/generating/running LEMS/NeuroML2 files

Thanks to Werner van Geit for an initial version of a python wrapper for jnml.

"""

from __future__ import absolute_import
from __future__ import unicode_literals

# py3.7, 3.8 require this to use standard collections as generics
from __future__ import annotations
import warnings
import os
import shutil
import sys
import subprocess
import math
from datetime import datetime
import textwrap
import random
import inspect
import zipfile
import shlex
from lxml import etree
import pprint
import logging
import tempfile
import typing
import traceback

import lems.model.model as lems_model
import lems
from lems.parser.LEMS import LEMSFileParser

from pyneuroml import __version__
from pyneuroml import JNEUROML_VERSION

import neuroml
from neuroml import NeuroMLDocument, Cell
import neuroml.loaders as loaders
import neuroml.writers as writers

# to maintain API compatibility:
# so that existing scripts that use: from pynml import generate_plot
# continue to work
from pyneuroml.plot import generate_plot, generate_interactive_plot  # noqa

DEFAULTS = {
    "v": False,
    "default_java_max_memory": "400M",
    "nogui": False,
}  # type: dict[str, typing.Any]

lems_model_with_units = None

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

version_string = "pyNeuroML v{} (libNeuroML v{}, jNeuroML v{})".format(
    __version__, neuroml.__version__, JNEUROML_VERSION
)

FILE_NOT_FOUND_ERR = 13
ARGUMENT_ERR = 14
UNKNOWN_ERR = 15


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


def get_lems_model_with_units() -> lems_model.Model:
    """
    Get a LEMS model with NeuroML core dimensions and units.

    :returns: a `lems.model.model.Model` that includes NeuroML dimensions and units.
    """
    global lems_model_with_units

    if lems_model_with_units is None:
        jar_path = get_path_to_jnml_jar()
        logger.debug(
            "Loading standard NeuroML2 dimension/unit definitions from %s" % jar_path
        )
        jar = zipfile.ZipFile(jar_path, "r")
        dims_units = jar.read("NeuroML2CoreTypes/NeuroMLCoreDimensions.xml")
        lems_model_with_units = lems_model.Model(include_includes=False)
        parser = LEMSFileParser(lems_model_with_units)
        parser.parse(dims_units)

    return lems_model_with_units


def extract_lems_definition_files(
    path: typing.Union[str, None, tempfile.TemporaryDirectory] = None
) -> str:
    """Extract the NeuroML2 LEMS definition files to a directory and return its path.

    This function can be used by other LEMS related functions that need to
    include the NeuroML2 LEMS definitions.

    If a path is provided, the folder is created relative to the current
    working directory.

    If no path is provided, for repeated usage for example, the files are
    extracted to a temporary directory using Python's
    `tempfile.mkdtemp
    <https://docs.python.org/3/library/tempfile.html>`__ function.

    Note: in both cases, it is the user's responsibility to remove the created
    directory when it is no longer required, for example using.  the
    `shutil.rmtree()` Python function.

    :param path: path of directory relative to current working directory to extract to, or None
    :type path: str or None
    :returns: directory path
    """
    jar_path = get_path_to_jnml_jar()
    logger.debug(
        "Loading standard NeuroML2 dimension/unit definitions from %s" % jar_path
    )
    jar = zipfile.ZipFile(jar_path, "r")
    namelist = [x for x in jar.namelist() if ".xml" in x and "NeuroML2CoreTypes" in x]
    logger.debug("NeuroML LEMS definition files in jar are: {}".format(namelist))

    # If a string is provided, ensure that it is relative to cwd
    if path and isinstance(path, str) and len(path) > 0:
        path = "./" + path
        try:
            os.makedirs(path)
        except FileExistsError:
            logger.warning(
                "{} already exists. Any NeuroML LEMS files in it will be overwritten".format(
                    path
                )
            )
        except OSError as err:
            logger.critical(err)
            sys.exit(UNKNOWN_ERR)
    else:
        path = tempfile.mkdtemp()

    logger.debug("Created directory: " + path)
    jar.extractall(path, namelist)
    path = path + "/NeuroML2CoreTypes/"
    logger.info("NeuroML LEMS definition files extracted to: {}".format(path))
    return path


def list_exposures(
    nml_doc_fn: str, substring: str = ""
) -> typing.Union[
    dict[lems.model.component.Component, list[lems.model.component.Exposure]],
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
) -> list[str]:
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


def split_nml2_quantity(nml2_quantity: str) -> tuple[float, str]:
    """Split a NeuroML 2 quantity into its magnitude and units

    :param nml2_quantity: NeuroML2 quantity to split
    :type nml2_quantity:
    :returns: a tuple (magnitude, unit)
    """
    magnitude = None
    i = len(nml2_quantity)
    while magnitude is None:
        try:
            part = nml2_quantity[0:i]
            nn = float(part)
            magnitude = nn
            unit = nml2_quantity[i:]
        except ValueError:
            i = i - 1

    return magnitude, unit


def get_value_in_si(nml2_quantity: str) -> typing.Union[float, None]:
    """Get value of a NeuroML2 quantity in SI units

    :param nml2_quantity: NeuroML2 quantity to convert
    :type nml2_quantity: str
    :returns: value in SI units (float)
    """
    try:
        return float(nml2_quantity)
    except ValueError:
        model = get_lems_model_with_units()
        m, u = split_nml2_quantity(nml2_quantity)
        si_value = None
        for un in model.units:
            if un.symbol == u:
                si_value = (m + un.offset) * un.scale * pow(10, un.power)
        return si_value


def convert_to_units(nml2_quantity: str, unit: str) -> float:
    """Convert a NeuroML2 quantity to provided unit.

    :param nml2_quantity: NeuroML2 quantity to convert
    :type nml2_quantity: str
    :param unit: unit to convert to
    :type unit: str
    :returns: converted value (float)
    """
    model = get_lems_model_with_units()
    m, u = split_nml2_quantity(nml2_quantity)
    si_value = None
    dim = None
    for un in model.units:
        if un.symbol == u:
            si_value = (m + un.offset) * un.scale * pow(10, un.power)
            dim = un.dimension

    for un in model.units:
        if un.symbol == unit:
            new_value = si_value / (un.scale * pow(10, un.power)) - un.offset
            if not un.dimension == dim:
                raise Exception(
                    "Cannot convert {} to {}. Dimensions of units ({}/{}) do not match!".format(
                        nml2_quantity, unit, dim, un.dimension
                    )
                )

    logger.debug(
        "Converting {} {} to {}: {} ({} in SI units)".format(
            m, u, unit, new_value, si_value
        )
    )

    return new_value


def generate_nmlgraph(nml2_file_name: str, level: int = 1, engine: str = "dot") -> None:
    """Generate NeuroML graph.

    :nml2_file_name (string): NML file to parse
    :level (string): level of graph to generate (default: '1')
    :engine (string): graph engine to use (default: 'dot')

    """
    from neuromllite.GraphVizHandler import GraphVizHandler
    from neuroml.hdf5.NeuroMLXMLParser import NeuroMLXMLParser

    logger.info(
        "Converting %s to graphical form, level %i, engine %s"
        % (nml2_file_name, level, engine)
    )

    handler = GraphVizHandler(level=level, engine=engine, nl_network=None)
    currParser = NeuroMLXMLParser(handler)
    currParser.parse(nml2_file_name)
    handler.finalise_document()

    logger.info("Done with GraphViz...")


def generate_lemsgraph(lems_file_name: str, verbose_generate: bool = True) -> bool:
    """Generate LEMS graph using jNeuroML

    :param lems_file_name: LEMS file to parse
    :type lems_file_name: str
    :param verbose_generate: whether or not jnml should be run with verbosity output
    :type verbose_generate: bool
    :returns bool: True of jnml ran without errors, exits without a return if jnml fails
    """
    pre_args = ""
    post_args = "-lems-graph"

    return run_jneuroml(
        pre_args,
        lems_file_name,
        post_args,
        verbose=verbose_generate,
        report_jnml_output=verbose_generate,
        exit_on_fail=True,
        return_string=False,
    )


def validate_neuroml1(
    nml1_file_name: str, verbose_validate: bool = True, return_string: bool = False
) -> typing.Union[bool, tuple[bool, str]]:
    """Validate a NeuroML v1 file.

    NOTE: NeuroML v1 is deprecated. Please use NeuroML v2.
    This functionality will be dropped in the future.

    :param nml1_file_name: name of NeuroMLv1 file to validate
    :type nml1_file_name: str
    :param verbose_validate: whether jnml should print verbose information while validating
    :type verbose_validate: bool (default: True)
    :param return_string: toggle to enable or disable returning the output of the jnml validation
    :type return_string: bool
    :returns: Either a bool, or a tuple (bool, str): True if jnml ran without errors, false if jnml fails; along with the message returned by jnml
    """
    logger.info("NOTE: NeuroMLv1 is deprecated. Please use NeuroMLv2.")
    pre_args = "-validatev1"
    post_args = ""

    warnings.warn(
        "Please note that NeuroMLv1 is deprecated. Functions supporting NeuroMLv1 will be removed in the future.  Please use NeuroMLv2.",
        FutureWarning,
        stacklevel=2,
    )

    return run_jneuroml(
        pre_args,
        nml1_file_name,
        post_args,
        verbose=verbose_validate,
        report_jnml_output=verbose_validate,
        exit_on_fail=False,
        return_string=return_string,
    )


def validate_neuroml2(
    nml2_file_name: str,
    verbose_validate: bool = True,
    max_memory: typing.Optional[str] = None,
    return_string: bool = False,
) -> typing.Union[bool, tuple[bool, str]]:
    """Validate a NeuroML2 file using jnml.

    :params nml2_file_name: name of NeuroML 2 file to validate
    :type nml2_file_name: str
    :param verbose_validate: whether jnml should print verbose information while validating
    :type verbose_validate: bool (default: True)
    :param max_memory: maximum memory the JVM should use while running jnml
    :type max_memory: str
    :param return_string: toggle to enable or disable returning the output of the jnml validation
    :type return_string: bool
    :returns: Either a bool, or a tuple (bool, str): True if jnml ran without errors, false if jnml fails; along with the message returned by jnml
    """
    pre_args = "-validate"
    post_args = ""

    if max_memory is not None:
        return run_jneuroml(
            pre_args,
            nml2_file_name,
            post_args,
            max_memory=max_memory,
            verbose=verbose_validate,
            report_jnml_output=verbose_validate,
            exit_on_fail=False,
            return_string=return_string,
        )
    else:
        return run_jneuroml(
            pre_args,
            nml2_file_name,
            post_args,
            verbose=verbose_validate,
            report_jnml_output=verbose_validate,
            exit_on_fail=False,
            return_string=return_string,
        )


def validate_neuroml2_lems_file(
    nml2_lems_file_name: str, max_memory: str = DEFAULTS["default_java_max_memory"]
) -> bool:
    """Validate a NeuroML 2 LEMS file using jNeuroML.

    Note that this uses jNeuroML and so is aware of the standard NeuroML LEMS
    definitions.

    TODO: allow inclusion of other paths for user-defined LEMS definitions
    (does the -norun option allow the use of -I?)

    :param nml2_lems_file_name: name of file to validate
    :type nml2_lems_file_name: str
    :param max_memory: memory to use for the Java virtual machine
    :type max_memory: str
    :returns: True if valid, False if invalid

    """
    post_args = ""
    post_args += "-norun"

    return run_jneuroml(
        "",
        nml2_lems_file_name,
        post_args,
        max_memory=max_memory,
        verbose=False,
        report_jnml_output=True,
        exit_on_fail=True,
    )


def read_neuroml2_file(
    nml2_file_name: str,
    include_includes: bool = False,
    verbose: bool = False,
    already_included: list = None,
    optimized: bool = False,
    check_validity_pre_include: bool = False,
) -> NeuroMLDocument:
    """Read a NeuroML2 file into a `nml.NeuroMLDocument`

    :param nml2_file_name: file of NeuroML 2 file to read
    :type nml2_file_name: str
    :param include_includes: toggle whether files included in NML file should also be included/read
    :type include_includes: bool
    :param verbose: toggle verbosity
    :type verbose: bool
    :param already_included: list of files already included
    :type already_included: list
    :param optimized: toggle whether the HDF5 loader should optimise the document
    :type optimized: bool
    :param check_validity_pre_include: check each file for validity before including
    :type check_validity_pre_include: bool
    :returns: nml.NeuroMLDocument object containing the read NeuroML file(s)
    """
    if already_included is None:
        already_included = []

    logger.info("Loading NeuroML2 file: %s" % nml2_file_name)

    if not os.path.isfile(nml2_file_name):
        logger.critical("Unable to find file: %s!" % nml2_file_name)
        sys.exit(FILE_NOT_FOUND_ERR)

    if nml2_file_name.endswith(".h5") or nml2_file_name.endswith(".hdf5"):
        nml2_doc = loaders.NeuroMLHdf5Loader.load(nml2_file_name, optimized=optimized)
    else:
        nml2_doc = loaders.NeuroMLLoader.load(nml2_file_name)

    base_path = os.path.dirname(os.path.realpath(nml2_file_name))

    if include_includes:
        if verbose:
            logger.info(
                "Including included files (included already: {})".format(
                    already_included
                )
            )

        incl_to_remove = []
        for include in nml2_doc.includes:
            incl_loc = os.path.abspath(os.path.join(base_path, include.href))
            if incl_loc not in already_included:
                inc = True  # type: typing.Union[bool, tuple[bool, str]]
                if check_validity_pre_include:
                    inc = validate_neuroml2(incl_loc, verbose_validate=False)

                if inc:
                    logger.debug(
                        "Loading included NeuroML2 file: {} (base: {}, resolved: {}, checking {})".format(
                            include.href,
                            base_path,
                            incl_loc,
                            check_validity_pre_include,
                        )
                    )
                    nml2_sub_doc = read_neuroml2_file(
                        incl_loc,
                        True,
                        verbose=verbose,
                        already_included=already_included,
                        check_validity_pre_include=check_validity_pre_include,
                    )
                    if incl_loc not in already_included:
                        already_included.append(incl_loc)

                    membs = inspect.getmembers(nml2_sub_doc)

                    for memb in membs:
                        if (
                            isinstance(memb[1], list)
                            and len(memb[1]) > 0
                            and not memb[0].endswith("_")
                        ):
                            for entry in memb[1]:
                                if memb[0] != "includes":
                                    logger.debug(
                                        "  Adding {!s} from: {!s} to list: {}".format(
                                            entry, incl_loc, memb[0]
                                        )
                                    )
                                    getattr(nml2_doc, memb[0]).append(entry)
                    incl_to_remove.append(include)
                else:
                    logger.warning("Not including file as it's not valid...")

        for include in incl_to_remove:
            nml2_doc.includes.remove(include)

    return nml2_doc


def quick_summary(nml2_doc: NeuroMLDocument) -> str:
    """Get a quick summary of the NeuroML2 document

    NOTE: You should prefer nml2_doc.summary(show_includes=False)

    :param nml2_doc: NeuroMLDocument to fetch summary for
    :type nml2_doc: NeuroMLDocument
    :returns: summary string
    """
    info = "Contents of NeuroML 2 document: {}\n".format(nml2_doc.id)
    membs = inspect.getmembers(nml2_doc)

    for memb in membs:
        if isinstance(memb[1], list) and len(memb[1]) > 0 and not memb[0].endswith("_"):
            info += "  {}:\n    [".format(memb[0])
            for entry in memb[1]:
                extra = "???"
                extra = entry.name if hasattr(entry, "name") else extra
                extra = entry.href if hasattr(entry, "href") else extra
                extra = entry.id if hasattr(entry, "id") else extra

                info += " {} ({}),".format(entry, extra)

            info += "]\n"
    return info


def summary(
    nml2_doc: typing.Optional[NeuroMLDocument] = None, verbose: bool = False
) -> None:
    """Wrapper around nml_doc.summary() to generate the pynml-summary command
    line tool.

    :param nml2_doc: NeuroMLDocument object or name of NeuroML v2 file to get summary for.
    :type nml2_doc: NeuroMLDocument
    :param verbose: toggle verbosity
    :type verbose: bool
    """

    usage = textwrap.dedent(
        """
        Usage:

        pynml-summary <NeuroML file> [-vh]

        Required arguments:
            NeuroML file: name of file to summarise

        Optional arguments:

            -v/--verbose:  enable verbose mode
            -h/--help:  print this help text and exit
        """
    )

    if len(sys.argv) < 2:
        print("Argument required.")
        print(usage)
        return

    if "-h" in sys.argv or "--help" in sys.argv:
        print(usage)
        return

    if "-v" in sys.argv or "--verbose" in sys.argv:
        verbose = True
        sys.argv.remove("-v")

    if nml2_doc is None:
        nml2_file_name = sys.argv[1]
        nml2_doc = read_neuroml2_file(nml2_file_name, include_includes=verbose)

    info = nml2_doc.summary(show_includes=False)

    if verbose:
        cell_info_str = ""
        for cell in nml2_doc.cells:
            cell_info_str += cell_info(cell) + "*\n"
        lines = info.split("\n")
        info = ""
        still_to_add = False
        for line in lines:
            if "Cell: " in line:
                still_to_add = True
                pass
            elif "Network: " in line:
                still_to_add = False
                if len(cell_info_str) > 0:
                    info += "%s" % cell_info_str
                info += "%s\n" % line
            else:
                if still_to_add and "******" in line:
                    if len(cell_info_str) > 0:
                        info += "%s" % cell_info_str
                info += "%s\n" % line
    print(info)


def cells_info(nml_file_name: str) -> str:
    """Provide information about the cells in a NeuroML file.

    :param nml_file_name: name of NeuroML v2 file
    :type nml_file_name: str
    :returns: information on cells (str)
    """
    from neuroml.loaders import read_neuroml2_file

    nml_doc = read_neuroml2_file(
        nml_file_name, include_includes=True, verbose=False, optimized=True
    )

    info = ""
    info += "Extracting information on %i cells in %s" % (
        len(nml_doc.cells),
        nml_file_name,
    )

    for cell in nml_doc.cells:
        info += cell_info(cell)
    return info


def cell_info(cell: Cell) -> str:
    """Provide information on a NeuroML Cell instance:

    - morphological information:

      - Segment information:

        - parent segments
        - segment location, extents, diameter
        - segment length
        - segment surface area
        - segment volume

      - Segment group information:

        - included segments

    - biophysical properties:

      - channel densities
      - specific capacitances

    :param cell: cell object to investigate
    :type cell: Cell
    :returns: string of cell information
    """
    info = ""
    prefix = "*  "
    info += prefix + "Cell: %s\n" % cell.id
    tot_length = 0
    tot_area = 0
    for seg in cell.morphology.segments:
        info += prefix + "  %s\n" % seg
        dist = seg.distal
        prox = seg.proximal
        parent_id = seg.parent.segments if seg.parent else "None (root segment)"
        length = cell.get_segment_length(seg.id)
        info += prefix + "    Parent segment: %s\n" % (parent_id)
        info += prefix + "    %s -> %s; seg length: %s um\n" % (prox, dist, length)

        tot_length += length
        area = cell.get_segment_surface_area(seg.id)
        volume = cell.get_segment_volume(seg.id)
        tot_area += area
        info += prefix + "    Surface area: %s um2, volume: %s um3\n" % (area, volume)
    numseg = len(cell.morphology.segments)
    info += prefix + "  Total length of %i segment%s: %s um; total area: %s um2\n" % (
        numseg,
        "s" if numseg > 1 else "",
        tot_length,
        tot_area,
    )

    info += prefix + "\n"

    for sg in cell.morphology.segment_groups:
        segs = cell.get_all_segments_in_group(sg.id)
        info += prefix + "  %s;\tcontains %i segment%s\n" % (
            str(sg).replace(", ", ",\t"),
            len(segs),
            ", id: %s" % segs[0] if len(segs) == 1 else "s in total",
        )

    if len(cell.morphology.segment_groups) > 0:
        info += prefix + "\n"

    seg_info = cell.get_segment_ids_vs_segments()
    if cell.biophysical_properties:
        for cd in cell.biophysical_properties.membrane_properties.channel_densities:
            # print dir(cd)
            group = cd.segment_groups if cd.segment_groups else "all"
            info += (
                prefix
                + "  Channel density: %s on %s;\tconductance of %s through ion chan %s with ion %s, erev: %s\n"
                % (cd.id, group, cd.cond_density, cd.ion_channel, cd.ion, cd.erev)
            )
            segs = cell.get_all_segments_in_group(group)
            for seg_id in segs:
                seg = seg_info[seg_id]

                cond_dens_si = get_value_in_si(cd.cond_density)
                surface_area_si = get_value_in_si(
                    "%s um2" % cell.get_segment_surface_area(seg_id)
                )
                cond_si = cond_dens_si * surface_area_si
                cond_pS = convert_to_units("%sS" % cond_si, "pS")
                info += (
                    prefix
                    + "    Channel is on %s,\ttotal conductance: %s S_per_m2 x %s m2 = %s S (%s pS)\n"
                    % (seg, cond_dens_si, surface_area_si, cond_si, cond_pS)
                )

        if len(cell.biophysical_properties.membrane_properties.channel_densities) > 0:
            info += prefix + "\n"

        for sc in cell.biophysical_properties.membrane_properties.specific_capacitances:
            group = sc.segment_groups if sc.segment_groups else "all"
            info += prefix + "  Specific capacitance on %s: %s\n" % (group, sc.value)
            segs = cell.get_all_segments_in_group(group)
            for seg_id in segs:
                seg = seg_info[seg_id]
                spec_cap_si = get_value_in_si(sc.value)
                surface_area_si = get_value_in_si(
                    "%s um2" % cell.get_segment_surface_area(seg_id)
                )
                cap_si = spec_cap_si * surface_area_si
                cap_pF = convert_to_units("%sF" % cap_si, "pF")
                info += (
                    prefix
                    + "    Capacitance of %s,\ttotal capacitance: %s F_per_m2 x %s m2 = %s F (%s pF)\n"
                    % (seg, spec_cap_si, surface_area_si, cap_si, cap_pF)
                )

    return info


def write_neuroml2_file(
    nml2_doc: NeuroMLDocument,
    nml2_file_name: str,
    validate: bool = True,
    verbose_validate: bool = False,
    hdf5: bool = False,
) -> None:
    """Write a NeuroMLDocument object to a file using libNeuroML.

    :param nml2_doc: NeuroMLDocument object to write to file
    :type nml2_doc: NeuroMLDocument
    :param nml2_file_name: name of file to write to
    :type nml2_file_name: str
    :param validate: toggle whether the written file should be validated
    :type validate: bool
    :param verbose_validate: toggle whether the validation should be verbose
    :type verbose_validate: bool
    :param hdf5: write to HDF5 file
    :type hdf5: bool
    """
    if hdf5 is True:
        writers.NeuroMLHdf5Writer.write(nml2_doc, nml2_file_name)
    else:
        writers.NeuroMLWriter.write(nml2_doc, nml2_file_name)

    if validate:
        return validate_neuroml2(nml2_file_name, verbose_validate)


def read_lems_file(
    lems_file_name: str,
    include_includes: bool = False,
    fail_on_missing_includes: bool = False,
    debug: bool = False,
) -> lems_model.Model:
    """Read LEMS file using PyLEMS. See WARNING below.

    WARNING: this is a general function that uses PyLEMS to read any files that
    are valid LEMS *even if they are not valid NeuroML*. Therefore, this
    function is not aware of the standard NeuroML LEMS definitions.

    To validate NeuroML LEMS files which need to be aware of the NeuroML
    standard LEMS definitions, please use the `validate_neuroml2_lems_file`
    function instead.
    """
    if not os.path.isfile(lems_file_name):
        logger.critical("Unable to find file: %s!" % lems_file_name)
        sys.exit(FILE_NOT_FOUND_ERR)

    model = lems_model.Model(
        include_includes=include_includes,
        fail_on_missing_includes=fail_on_missing_includes,
    )
    model.debug = debug

    model.import_from_file(lems_file_name)

    return model


def write_lems_file(
    lems_model: lems_model.Model, lems_file_name: str, validate: bool = False
) -> None:
    """Write a lems_model.Model to file using pyLEMS.

    :param lems_model: LEMS model to write to file
    :type lems_model: lems_model.Model
    :param lems_file_name: name of file to write to
    :type lems_file_name: str
    :param validate: toggle whether written file should be validated
    :type validate: bool
    """
    lems_model.export_to_file(lems_file_name)

    if validate:
        from lems.base.util import validate_lems

        validate_lems(lems_file_name)


def run_lems_with_jneuroml(
    lems_file_name: str,
    paths_to_include: list = [],
    max_memory: str = DEFAULTS["default_java_max_memory"],
    skip_run: bool = False,
    nogui: bool = False,
    load_saved_data: bool = False,
    reload_events: bool = False,
    plot: bool = False,
    show_plot_already: bool = True,
    exec_in_dir: str = ".",
    verbose: bool = DEFAULTS["v"],
    exit_on_fail: bool = True,
    cleanup: bool = False,
) -> typing.Union[bool, typing.Union[dict, tuple[dict, dict]]]:
    """Parse/Run a LEMS file with jnml.

    Tip: set `skip_run=True` to only parse the LEMS file but not run the simulation.

    :param lems_file_name: name of LEMS file to run
    :type lems_file_name: str
    :param paths_to_include: additional directory paths to include (for other NML/LEMS files, for example)
    :type paths_to_include: list(str)
    :param max_memory: maximum memory allowed for use by the JVM
    :type max_memory: bool
    :param skip_run: toggle whether run should be skipped, if skipped, file will only be parsed
    :type skip_run: bool
    :param nogui: toggle whether jnml GUI should be shown
    :type nogui: bool
    :param load_saved_data: toggle whether any saved data should be loaded
    :type load_saved_data: bool
    :param reload_events: toggle whether events should be reloaded
    :type reload_events: bool
    :param plot: toggle whether specified plots should be plotted
    :type plot: bool
    :param show_plot_already: toggle whether prepared plots should be shown
    :type show_plot_already: bool
    :param exec_in_dir: working directory to execute LEMS simulation in
    :type exec_in_dir: str
    :param verbose: toggle whether jnml should print verbose information
    :type verbose: bool
    :param exit_on_fail: toggle whether command should exit if jnml fails
    :type exit_on_fail: bool
    :param cleanup: toggle whether the directory should be cleaned of generated files after run completion
    :type cleanup: bool
    """
    logger.info(
        "Loading LEMS file: {} and running with jNeuroML".format(lems_file_name)
    )
    post_args = ""
    post_args += gui_string(nogui)
    post_args += include_string(paths_to_include)

    t_run = datetime.now()

    if not skip_run:
        success = run_jneuroml(
            "",
            lems_file_name,
            post_args,
            max_memory=max_memory,
            exec_in_dir=exec_in_dir,
            verbose=verbose,
            report_jnml_output=verbose,
            exit_on_fail=exit_on_fail,
        )

    if not success:
        return False

    if load_saved_data:
        return reload_saved_data(
            lems_file_name,
            base_dir=exec_in_dir,
            t_run=t_run,
            plot=plot,
            show_plot_already=show_plot_already,
            simulator="jNeuroML",
            reload_events=reload_events,
            remove_dat_files_after_load=cleanup,
        )
    else:
        return True


def nml2_to_svg(
    nml2_file_name: str,
    max_memory: str = DEFAULTS["default_java_max_memory"],
    verbose: bool = True,
) -> None:
    """Generate the SVG representation of a NeuroML model using jnml

    :param nml2_file_name: name of NeuroML2 file to generate SVG for
    :type nml2_file_name: str
    :param max_memory: maximum memory allowed for use by the JVM
    :type max_memory: str
    :param verbose: toggle whether jnml should print verbose information
    :type verbose: bool
    """
    logger.info("Converting NeuroML2 file: {} to SVG".format(nml2_file_name))

    post_args = "-svg"

    run_jneuroml("", nml2_file_name, post_args, max_memory=max_memory, verbose=verbose)


def nml2_to_png(
    nml2_file_name: str,
    max_memory: str = DEFAULTS["default_java_max_memory"],
    verbose: bool = True,
) -> None:
    """Generate the PNG representation of a NeuroML model using jnml

    :param nml2_file_name: name of NeuroML2 file to generate PNG for
    :type nml2_file_name: str
    :param max_memory: maximum memory allowed for use by the JVM
    :type max_memory: str
    :param verbose: toggle whether jnml should print verbose information
    :type verbose: bool
    """
    logger.info("Converting NeuroML2 file: %s to PNG" % nml2_file_name)

    post_args = "-png"

    run_jneuroml("", nml2_file_name, post_args, max_memory=max_memory, verbose=verbose)


def include_string(paths_to_include: typing.Union[str, tuple[str], list[str]]) -> str:
    """Convert a path or list of paths into an include string to be used by
    jnml.

    :param paths_to_include: path or list or tuple of paths to be included
    :type paths_to_include: str or list(str) or tuple(str)
    :returns: include string to be used with jnml.
    """
    if paths_to_include:
        if type(paths_to_include) is str:
            paths_to_include = [paths_to_include]
    if type(paths_to_include) in (tuple, list):
        result = " -I '%s'" % ":".join(paths_to_include)
    else:
        result = ""
    return result


def gui_string(nogui: bool) -> str:
    """Return the gui string for jnml

    :param nogui: toggle whether GUI should be used or not
    :type nogui: bool
    :returns: gui  string or empty string
    """
    return " -nogui" if nogui else ""


def run_lems_with(engine: str, *args: typing.Any, **kwargs: typing.Any):
    """Run LEMS with specified engine.

    Wrapper around the many `run_lems_with_*` methods.
    The engine should be the suffix, for example, to use
    `run_lems_with_jneuroml_neuron`, engine will be `jneuroml_neuron`.

    All kwargs are passed as is to the function. Please see the individual
    function documentations for information on arguments.

    :param engine: engine to run with
    :type engine: string (valid names are methods)
    :param *args: postional arguments to pass to run function
    :param **kwargs: named arguments to pass to run function
    :returns: return value of called method

    """
    function_tuple = inspect.getmembers(sys.modules[__name__], inspect.isfunction)
    found = False
    for fname, function in function_tuple:
        if fname.startswith("run_lems_with") and fname.endswith(engine):
            print(f"Running with {fname}")
            found = True
            return function(*args, **kwargs)

    if found is False:
        logger.error(f"Could not find engine {engine}. Exiting.")
        return False


def run_lems_with_jneuroml_neuron(
    lems_file_name: str,
    paths_to_include: list[str] = [],
    max_memory: str = DEFAULTS["default_java_max_memory"],
    skip_run: bool = False,
    nogui: bool = False,
    load_saved_data: bool = False,
    reload_events: bool = False,
    plot: bool = False,
    show_plot_already: bool = True,
    exec_in_dir: str = ".",
    only_generate_scripts: bool = False,
    compile_mods: bool = True,
    verbose: bool = DEFAULTS["v"],
    exit_on_fail: bool = True,
    cleanup: bool = False,
    realtime_output: bool = False,
) -> typing.Union[bool, typing.Union[dict, tuple[dict, dict]]]:
    # jnml_runs_neuron=True):  #jnml_runs_neuron=False is Work in progress!!!
    """Run LEMS file with the NEURON simulator

    Tip: set `skip_run=True` to only parse the LEMS file but not run the simulation.

    :param lems_file_name: name of LEMS file to run
    :type lems_file_name: str
    :param paths_to_include: additional directory paths to include (for other NML/LEMS files, for example)
    :type paths_to_include: list(str)
    :param max_memory: maximum memory allowed for use by the JVM
    :type max_memory: bool
    :param skip_run: toggle whether run should be skipped, if skipped, file will only be parsed
    :type skip_run: bool
    :param nogui: toggle whether jnml GUI should be shown
    :type nogui: bool
    :param load_saved_data: toggle whether any saved data should be loaded
    :type load_saved_data: bool
    :param reload_events: toggle whether events should be reloaded
    :type reload_events: bool
    :param plot: toggle whether specified plots should be plotted
    :type plot: bool
    :param show_plot_already: toggle whether prepared plots should be shown
    :type show_plot_already: bool
    :param exec_in_dir: working directory to execute LEMS simulation in
    :type exec_in_dir: str
    :param only_generate_scripts: toggle whether only the runner script should be generated
    :type only_generate_scripts: bool
    :param compile_mods: toggle whether generated mod files should be compiled
    :type compile_mods: bool
    :param verbose: toggle whether jnml should print verbose information
    :type verbose: bool
    :param exit_on_fail: toggle whether command should exit if jnml fails
    :type exit_on_fail: bool
    :param cleanup: toggle whether the directory should be cleaned of generated files after run completion
    :type cleanup: bool
    :param realtime_output: toggle whether realtime output should be shown
    :type realtime_output: bool
    """

    logger.info(
        "Loading LEMS file: {} and running with jNeuroML_NEURON".format(lems_file_name)
    )

    post_args = " -neuron"
    if not only_generate_scripts:  # and jnml_runs_neuron:
        post_args += " -run"
    if compile_mods:
        post_args += " -compile"

    post_args += gui_string(nogui)
    post_args += include_string(paths_to_include)

    t_run = datetime.now()
    if skip_run:
        success = True
    else:
        # Fix PYTHONPATH for NEURON: has been an issue on HBP Collaboratory...
        if "PYTHONPATH" not in os.environ:
            os.environ["PYTHONPATH"] = ""
        for path in sys.path:
            if path + ":" not in os.environ["PYTHONPATH"]:
                os.environ["PYTHONPATH"] = "%s:%s" % (path, os.environ["PYTHONPATH"])

        logger.debug("PYTHONPATH for NEURON: {}".format(os.environ["PYTHONPATH"]))

        if realtime_output:
            success = run_jneuroml_with_realtime_output(
                "",
                lems_file_name,
                post_args,
                max_memory=max_memory,
                exec_in_dir=exec_in_dir,
                verbose=verbose,
                exit_on_fail=exit_on_fail,
            )
            logger.debug("PYTHONPATH for NEURON: {}".format(os.environ["PYTHONPATH"]))
        else:
            success = run_jneuroml(
                "",
                lems_file_name,
                post_args,
                max_memory=max_memory,
                exec_in_dir=exec_in_dir,
                verbose=verbose,
                report_jnml_output=verbose,
                exit_on_fail=exit_on_fail,
            )

        """
        TODO: Work in progress!!!
        if not jnml_runs_neuron:
          logger.info("Running...")
          from LEMS_NML2_Ex5_DetCell_nrn import NeuronSimulation
          ns = NeuronSimulation(tstop=300, dt=0.01, seed=123456789)
          ns.run()
        """

    if not success:
        return False

    if load_saved_data:
        return reload_saved_data(
            lems_file_name,
            base_dir=exec_in_dir,
            t_run=t_run,
            plot=plot,
            show_plot_already=show_plot_already,
            simulator="jNeuroML_NEURON",
            reload_events=reload_events,
            remove_dat_files_after_load=cleanup,
        )
    else:
        return True


def run_lems_with_jneuroml_netpyne(
    lems_file_name: str,
    paths_to_include: list[str] = [],
    max_memory: str = DEFAULTS["default_java_max_memory"],
    skip_run: bool = False,
    nogui: bool = False,
    num_processors: int = 1,
    load_saved_data: bool = False,
    reload_events: bool = False,
    plot: bool = False,
    show_plot_already: bool = True,
    exec_in_dir: str = ".",
    only_generate_scripts: bool = False,
    only_generate_json: bool = False,
    verbose: bool = DEFAULTS["v"],
    exit_on_fail: bool = True,
    return_string: bool = False,
    cleanup: bool = False,
) -> typing.Union[bool, tuple[bool, str], typing.Union[dict, tuple[dict, dict]]]:
    """Run LEMS file with the NEURON simulator

    Tip: set `skip_run=True` to only parse the LEMS file but not run the simulation.

    :param lems_file_name: name of LEMS file to run
    :type lems_file_name: str
    :param paths_to_include: additional directory paths to include (for other NML/LEMS files, for example)
    :type paths_to_include: list(str)
    :param max_memory: maximum memory allowed for use by the JVM
    :type max_memory: bool
    :param skip_run: toggle whether run should be skipped, if skipped, file will only be parsed
    :type skip_run: bool
    :param nogui: toggle whether jnml GUI should be shown
    :type nogui: bool
    :param num_processors: number of processors to use for running NetPyNE
    :type num_processors: int
    :param load_saved_data: toggle whether any saved data should be loaded
    :type load_saved_data: bool
    :param reload_events: toggle whether events should be reloaded
    :type reload_events: bool
    :param plot: toggle whether specified plots should be plotted
    :type plot: bool
    :param show_plot_already: toggle whether prepared plots should be shown
    :type show_plot_already: bool
    :param exec_in_dir: working directory to execute LEMS simulation in
    :type exec_in_dir: str
    :param only_generate_scripts: toggle whether only the runner script should be generated
    :type only_generate_scripts: bool
    :param verbose: toggle whether jnml should print verbose information
    :type verbose: bool
    :param exit_on_fail: toggle whether command should exit if jnml fails
    :type exit_on_fail: bool
    :param return_string: toggle whether command output string should be returned
    :type return_string: bool
    :param cleanup: toggle whether the directory should be cleaned of generated files after run completion
    :type cleanup: bool
    :returns: either a bool, or a Tuple (bool, str) depending on the value of
        return_string: True of jnml ran successfully, False if not; along with the
        output of the command. If load_saved_data is True, it returns a dict
        with the data

    """

    logger.info(
        "Loading LEMS file: {} and running with jNeuroML_NetPyNE".format(lems_file_name)
    )

    post_args = " -netpyne"

    if num_processors != 1:
        post_args += " -np %i" % num_processors
    if not only_generate_scripts and not only_generate_json:
        post_args += " -run"
    if only_generate_json:
        post_args += " -json"

    post_args += gui_string(nogui)
    post_args += include_string(paths_to_include)

    t_run = datetime.now()
    if skip_run:
        success = True
    else:
        if return_string is True:
            (success, output_string) = run_jneuroml(
                "",
                lems_file_name,
                post_args,
                max_memory=max_memory,
                exec_in_dir=exec_in_dir,
                verbose=verbose,
                exit_on_fail=exit_on_fail,
                return_string=True,
            )
        else:
            success = run_jneuroml(
                "",
                lems_file_name,
                post_args,
                max_memory=max_memory,
                exec_in_dir=exec_in_dir,
                verbose=verbose,
                exit_on_fail=exit_on_fail,
                return_string=False,
            )

    if not success and return_string is True:
        return False, output_string
    if not success and return_string is False:
        return False

    if load_saved_data:
        return reload_saved_data(
            lems_file_name,
            base_dir=exec_in_dir,
            t_run=t_run,
            plot=plot,
            show_plot_already=show_plot_already,
            simulator="jNeuroML_NetPyNE",
            reload_events=reload_events,
            remove_dat_files_after_load=cleanup,
        )

    if return_string is True:
        return True, output_string

    return True


# TODO: need to enable run with Brian2!
def run_lems_with_jneuroml_brian2(
    lems_file_name: str,
    paths_to_include: list[str] = [],
    max_memory: str = DEFAULTS["default_java_max_memory"],
    skip_run: bool = False,
    nogui: bool = False,
    load_saved_data: bool = False,
    reload_events: bool = False,
    plot: bool = False,
    show_plot_already: bool = True,
    exec_in_dir: str = ".",
    verbose: bool = DEFAULTS["v"],
    exit_on_fail: bool = True,
    cleanup: bool = False,
) -> typing.Union[bool, typing.Union[dict, tuple[dict, dict]]]:
    """Run LEMS file with the NEURON simulator

    Tip: set `skip_run=True` to only parse the LEMS file but not run the simulation.

    :param lems_file_name: name of LEMS file to run
    :type lems_file_name: str
    :param paths_to_include: additional directory paths to include (for other NML/LEMS files, for example)
    :type paths_to_include: list(str)
    :param max_memory: maximum memory allowed for use by the JVM
    :type max_memory: bool
    :param skip_run: toggle whether run should be skipped, if skipped, file will only be parsed
    :type skip_run: bool
    :param nogui: toggle whether jnml GUI should be shown
    :type nogui: bool
    :param load_saved_data: toggle whether any saved data should be loaded
    :type load_saved_data: bool
    :param reload_events: toggle whether events should be reloaded
    :type reload_events: bool
    :param plot: toggle whether specified plots should be plotted
    :type plot: bool
    :param show_plot_already: toggle whether prepared plots should be shown
    :type show_plot_already: bool
    :param exec_in_dir: working directory to execute LEMS simulation in
    :type exec_in_dir: str
    :param verbose: toggle whether jnml should print verbose information
    :type verbose: bool
    :param exit_on_fail: toggle whether command should exit if jnml fails
    :type exit_on_fail: bool
    :param cleanup: toggle whether the directory should be cleaned of generated files after run completion
    :type cleanup: bool
    """

    logger.info(
        "Loading LEMS file: {} and running with jNeuroML_Brian2".format(lems_file_name)
    )

    post_args = " -brian2"

    # post_args += gui_string(nogui)
    # post_args += include_string(paths_to_include)

    t_run = datetime.now()
    if skip_run:
        success = True
    else:
        success = run_jneuroml(
            "",
            lems_file_name,
            post_args,
            max_memory=max_memory,
            exec_in_dir=exec_in_dir,
            verbose=verbose,
            exit_on_fail=exit_on_fail,
        )

        old_sys_args = [a for a in sys.argv]
        sys.argv[1] = "-nogui"  # To supress gui for brian simulation...
        logger.info(
            "Importing generated Brian2 python file (changed args from {} to {})".format(
                old_sys_args, sys.argv
            )
        )
        brian2_py_name = lems_file_name.replace(".xml", "_brian2")
        exec("import %s" % brian2_py_name)
        sys.argv = old_sys_args
        logger.info("Finished Brian2 simulation, back to {}".format(sys.argv))

    if not success:
        return False

    if load_saved_data:
        return reload_saved_data(
            lems_file_name,
            base_dir=exec_in_dir,
            t_run=t_run,
            plot=plot,
            show_plot_already=show_plot_already,
            simulator="jNeuroML_Brian2",
            reload_events=reload_events,
            remove_dat_files_after_load=cleanup,
        )
    else:
        return True


def run_lems_with_eden(
    lems_file_name: str,
    load_saved_data: bool = False,
    reload_events: bool = False,
    verbose: bool = DEFAULTS["v"],
) -> typing.Union[bool, typing.Union[dict, tuple[dict, dict]]]:
    """Run LEMS file with the EDEN simulator

    :param lems_file_name: name of LEMS file to run
    :type lems_file_name: str
    :param load_saved_data: toggle whether any saved data should be loaded
    :type load_saved_data: bool
    :param reload_events: toggle whether events should be reloaded
    :type reload_events: bool
    :param verbose: toggle whether to print verbose information
    :type verbose: bool
    """

    import eden_simulator

    logger.info(
        "Running a simulation of %s in EDEN v%s"
        % (
            lems_file_name,
            eden_simulator.__version__
            if hasattr(eden_simulator, "__version__")
            else "???",
        )
    )

    results = eden_simulator.runEden(lems_file_name)

    if verbose:
        logger.info(
            "Completed simulation in EDEN, saved results: %s" % (results.keys())
        )

    if load_saved_data:
        logger.warning("Event saving is not yet supported in EDEN!!")
        return results, {}
    elif load_saved_data:
        return results
    else:
        return True


def reload_saved_data(
    lems_file_name: str,
    base_dir: str = ".",
    t_run: datetime = datetime(1900, 1, 1),
    plot: bool = False,
    show_plot_already: bool = True,
    simulator: typing.Optional[str] = None,
    reload_events: bool = False,
    verbose: bool = DEFAULTS["v"],
    remove_dat_files_after_load: bool = False,
) -> typing.Union[dict, tuple[dict, dict]]:
    """Reload data saved from previous LEMS simulation run.

    :param lems_file_name: name of LEMS file that was used to generate the data
    :type lems_file_name: str
    :param base_dir: directory to run in
    :type base_dir: str
    :param t_run: time of run
    :type t_run: datetime
    :param plot: toggle plotting
    :type plot: bool
    :param show_plot_already: toggle if plots should be shown
    :type show_plot_already: bool
    :param simulator: simulator that was used to generate data
    :type simulator: str
    :param reload_event: toggle whether events should be loaded
    :type reload_event: bool
    :param verbose: toggle verbose output
    :type verbose: bool
    :param remove_dat_files_after_load: toggle if data files should be deleted after they've been loaded
    :type remove_dat_files_after_load: bool


    TODO: remove unused vebose argument (needs checking to see if is being
    used in other places)
    """
    if not os.path.isfile(lems_file_name):
        real_lems_file = os.path.realpath(os.path.join(base_dir, lems_file_name))
    else:
        real_lems_file = os.path.realpath(lems_file_name)

    logger.debug(
        "Reloading data specified in LEMS file: %s (%s), base_dir: %s, cwd: %s; plotting %s"
        % (lems_file_name, real_lems_file, base_dir, os.getcwd(), show_plot_already)
    )

    # Could use pylems to parse all this...
    traces = {}  # type: dict
    events = {}  # type: dict

    if plot:
        import matplotlib.pyplot as plt

    base_lems_file_path = os.path.dirname(os.path.realpath(lems_file_name))
    tree = etree.parse(real_lems_file)

    sim = tree.getroot().find("Simulation")
    ns_prefix = ""

    possible_prefixes = ["{http://www.neuroml.org/lems/0.7.2}"]
    if sim is None:
        # print(tree.getroot().nsmap)
        # print(tree.getroot().getchildren())
        for pre in possible_prefixes:
            for comp in tree.getroot().findall(pre + "Component"):
                if comp.attrib["type"] == "Simulation":
                    ns_prefix = pre
                    sim = comp

    if reload_events:
        event_output_files = sim.findall(ns_prefix + "EventOutputFile")
        for i, of in enumerate(event_output_files):
            name = of.attrib["fileName"]
            file_name = os.path.join(base_dir, name)
            if not os.path.isfile(file_name):  # If not relative to the LEMS file...
                file_name = os.path.join(base_lems_file_path, name)

            # if not os.path.isfile(file_name): # If not relative to the LEMS file...
            #    file_name = os.path.join(os.getcwd(),name)
            # ... try relative to cwd.
            # if not os.path.isfile(file_name): # If not relative to the LEMS file...
            #    file_name = os.path.join(os.getcwd(),'NeuroML2','results',name)
            # ... try relative to cwd in NeuroML2/results subdir.
            if not os.path.isfile(file_name):  # If not relative to the base dir...
                raise OSError(
                    ("Could not find simulation output " "file %s" % file_name)
                )
            format = of.attrib["format"]
            logger.info(
                "Loading saved events from %s (format: %s)" % (file_name, format)
            )
            selections = {}
            for col in of.findall(ns_prefix + "EventSelection"):
                id = int(col.attrib["id"])
                select = col.attrib["select"]
                events[select] = []
                selections[id] = select

            with open(file_name) as f:
                for line in f:
                    values = line.split()
                    if format == "TIME_ID":
                        t = float(values[0])
                        id = int(values[1])
                    elif format == "ID_TIME":
                        id = int(values[0])
                        t = float(values[1])
                    logger.debug(
                        "Found a event in cell %s (%s) at t = %s"
                        % (id, selections[id], t)
                    )
                    events[selections[id]].append(t)

            if remove_dat_files_after_load:
                logger.warning(
                    "Removing file %s after having loading its data!" % file_name
                )
                os.remove(file_name)

    output_files = sim.findall(ns_prefix + "OutputFile")
    n_output_files = len(output_files)
    if plot:
        rows = int(max(1, math.ceil(n_output_files / float(3))))
        columns = min(3, n_output_files)
        fig, ax = plt.subplots(
            rows, columns, sharex=True, figsize=(8 * columns, 4 * rows)
        )
        if n_output_files > 1:
            ax = ax.ravel()

    for i, of in enumerate(output_files):
        traces["t"] = []
        name = of.attrib["fileName"]
        file_name = os.path.join(base_dir, name)

        if not os.path.isfile(file_name):  # If not relative to the LEMS file...
            file_name = os.path.join(base_lems_file_path, name)

        if not os.path.isfile(file_name):  # If not relative to the LEMS file...
            file_name = os.path.join(os.getcwd(), name)

            # ... try relative to cwd.
        if not os.path.isfile(file_name):  # If not relative to the LEMS file...
            file_name = os.path.join(os.getcwd(), "NeuroML2", "results", name)
            # ... try relative to cwd in NeuroML2/results subdir.
        if not os.path.isfile(file_name):  # If not relative to the LEMS file...
            raise OSError(("Could not find simulation output " "file %s" % file_name))
        t_file_mod = datetime.fromtimestamp(os.path.getmtime(file_name))
        if t_file_mod < t_run:
            raise Exception(
                "Expected output file %s has not been modified since "
                "%s but the simulation was run later at %s."
                % (file_name, t_file_mod, t_run)
            )

        logger.debug(
            "Loading saved data from %s%s"
            % (file_name, " (%s)" % simulator if simulator else "")
        )

        cols = []
        cols.append("t")
        for col in of.findall(ns_prefix + "OutputColumn"):
            quantity = col.attrib["quantity"]
            traces[quantity] = []
            cols.append(quantity)

        with open(file_name) as f:
            for line in f:
                values = line.split()
                for vi in range(len(values)):
                    traces[cols[vi]].append(float(values[vi]))

        if remove_dat_files_after_load:
            logger.warning(
                "Removing file %s after having loading its data!" % file_name
            )
            os.remove(file_name)

        if plot:
            info = "Data loaded from %s%s" % (
                file_name,
                " (%s)" % simulator if simulator else "",
            )
            logger.warning("Reloading: %s" % info)
            plt.get_current_fig_manager().set_window_title(info)

            legend = False
            for key in cols:
                if n_output_files > 1:
                    ax_ = ax[i]
                else:
                    ax_ = ax
                ax_.set_xlabel("Time (ms)")
                ax_.set_ylabel("(SI units...)")
                ax_.xaxis.grid(True)
                ax_.yaxis.grid(True)

                if key != "t":
                    ax_.plot(traces["t"], traces[key], label=key)
                    logger.debug("Adding trace for: %s, from: %s" % (key, file_name))
                    ax_.used = True
                    legend = True

                if legend:
                    if n_output_files > 1:
                        ax_.legend(
                            loc="upper right", fancybox=True, shadow=True, ncol=4
                        )  # ,bbox_to_anchor=(0.5, -0.05))
                    else:
                        ax_.legend(
                            loc="upper center",
                            bbox_to_anchor=(0.5, -0.05),
                            fancybox=True,
                            shadow=True,
                            ncol=4,
                        )

    #  print(traces.keys())

    if plot and show_plot_already:
        if n_output_files > 1:
            ax_ = ax
        else:
            ax_ = [ax]
        for axi in ax_:
            if not hasattr(axi, "used") or not axi.used:
                axi.axis("off")
        plt.tight_layout()
        plt.show()

    if reload_events:
        return traces, events
    else:
        return traces


def confirm_file_exists(filename: str) -> None:
    """Check if a file exists, exit if it does not.

    :param filename: the filename to check
    :type filename: str
    """
    if not os.path.isfile(filename):
        logger.critical("Unable to find file: %s!" % filename)
        sys.exit(FILE_NOT_FOUND_ERR)


def confirm_neuroml_file(filename: str) -> None:
    """Confirm that file exists and is a NeuroML file before proceeding with
    processing.

    :param filename: Names of files to check
    :type filename: str
    """
    # print('Checking file: %s'%filename)
    # Some conditions to check if a LEMS file was entered
    # TODO: Ideally we'd like to check the root node: checking file extensions is brittle
    confirm_file_exists(filename)
    if filename.startswith("LEMS_"):
        logger.warning(
            textwrap.dedent(
                """
            *************************************************************************************
            **  Warning, you may be trying to use a LEMS XML file (containing <Simulation> etc.)
            **  for a pyNeuroML option when a NeuroML2 file is required...
            *************************************************************************************
            """
            )
        )


def confirm_lems_file(filename: str) -> None:
    """Confirm that file exists and is a LEMS file before proceeding with
    processing.

    :param filename: Names of files to check
    :type filename: list of strings
    """
    # print('Checking file: %s'%filename)
    # Some conditions to check if a LEMS file was entered
    # TODO: Ideally we'd like to check the root node: checking file extensions is brittle
    confirm_file_exists(filename)
    if filename.endswith("nml"):
        logger.warning(
            textwrap.dedent(
                """
            *************************************************************************************
            **  Warning, you may be trying to use a NeuroML2 file for a pyNeuroML option
            **  when a LEMS XML file (containing <Simulation> etc.) is required...
            *************************************************************************************
            """
            )
        )


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


def evaluate_arguments(args):
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


def get_path_to_jnml_jar() -> str:
    """Get the path to the jNeuroML jar included with PyNeuroML.

    :returns: path of jar file
    """
    script_dir = os.path.dirname(os.path.realpath(__file__))
    jar_path = os.path.join(
        script_dir, "lib", "jNeuroML-%s-jar-with-dependencies.jar" % JNEUROML_VERSION
    )
    return jar_path


def run_jneuroml(
    pre_args: str,
    target_file: str,
    post_args: str,
    max_memory: str = DEFAULTS["default_java_max_memory"],
    exec_in_dir: str = ".",
    verbose: bool = DEFAULTS["v"],
    report_jnml_output: bool = True,
    exit_on_fail: bool = False,
    return_string: bool = False,
) -> typing.Union[tuple[bool, str], bool]:
    """Run jnml with provided arguments.

    :param pre_args: pre-file name arguments
    :type pre_args: list of strings
    :param target_file: LEMS or NeuroML file to run jnml on
    :type target_file: str
    :param max_memory: maximum memory allowed for use by the JVM
    :type max_memory: bool
    :param exec_in_dir: working directory to execute LEMS simulation in
    :type exec_in_dir: str
    :param verbose: toggle whether jnml should print verbose information
    :type verbose: bool
    :param report_jnml_output: toggle whether jnml output should be printed
    :type report_jnml_output: bool
    :param exit_on_fail: toggle whether command should exit if jnml fails
    :type exit_on_fail: bool
    :param return_string: toggle whether the output string should be returned
    :type return_string: bool

    :returns: either a bool, or a Tuple (bool, str) depending on the value of
        return_string: True of jnml ran successfully, False if not; along with the
        output of the command

    """
    logger.debug(
        "Running jnml on %s with pre args: [%s], post args: [%s], in dir: %s, verbose: %s, report: %s, exit on fail: %s"
        % (
            target_file,
            pre_args,
            post_args,
            exec_in_dir,
            verbose,
            report_jnml_output,
            exit_on_fail,
        )
    )
    if post_args and "nogui" in post_args and not os.name == "nt":
        pre_jar = " -Djava.awt.headless=true"
    else:
        pre_jar = ""

    jar_path = get_path_to_jnml_jar()
    output = ""
    retcode = -1

    try:
        command = f'java -Xmx{max_memory} {pre_jar} -jar  "{jar_path}" {pre_args} {target_file} {post_args}'
        retcode, output = execute_command_in_dir(
            command, exec_in_dir, verbose=verbose, prefix=" jNeuroML >>  "
        )

        if retcode != 0:
            if exit_on_fail:
                logger.error("execute_command_in_dir returned with output: %s" % output)
                sys.exit(retcode)
            else:
                if return_string:
                    return (False, output)
                else:
                    return False

        if report_jnml_output:
            logger.debug(
                "Successfully ran the following command using pyNeuroML v%s: \n    %s"
                % (__version__, command)
            )
            logger.debug("Output:\n\n%s" % output)

    #  except KeyboardInterrupt as e:
    #    raise e

    except Exception as e:
        logger.error("*** Execution of jnml has failed! ***")
        logger.error("Error:  %s" % e)
        logger.error("*** Command: %s ***" % command)
        logger.error("Output: %s" % output)
        if exit_on_fail:
            sys.exit(UNKNOWN_ERR)
        else:
            if return_string:
                return (False, output)
            else:
                return False
    if return_string:
        return (True, output)
    else:
        return True


# TODO: Refactorinng
def run_jneuroml_with_realtime_output(
    pre_args: str,
    target_file: str,
    post_args: str,
    max_memory: str = DEFAULTS["default_java_max_memory"],
    exec_in_dir: str = ".",
    verbose: bool = DEFAULTS["v"],
    exit_on_fail: bool = True,
) -> bool:
    # XXX: Only tested with Linux
    """Run jnml with provided arguments with realtime output.

    NOTE: this has only been tested on Linux.

    :param pre_args: pre-file name arguments
    :type pre_args: list of strings
    :param target_file: LEMS or NeuroML file to run jnml on
    :type target_file: str
    :param max_memory: maximum memory allowed for use by the JVM
    :type max_memory: bool
    :param exec_in_dir: working directory to execute LEMS simulation in
    :type exec_in_dir: str
    :param verbose: toggle whether jnml should print verbose information
    :type verbose: bool
    :param exit_on_fail: toggle whether command should exit if jnml fails
    :type exit_on_fail: bool
    """
    if post_args and "nogui" in post_args and not os.name == "nt":
        pre_jar = " -Djava.awt.headless=true"
    else:
        pre_jar = ""
    jar_path = get_path_to_jnml_jar()

    command = ""
    command_success = False

    try:
        command = 'java -Xmx%s %s -jar  "%s" %s "%s" %s' % (
            max_memory,
            pre_jar,
            jar_path,
            pre_args,
            target_file,
            post_args,
        )
        command_success = execute_command_in_dir_with_realtime_output(
            command, exec_in_dir, verbose=verbose, prefix=" jNeuroML >>  "
        )

    except KeyboardInterrupt as e:
        raise e
    except:
        logger.error("*** Execution of jnml has failed! ***")
        logger.error("*** Command: %s ***" % command)
        if exit_on_fail:
            sys.exit(UNKNOWN_ERR)
        else:
            return False

    return command_success


def execute_command_in_dir_with_realtime_output(
    command: str,
    directory: str,
    verbose: bool = DEFAULTS["v"],
    prefix: str = "Output: ",
    env: typing.Optional[str] = None,
) -> bool:
    # NOTE: Only tested with Linux
    """Run a command in a given directory with real time output.

    NOTE: this has only been tested on Linux.

    :param command: command to run
    :type command: str
    :param directory: directory to run command in
    :type directory: str
    :param verbose: toggle verbose output
    :type verbose: bool
    :param prefix: string to prefix output with
    :type prefix: str
    :param env: environment variables to be used
    :type env: str
    """
    if os.name == "nt":
        directory = os.path.normpath(directory)

    print("####################################################################")
    print("# pyNeuroML executing: (%s) in directory: %s" % (command, directory))
    if env is not None:
        print("# Extra env variables %s" % (env))
    print("####################################################################")

    p = None
    try:
        p = subprocess.Popen(
            shlex.split(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            cwd=directory,
            env=env,
            universal_newlines=True,
        )
        with p.stdout:
            for line in iter(p.stdout.readline, ""):
                print("# %s" % line.strip())
        p.wait()  # wait for the subprocess to exit

        print("####################################################################")
    except KeyboardInterrupt as e:
        logger.error("*** Command interrupted: \n       %s" % command)
        if p:
            p.kill()
        raise e
    except Exception as e:
        print("# Exception occured: %s" % (e))
        print("# More...")
        print(traceback.format_exc())
        print("####################################################################")
        raise e

    if not p.returncode == 0:
        logger.critical(
            "*** Problem running command (return code: %s): \n       %s"
            % (p.returncode, command)
        )

    return p.returncode == 0


def execute_command_in_dir(
    command: str,
    directory: str,
    verbose: bool = DEFAULTS["v"],
    prefix: str = "Output: ",
    env: typing.Any = None,
) -> tuple[int, str]:
    """Execute a command in specific working directory

    :param command: command to run
    :type command: str
    :param directory: directory to run command in
    :type directory: str
    :param verbose: toggle verbose output
    :type verbose: bool
    :param prefix: string to prefix console output with
    :type prefix: str
    :param env: environment variables to be used
    :type env: str
    """
    return_string = ""  # type: typing.Union[bytes, str]
    if os.name == "nt":
        directory = os.path.normpath(directory)

    logger.info("Executing: (%s) in directory: %s" % (command, directory))
    if env is not None:
        logger.debug("Extra env variables %s" % (env))

    try:
        if os.name == "nt":
            return_string = subprocess.check_output(
                command, cwd=directory, shell=True, env=env, close_fds=False
            )
        else:
            return_string = subprocess.check_output(
                command,
                cwd=directory,
                shell=True,
                stderr=subprocess.STDOUT,
                env=env,
                close_fds=True,
            )

        return_string = return_string.decode("utf-8")  # For Python 3

        logger.info("Command completed successfully!")
        if verbose:
            logger.info(
                "Output: \n %s%s"
                % (prefix, return_string.replace("\n", "\n " + prefix))
            )
        return (0, return_string)

    except AttributeError:
        # For python 2.6...
        logger.warning("Assuming Python 2.6...")

        return_string = subprocess.Popen(
            command, cwd=directory, shell=True, stdout=subprocess.PIPE
        ).communicate()[0]
        return return_string.decode("utf-8")

    except subprocess.CalledProcessError as e:
        logger.critical("*** Problem running command: \n       %s" % e)
        logger.critical(
            "%s%s" % (prefix, e.output.decode().replace("\n", "\n" + prefix))
        )
        return (e.returncode, e.output.decode())
    except Exception as e:
        logger.critical("*** Unknown problem running command: %s" % e)
        return (-1, str(e))


"""
    As usually saved by jLEMS, etc. First column is time (in seconds), multiple other columns
"""


def reload_standard_dat_file(file_name: str) -> tuple[dict, list]:
    """Reload a datafile as usually saved by jLEMS, etc.
    First column is time (in seconds), multiple other columns.

    :param file_name: name of data file to load
    :type file_name: str
    :returns: tuple of (data, column names)
    """
    with open(file_name) as dat_file:
        data = {}  # type: dict
        indeces = []  # type: list
        for line in dat_file:
            words = line.split()

            if "t" not in data.keys():
                data["t"] = []
                for i in range(len(words) - 1):
                    data[i] = []
                    indeces.append(i)
            data["t"].append(float(words[0]))
            for i in range(len(words) - 1):
                data[i].append(float(words[i + 1]))

        logger.info("Loaded data from %s; columns: %s" % (file_name, indeces))
    return data, indeces


def _find_elements(el, name, rdf=False):
    ns = "http://www.neuroml.org/schema/neuroml2"
    if rdf:
        ns = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    return el.findall(".//{%s}%s" % (ns, name))


def _get_attr_in_element(el, name, rdf=False):
    ns = "http://www.neuroml.org/schema/neuroml2"
    if rdf:
        ns = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    aname = "{%s}%s" % (ns, name)
    return el.attrib[aname] if aname in el.attrib else None


def extract_annotations(nml2_file: str) -> None:
    """Extract and print annotations from a NeuroML 2 file.

    :param nml2_file: name of NeuroML2 file to parse
    :type nml2_file: str
    """
    pp = pprint.PrettyPrinter()
    test_file = open(nml2_file)
    root = etree.parse(test_file).getroot()
    annotations = {}  # type: dict

    for a in _find_elements(root, "annotation"):
        for r in _find_elements(a, "Description", rdf=True):
            desc = _get_attr_in_element(r, "about", rdf=True)
            annotations[desc] = []

            for info in r:
                if isinstance(info.tag, str):
                    kind = info.tag.replace(
                        "{http://biomodels.net/biology-qualifiers/}", "bqbiol:"
                    )
                    kind = kind.replace(
                        "{http://biomodels.net/model-qualifiers/}", "bqmodel:"
                    )

                    for li in _find_elements(info, "li", rdf=True):
                        attr = _get_attr_in_element(li, "resource", rdf=True)
                        if attr:
                            annotations[desc].append({kind: attr})

    logger.info("Annotations in %s: " % (nml2_file))
    pp.pprint(annotations)


"""
Work in progress: expand a (simple) ComponentType  and evaluate an instance of it by
giving parameters & required variables
Used in MOOSE NeuroML reader...
"""


def evaluate_component(comp_type, req_variables={}, parameter_values={}):
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
        args = parse_arguments()

    evaluate_arguments(args)


if __name__ == "__main__":
    main()
