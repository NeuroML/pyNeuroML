"""
use libsbml.SBMLDocument.checkConsistency to check validaity of an SBML document
based on https://github.com/combine-org/combine-notebooks/blob/main/src/combine_notebooks/validation/validation_sbml.py
"""

import os
import libsbml
from libsbml import SBMLReader
from typing import List


def validate_sbml_files(input_files: List[str], strict_units: bool = False) -> bool:
    """
    validate each input file using libsbml.SBMLDocument.checkConsistency
    input_files is a list of one or more filepaths
    strict_units converts unit consistency warnings into errors
    """

    if not len(input_files) >= 1:
        raise Exception("No input files specified")

    all_valid = True

    for file_name in input_files:
        if not os.path.isfile(file_name):
            raise OSError(f"Could not find SBML file {file_name}")

        reader = SBMLReader()

        try:
            doc = reader.readSBML(file_name)
        except Exception:
            raise OSError(f"SBMLReader failed to load the file {file_name}")

        # Always check for unit consistency
        doc.setConsistencyChecks(libsbml.LIBSBML_CAT_UNITS_CONSISTENCY, True)
        doc.checkConsistency()

        # Get errors/warnings
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
            elif (
                (strict_units is True)
                # For error code definitions see
                # https://github.com/sbmlteam/libsbml/blob/fee56c943ea39b9ac1f8491cac2fc9b3665e368f/src/sbml/SBMLError.h#L528
                # and sbml.level-3.version-2.core.release-2.pdf page 159
                and (error.getErrorId() >= 10500)
                and (error.getErrorId() <= 10599)
            ):
                # Treat unit consistency warnings as errors
                errors.append(error)
            else:
                warnings.append(error)

        # print results
        print("-" * 80)
        print(f"{'validation error(s)':<25}: {len(errors)}")
        print(f"{'validation warning(s)':<25}: {len(warnings)}")

        if len(errors) > 0:
            all_valid = False
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

    return all_valid
