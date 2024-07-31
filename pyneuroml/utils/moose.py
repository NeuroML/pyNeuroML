#!/usr/bin/env python3
"""
Utils for moose:
https://github.com/BhallaLab/moose-core/

File: pyneuroml/utils/moose.py

Copyright 2024 NeuroML contributors
"""

import logging
import typing

import neuroml

from .units import get_value_in_si

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def evaluate_component(
    comp_type: neuroml.ComponentType,
    req_variables: typing.Dict[str, str] = {},
    parameter_values: typing.Dict[str, str] = {},
) -> typing.Dict[str, str]:
    """
    Expand a (simple) ComponentType  and evaluate an instance of it by
    giving parameters & required variables

    This is used in MOOSE NeuroML reader:
    https://github.com/BhallaLab/moose-core/blob/a6db169d10d47043710abe003a9c605b4a6a6ea9/python/moose/neuroml2/reader.py

    Note that this is still a WIP.

    :param comp_type: component type to evaluate
    :type comp_type: neuroml.ComponentType
    :param req_variables: dictionary holding variables and their values
    :type req_variables: dict
    :param parameter_values: dictionary holding parameters and their values
    :type parameter_values: dict

    :returns: dict of conditional derived variables and their calculated values
    :rtype: dict
    """
    logger.debug(
        "Evaluating %s with req:%s; params:%s"
        % (comp_type.name, req_variables, parameter_values)
    )
    exec_str = ""
    return_vals: typing.Dict[str, str] = {}
    for p in parameter_values:
        exec_str += "%s = %s\n" % (p, get_value_in_si(parameter_values[p]))
    for r in req_variables:
        exec_str += "%s = %s\n" % (r, get_value_in_si(req_variables[r]))
    for c in comp_type.Constant:
        exec_str += "%s = %s\n" % (c.name, get_value_in_si(c.value))
    for d in comp_type.Dynamics:
        for dv in d.DerivedVariable:
            exec_str += "%s = %s\n" % (dv.name, dv.value)
            exec_str += 'return_vals["%s"] = %s\n' % (dv.name, dv.name)
        for cdv in d.ConditionalDerivedVariable:
            for case in cdv.Case:
                if case.condition:
                    cond = (
                        case.condition.replace(".neq.", "!=")
                        .replace(".eq.", "==")
                        .replace(".gt.", ">")
                        .replace(".lt.", "<")
                    )
                    exec_str += "if ( %s ): %s = %s \n" % (cond, cdv.name, case.value)
                else:
                    exec_str += "else: %s = %s \n" % (cdv.name, case.value)

            exec_str += "\n"

            exec_str += 'return_vals["%s"] = %s\n' % (cdv.name, cdv.name)
    exec_str = "from math import exp  # only one required for nml2?\n" + exec_str
    # logger.info('Exec %s'%exec_str)
    exec(exec_str)

    return return_vals
