#!/usr/bin/env python3
"""
Methods related to units.

File: pyneuroml/utils/units.py

Copyright 2024 NeuroML contributors
"""


import logging
import typing
import zipfile

import lems.model.model as lems_model
from lems.parser.LEMS import LEMSFileParser
import pyneuroml.utils.misc as pymisc

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


lems_model_with_units = None


def split_nml2_quantity(nml2_quantity: str) -> typing.Tuple[float, str]:
    """Split a NeuroML 2 quantity into its magnitude and units

    :param nml2_quantity: NeuroML2 quantity to split
    :type nml2_quantity:
    :returns: a tuple (magnitude, unit)
    """
    magnitude = None
    i = len(nml2_quantity)
    while magnitude is None:
        try:
            part = nml2_quantity[0:i]
            nn = float(part)
            magnitude = nn
            unit = nml2_quantity[i:]
        except ValueError:
            i = i - 1

    return magnitude, unit


def get_value_in_si(nml2_quantity: str) -> typing.Union[float, None]:
    """Get value of a NeuroML2 quantity in SI units

    :param nml2_quantity: NeuroML2 quantity to convert
    :type nml2_quantity: str
    :returns: value in SI units (float)
    """
    try:
        return float(nml2_quantity)
    except ValueError:
        model = get_lems_model_with_units()
        m, u = split_nml2_quantity(nml2_quantity)
        si_value = None
        for un in model.units:
            if un.symbol == u:
                si_value = (m + un.offset) * un.scale * pow(10, un.power)
        return si_value


def convert_to_units(nml2_quantity: str, unit: str) -> float:
    """Convert a NeuroML2 quantity to provided unit.

    :param nml2_quantity: NeuroML2 quantity to convert
    :type nml2_quantity: str
    :param unit: unit to convert to
    :type unit: str
    :returns: converted value (float)
    """
    model = get_lems_model_with_units()
    m, u = split_nml2_quantity(nml2_quantity)
    si_value = None
    dim = None
    for un in model.units:
        if un.symbol == u:
            si_value = (m + un.offset) * un.scale * pow(10, un.power)
            dim = un.dimension

    for un in model.units:
        if un.symbol == unit:
            new_value = si_value / (un.scale * pow(10, un.power)) - un.offset
            if not un.dimension == dim:
                raise Exception(
                    "Cannot convert {} to {}. Dimensions of units ({}/{}) do not match!".format(
                        nml2_quantity, unit, dim, un.dimension
                    )
                )

    logger.debug(
        "Converting {} {} to {}: {} ({} in SI units)".format(
            m, u, unit, new_value, si_value
        )
    )

    return new_value


def get_lems_model_with_units() -> lems_model.Model:
    """
    Get a LEMS model with NeuroML core dimensions and units.

    :returns: a `lems.model.model.Model` that includes NeuroML dimensions and units.
    """
    global lems_model_with_units

    if lems_model_with_units is None:
        jar_path = pymisc.get_path_to_jnml_jar()
        logger.debug(
            "Loading standard NeuroML2 dimension/unit definitions from %s" % jar_path
        )
        jar = zipfile.ZipFile(jar_path, "r")
        dims_units = jar.read("NeuroML2CoreTypes/NeuroMLCoreDimensions.xml")
        lems_model_with_units = lems_model.Model(include_includes=False)
        parser = LEMSFileParser(lems_model_with_units)
        parser.parse(dims_units)

    return lems_model_with_units
