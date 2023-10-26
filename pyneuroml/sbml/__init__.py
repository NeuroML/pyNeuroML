"""
use libsbml.SBMLDocument.checkConsistency to check validaity of an SBML document
based on https://github.com/combine-org/combine-notebooks/blob/main/src/combine_notebooks/validation/validation_sbml.py
"""

import os
import libsbml
from libsbml import SBMLDocument, SBMLReader

def validate_sbml_files(input_files : str,units_consistency: bool = False):
    '''
    validate each input file using libsbml.SBMLDocument.checkConsistency
    input_files is a space separated list of one or more filepaths
    '''

    for file_name in input_files.split():
        if not os.path.isfile(file_name):
            raise OSError(
                ("Could not find SBML file %s" % file_name)
            )

        try:
            reader = SBMLReader()
            doc = reader.readSBML(file_name)
        except:
            raise OSError(
                ("SBMLReader failed to load the file %s" % file_name)
            )

        # set the unit checking, similar for the other settings
        doc.setConsistencyChecks(libsbml.LIBSBML_CAT_UNITS_CONSISTENCY, units_consistency)
        doc.checkConsistency()
        # get errors/warnings
        n_errors: int = doc.getNumErrors()
        errors: List[libsbml.SBMLError] = list()
        warnings: List[libsbml.SBMLError] = list()
        for k in range(n_errors):
            error: libsbml.SBMLError = doc.getError(k)
            severity = error.getSeverity()
            if (severity == libsbml.LIBSBML_SEV_ERROR) or (
                severity == libsbml.LIBSBML_SEV_FATAL
            ):
                errors.append(error)
            else:
                warnings.append(error)
        # print results
        print("-" * 80)
        print(f"{'validation error(s)':<25}: {len(errors)}")
        print(f"{'validation warning(s)':<25}: {len(warnings)}")
        if len(errors) > 0:
            print("--- errors ---")
            for kerr in enumerate(errors):
                print(f"E{kerr}: {error.getCategoryAsString()} L{error.getLine()}")
                print(
                    f"[{error.getSeverityAsString()}] {error.getShortMessage()} | {error.getMessage()}"
                )
        if len(warnings) > 0:
            print("--- warnings ---")
            for kwarn in enumerate(warnings):
                print(f"E{kwarn}: {error.getCategoryAsString()} L{error.getLine()}")
                print(
                    f"[{error.getSeverityAsString()}] {error.getShortMessage()} | {error.getMessage()}"
                )
        print("-" * 80)