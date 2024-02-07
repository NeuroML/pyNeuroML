"""
run a model using the tellurium engine
"""

from pyneuroml.sedml import validate_sedml_files
import tellurium as te

te.setDefaultPlottingEngine("matplotlib")

import sys
import os

# For technical reasons, any software which uses libSEDML
# must provide a custom build - Tellurium uses tesedml
try:
    import libsedml
except ImportError:
    import tesedml as libsedml


def run_from_sedml_file(input_files):
    "read a SEDML file(s) and run the model(s) using tellurium's executeSEDML command"

    if not len(input_files) >= 1:
        raise ValueError("No input files specified")

    for file_name in input_files:
        # tellurium seems not to do much validation so we do our own here
        if not validate_sedml_files([file_name]):
            raise IOError(f"failed to validate SEDML file {file_name}")

        try:
            doc = libsedml.readSedML(file_name)
        except Exception:
            raise IOError(f"readSedML failed trying to open the file {file_name}")

        # execute SED-ML using Tellurium
        working_dir = os.path.dirname(file_name)
        if working_dir == "":
            working_dir = "."
        to_sed = doc.toSed()
        te.executeSEDML(to_sed, workingDir=working_dir)
