#!/usr/bin/env python3
"""
The utils package contains various utility functions to aid users working with
PyNeuroML

Copyright 2023 NeuroML Contributors
"""

import typing
import logging
import re
import neuroml


logger = logging.getLogger(__name__)


MAX_COLOUR = (255, 0, 0)  # type: typing.Tuple[int, int, int]
MIN_COLOUR = (255, 255, 0)  # type: typing.Tuple[int, int, int]


def extract_position_info(
    nml_model: neuroml.NeuroMLDocument, verbose: bool = False
) -> tuple:
    """Extract position information from a NeuroML model

    Returns a tuple of dictionaries:

    - cell_id_vs_cell: dict(cell id, cell object)
    - pop_id_vs_cell: dict(pop id, cell object)
    - positions: dict(pop id, dict(cell id, position in x, y, z))
    - pop_id_vs_color: dict(pop id, colour property)
    - pop_id_vs_radii: dict(pop id, radius property)

    :param nml_model: NeuroML2 model to extract position information from
    :type nml_model: NeuroMLDocument
    :param verbose: toggle function verbosity
    :type verbose: bool
    :returns: [cell id vs cell dict, pop id vs cell dict, positions dict, pop id vs colour dict, pop id vs radii dict]
    :rtype: tuple of dicts
    """

    cell_id_vs_cell = {}
    positions = {}
    pop_id_vs_cell = {}
    pop_id_vs_color = {}
    pop_id_vs_radii = {}

    cell_elements = []
    cell_elements.extend(nml_model.cells)
    cell_elements.extend(nml_model.cell2_ca_poolses)

    for cell in cell_elements:
        cell_id_vs_cell[cell.id] = cell

    if len(nml_model.networks) > 0:
        popElements = nml_model.networks[0].populations
    else:
        popElements = []
        net = neuroml.Network(id="x")
        nml_model.networks.append(net)
        cell_str = ""
        for cell in cell_elements:
            pop = neuroml.Population(
                id="dummy_population_%s" % cell.id, size=1, component=cell.id
            )
            net.populations.append(pop)
            cell_str += cell.id + "__"
        net.id = cell_str[:-2]

        popElements = nml_model.networks[0].populations

    for pop in popElements:
        name = pop.id
        celltype = pop.component
        instances = pop.instances

        if pop.component in cell_id_vs_cell.keys():
            pop_id_vs_cell[pop.id] = cell_id_vs_cell[pop.component]
        else:
            pop_id_vs_cell[pop.id] = None

        info = "Population: %s has %i positioned cells of type: %s" % (
            name,
            len(instances),
            celltype,
        )
        if verbose:
            print(info)

        colour = "b"
        substitute_radius = None

        props = []
        props.extend(pop.properties)
        """ TODO
        if pop.annotation:
            props.extend(pop.annotation.properties)"""

        for prop in props:
            # print(prop)
            if prop.tag == "color":
                color = prop.value
                color = (
                    float(color.split(" ")[0]),
                    float(color.split(" ")[1]),
                    float(color.split(" ")[2]),
                )

                pop_id_vs_color[pop.id] = color
                logger.debug(f"Colour determined to be: {color}")
            if prop.tag == "radius":
                substitute_radius = float(prop.value)
                pop_id_vs_radii[pop.id] = substitute_radius

        pop_positions = {}

        if len(instances) > 0:
            for instance in instances:
                location = instance.location
                id = int(instance.id)

                x = float(location.x)
                y = float(location.y)
                z = float(location.z)
                pop_positions[id] = (x, y, z)
        else:
            for id in range(pop.size):
                pop_positions[id] = (0, 0, 0)

        positions[name] = pop_positions

    return cell_id_vs_cell, pop_id_vs_cell, positions, pop_id_vs_color, pop_id_vs_radii


def convert_case(name):
    """Converts from camelCase to under_score"""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def get_ion_color(ion: str) -> str:
    """Get colours for ions in hex format.

    Hard codes for na, k, ca, h. All others get a grey.

    :param ion: name of ion
    :type ion: str
    :returns: colour in hex
    :rtype: str
    """
    if ion.lower() == "na":
        col = "#1E90FF"
    elif ion.lower() == "k":
        col = "#CD5C5C"
    elif ion.lower() == "ca":
        col = "#8FBC8F"
    elif ion.lower() == "h":
        col = "#ffd9b3"
    else:
        col = "#A9A9A9"

    return col


def get_colour_hex(
    fract: float,
    min_colour: typing.Tuple[int, int, int] = MIN_COLOUR,
    max_colour: typing.Tuple[int, int, int] = MAX_COLOUR,
) -> str:
    """Get colour hex at fraction between `min_colour` and `max_colour`.

    :param fract: fraction between `min_colour` and `max_colour`
    :type fract: float between (0, 1)
    :param min_colour: lower colour tuple (R, G, B)
    :type min_colour: tuple
    :param max_colour upper colour tuple (R, G, B)
    :type max_colour: tuple
    :returns: colour in hex representation
    :rtype: string
    """
    rgb = [hex(int(x + (y - x) * fract)) for x, y in zip(min_colour, max_colour)]
    col = "#"
    for c in rgb:
        col += c[2:4] if len(c) == 4 else "00"
    return col


def get_state_color(s: str) -> str:
    """Get colours for state variables.

    Hard codes for m, k, r, h, l, n, a, b, c, q, e, f, p, s, u.

    :param state: name of state
    :type state: str
    :returns: colour in hex format
    :rtype: str
    """
    col = "#000000"
    if s.startswith("m"):
        col = "#FF0000"
    if s.startswith("k"):
        col = "#FF0000"
    if s.startswith("r"):
        col = "#FF0000"
    if s.startswith("h"):
        col = "#00FF00"
    if s.startswith("l"):
        col = "#00FF00"
    if s.startswith("n"):
        col = "#0000FF"
    if s.startswith("a"):
        col = "#FF0000"
    if s.startswith("b"):
        col = "#00FF00"
    if s.startswith("c"):
        col = "#0000FF"
    if s.startswith("q"):
        col = "#FF00FF"
    if s.startswith("e"):
        col = "#00FFFF"
    if s.startswith("f"):
        col = "#DDDD00"
    if s.startswith("p"):
        col = "#880000"
    if s.startswith("s"):
        col = "#888800"
    if s.startswith("u"):
        col = "#880088"

    return col
