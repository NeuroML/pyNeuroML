"""
run a model using the tellurium engine
"""

import logging
import os

from pyneuroml.sedml import validate_sedml_files

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    import tellurium as te

    te.setDefaultPlottingEngine("matplotlib")
except ImportError:
    logger.warning("Please install optional dependencies to use Tellurium features:")
    logger.warning("pip install pyneuroml[tellurium]")

try:
    import libsedml
except ImportError:
    logger.warning("Please install optional dependencies to use SED-ML features:")
    logger.warning("pip install pyneuroml[combine]")


# # For technical reasons, any software which uses libSEDML
# # must provide a custom build - Tellurium uses tesedml
# try:
#     import libsedml
# except ImportError:
#     import tesedml as libsedml


def run_from_sedml_file(input_files, args):
    "read a SEDML file and run it using tellurium's executeSEDML command"

    # input_files list is a shared option with commands that can take >1 filename
    # therefore datatype is a list not a single filename
    if not len(input_files) >= 1:
        raise ValueError("No input files specified")

    if len(input_files) > 1:
        raise ValueError("Only a single input file is supported")

    # set default output directory
    outputdir = "."
    saveoutputs = True

    if "-outputdir" in args:
        try:
            outputdir = args[args.index("-outputdir") + 1]
        except Exception:
            raise ValueError("Incorrectly specified outputdir")

        if outputdir == "none":
            outputdir = None
            saveoutputs = False

    file_name = input_files[0]

    # tellurium seems not to do much validation so we do our own here
    if not validate_sedml_files([file_name]):
        raise IOError(f"failed to validate SEDML file {file_name}")

    try:
        doc = libsedml.readSedML(file_name)
    except Exception:
        raise IOError(f"readSedML failed trying to open the file {file_name}")

    working_dir = os.path.dirname(file_name)
    if working_dir == "":
        working_dir = "."
    to_sed = doc.toSed()

    # execute SED-ML using Tellurium
    te.executeSEDML(
        to_sed,
        workingDir=working_dir,
        createOutputs=True,
        saveOutputs=saveoutputs,
        outputDir=outputdir,
    )
