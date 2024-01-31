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


def run_from_sedml_file(sedml_file):
    "read a SEDML file and run the model using tellurium's executeSEDML command"

    sedml_doc = libsedml.readSedML(sedml_file)
    n_errors = sedml_doc.getErrorLog().getNumFailsWithSeverity(
        libsedml.LIBSEDML_SEV_ERROR
    )
    print("Read SED-ML file %s, number of errors: %i" % (sedml_file, n_errors))
    if n_errors > 0:
        print(sedml_doc.getErrorLog().toString())

    print(sedml_doc)

    print(dir(sedml_doc))
    print(sedml_doc.toSed())

    # execute SED-ML using Tellurium
    te.executeSEDML(sedml_doc.toSed(), workingDir=".")
