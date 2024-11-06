#!/usr/bin/env python3
"""
Methods related to IO.

File: pyneuroml/io.py

Copyright 2024 NeuroML contributors
"""

import inspect
import logging
import os
import sys
import textwrap
import typing
from typing import Optional

import lems.model.model as lems_model
import neuroml.loaders as loaders
import neuroml.writers as writers
from lxml import etree
from neuroml import NeuroMLDocument

from pyneuroml.errors import ARGUMENT_ERR, FILE_NOT_FOUND_ERR, NMLFileTypeError
from pyneuroml.validators import validate_neuroml2

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def read_neuroml2_file(
    nml2_file_name: str,
    include_includes: bool = False,
    verbose: bool = False,
    already_included: Optional[list] = None,
    optimized: bool = False,
    check_validity_pre_include: bool = False,
    fix_external_morphs_biophys: bool = False,
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
    :param fix_external_morphs_biophys: if a cell element has a morphology (or biophysicalProperties) attribute, as opposed to a subelement morphology/biophysicalProperties, substitute the external element into the cell element for ease of access
    :type fix_external_morphs_biophys: bool
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
                inc = True  # type: typing.Union[bool, typing.Tuple[bool, str]]
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

        if fix_external_morphs_biophys:
            from neuroml.utils import fix_external_morphs_biophys_in_cell

            fix_external_morphs_biophys_in_cell(nml2_doc)

    return nml2_doc


def write_neuroml2_file(
    nml2_doc: NeuroMLDocument,
    nml2_file_name: str,
    validate: bool = True,
    verbose_validate: bool = False,
    hdf5: bool = False,
) -> typing.Optional[typing.Union[bool, typing.Tuple[bool, str]]]:
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
    return None


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


def confirm_file_exists(filename: str) -> None:
    """Check if a file exists, exit if it does not.

    :param filename: the filename to check
    :type filename: str
    """
    if not os.path.isfile(filename):
        logger.critical("Unable to find file: %s!" % filename)
        sys.exit(FILE_NOT_FOUND_ERR)


def confirm_neuroml_file(filename: str, sys_error: bool = False) -> None:
    """Confirm that file exists and is a NeuroML file before proceeding with
    processing.

    :param filename: Names of files to check
    :type filename: str
    :param sys_error: toggle whether function should exit or raise exception
    :type sys_error: bool
    """
    error_string = textwrap.dedent(
        """
    *************************************************************************************
    **  You may be trying to use a LEMS XML file (containing <Simulation> etc.)
    **  for a pyNeuroML option when a NeuroML2 file is required.
    *************************************************************************************
    """
    )

    try:
        confirm_file_type(filename, ["nml"], "neuroml")
    except NMLFileTypeError as e:
        if filename.startswith("LEMS_"):
            logger.warning(error_string)
        if sys_error is True:
            logger.error(e)
            sys.exit(ARGUMENT_ERR)
        else:
            raise e


def confirm_lems_file(filename: str, sys_error: bool = False) -> None:
    """Confirm that file exists and is a LEMS file before proceeding with
    processing.

    :param filename: Names of files to check
    :type filename: list of strings
    :param sys_error: toggle whether function should exit or raise exception
    :type sys_error: bool
    """
    error_string = textwrap.dedent(
        """
    *************************************************************************************
    **  You may be trying to use a NeuroML2 file for a pyNeuroML option
    **  when a LEMS XML file (containing <Simulation> etc.) is required.
    *************************************************************************************
    """
    )
    try:
        confirm_file_type(filename, ["xml"], "lems")
    except NMLFileTypeError as e:
        if filename.endswith("nml"):
            logger.warning(error_string)
        if sys_error is True:
            logger.error(e)
            sys.exit(ARGUMENT_ERR)
        else:
            raise e


def confirm_file_type(
    filename: str,
    file_exts: typing.List[str],
    root_tag: typing.Optional[str] = None,
    error_str: typing.Optional[str] = None,
    sys_error: bool = False,
) -> None:
    """Confirm that a file exists and is of the provided type.

    First we rely on file extensions to test for type, since this is the
    simplest way. If this test fails, we read the full file and test the root
    tag if one has been provided.

    :param filename: filename to confirm
    :type filename: str
    :param file_exts: list of valid file extensions, without the leading dot
    :type file_exts: list of strings
    :param root_tag: root tag for file, used if extensions do not match
    :type root_tag: str
    :param error_str: an optional error string to print along with the thrown
        exception
    :type error_str: string (optional)

    :raises NMLFileTypeError: if file does not have one of the provided extensions

    """
    confirm_file_exists(filename)
    filename_ext = filename.split(".")[-1]

    matched = False

    if filename_ext in file_exts:
        matched = True

    got_root_tag = None

    if matched is False:
        if root_tag is not None:
            with open(filename) as i_file:
                xml_tree = etree.parse(i_file)
                tree_root = xml_tree.getroot()
                got_root_tag = tree_root.tag

                if got_root_tag.lower() == root_tag.lower():
                    matched = True

    if matched is False:
        error_string = f"Expected file extension does not match: {', '.join(file_exts)}; got {filename_ext}."

        if root_tag is not None:
            error_string += (
                f" Expected root tag does not match: {root_tag}; got {got_root_tag}"
            )

        if error_str is not None:
            error_string += "\n" + error_str
        if sys_error is True:
            logger.error(error_string)
            sys.exit(ARGUMENT_ERR)
        else:
            raise NMLFileTypeError(error_string)
