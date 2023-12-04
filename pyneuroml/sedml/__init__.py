"""
use libsedml getErrorLog().getNumFailsWithSeverity(libsedml.LIBSEDML_SEV_ERROR) to validate SEDML file(s)
based on example here https://github.com/SED-ML/libSEDML/blob/master/examples/python/echo_sedml.py
"""

import os
import errno
import libsedml
from typing import List


def validate_sedml_files(input_files: List[str]) -> bool:
    """
    validate SEDML file(s)
    input_files is a list of one or more filepaths
    """

    if not len(input_files) >= 1:
        raise ValueError("No input files specified")

    all_valid = True

    for file_name in input_files:
        if not os.path.isfile(file_name):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file_name)

        if not os.access(file_name, os.R_OK):
            raise IOError(f"Could not read SEDML file {file_name}")

        try:
            doc = libsedml.readSedML(file_name)
        except Exception:
            raise IOError(f"readSedML failed trying to open the file {file_name}")

        if doc.getErrorLog().getNumFailsWithSeverity(libsedml.LIBSEDML_SEV_ERROR) > 0:
            all_valid = False
            print(doc.getErrorLog().toString())

    return all_valid
