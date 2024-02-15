#!/usr/bin/env python3
"""
Methods related to validation of NeuroML models

File: pyneuroml/validators.py

Copyright 2024 NeuroML contributors
"""


import logging
import typing
import warnings

from pyneuroml import DEFAULTS
from pyneuroml.runners import run_jneuroml

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def validate_neuroml1(
    nml1_file_name: str, verbose_validate: bool = True, return_string: bool = False
) -> typing.Union[bool, typing.Tuple[bool, str]]:
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
) -> typing.Union[bool, typing.Tuple[bool, str]]:
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
