"""
run a model using the tellurium engine
"""

import tellurium as te

te.setDefaultPlottingEngine("matplotlib")

import sys

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
        # check validity of sedml file here

        try:
            doc = libsedml.readSedML(file_name)
        except Exception:
            raise IOError(f"readSedML failed trying to open the file {file_name}")

        # execute SED-ML using Tellurium
        te.executeSEDML(doc.toSed(), workingDir=".")
