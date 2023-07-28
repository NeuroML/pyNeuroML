#!/usr/bin/env python3
"""
The utils package contains various utility functions to aid users working with
PyNeuroML

Copyright 2023 NeuroML Contributors
"""

import logging
import os
import re
import time
import typing
from pathlib import Path

import neuroml

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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


def get_files_generated_after(
    timestamp: float = time.time(),
    directory: str = ".",
    ignore_suffixes: typing.List[str] = ["xml", "nml"],
    include_suffixes: typing.List[str] = [],
) -> typing.List[str]:
    """Get files modified after provided time stamp in directory, excluding provided suffixes.

    Currently ignores directories.

    .. versionadded:: 1.0.9

    :param timestamp: time stamp to compare to
    :type timestamp: float
    :param directory: directory to list files of
    :type directory: str
    :param ignore_suffixes: file suffixes to ignore (none if empty)
    :type ignore_suffixes: str
    :param include_suffixes: file suffixes to include (all if empty)
    :type include_suffixes: str
    :returns: list of file names
    :rtype: list(str)

    """
    logger.debug(f"Timestamp is: {timestamp}")
    current_files = list(Path(directory).glob("*"))
    # only files, ignore directories
    current_files = [f for f in current_files if f.is_file()]
    files = []
    for file in current_files:
        excluded = False
        for sfx in ignore_suffixes:
            if file.name.endswith(sfx):
                excluded = True
                break

        # no need to proceed
        if excluded is True:
            continue

        included = False
        # if no suffixes, ignore this
        if len(include_suffixes) == 0:
            included = True
        else:
            for sfx in include_suffixes:
                if file.name.endswith(sfx):
                    included = True
                    break

        # no need to proceed
        if included is False:
            continue

        file_mtime = os.path.getmtime(file)
        if file_mtime > timestamp:
            files.append(file.name)

    return files
