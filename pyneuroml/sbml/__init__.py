"""
use libsbml.SBMLDocument.checkConsistency to check validaity of an SBML document
based on https://github.com/combine-org/combine-notebooks/blob/main/src/combine_notebooks/validation/validation_sbml.py
"""

import os
import errno
from typing import List


import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    import libsbml
    from libsbml import SBMLReader
except ImportError:
    logger.warning("Please install optional dependencies to use SBML features:")
    logger.warning("pip install pyneuroml[combine]")


def validate_sbml_files(input_files: List[str], strict_units: bool = False) -> bool:
    """Validate input files using libsbml.SBMLDocument.checkConsistency

    .. versionadded:: 1.1.5

    :param input_files: a list of one or more filepaths
    :type input_files: list(str)
    :param strict_units: toggle whether unit consistency warnings should be
        treated as errors
    :type strict_units: bool
    :returns: True if all files are valid, else False
    :rtype: bool
    """

    if not len(input_files) >= 1:
        raise ValueError("No input files specified")

    all_valid = True

    for file_name in input_files:
        # These checks are already implemented by SBMLReader
        # But could just be logged along with the other error types rather than causing exceptions
        if not os.path.isfile(file_name):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file_name)

        if not os.access(file_name, os.R_OK):
            raise IOError(f"Could not read SBML file {file_name}")

        try:
            reader = SBMLReader()
            doc = reader.readSBML(file_name)
        except Exception:
            # usually errors are logged within the doc object rather than being thrown
            raise IOError(f"SBMLReader failed trying to open the file {file_name}")

        # Always check for unit consistency
        doc.setConsistencyChecks(libsbml.LIBSBML_CAT_UNITS_CONSISTENCY, True)
        doc.checkConsistency()

        # Get errors/warnings arising from the file reading or consistency checking calls above
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
        print(f"{'Validating SBML'}: {file_name}")
        print(f"{'Validation error(s)':<25}: {len(errors)}")
        print(f"{'Validation warning(s)':<25}: {len(warnings)}")

        if len(errors) > 0:
            all_valid = False
            print("--- errors ---")
            for kerr in enumerate(errors):
                print(f"E{kerr[0]}: {error.getCategoryAsString()} L{error.getLine()}")
                print(
                    f"[{error.getSeverityAsString()}] {error.getShortMessage()} | {error.getMessage()}"
                )

        if len(warnings) > 0:
            print("--- warnings ---")
            for kwarn in enumerate(warnings):
                print(f"E{kwarn[0]}: {error.getCategoryAsString()} L{error.getLine()}")
                print(
                    f"[{error.getSeverityAsString()}] {error.getShortMessage()} | {error.getMessage()}"
                )

        print("-" * 80)

    return all_valid
