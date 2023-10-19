#!/usr/bin/env python3
"""
The utils package contains various utility functions to aid users working with
PyNeuroML

Copyright 2023 NeuroML Contributors
"""

import copy
import datetime
import logging
import math
import os
import random
import re
import string
import time
import typing
from pathlib import Path

import neuroml
import numpy

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
    popElements = []

    cell_elements.extend(nml_model.cells)
    cell_elements.extend(nml_model.cell2_ca_poolses)

    # if the model does not include a network, plot all the cells in the
    # model in new dummy populations
    if len(nml_model.networks) == 0:
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

    for cell in cell_elements:
        cell_id_vs_cell[cell.id] = cell

    for pop in popElements:
        name = pop.id
        celltype = pop.component
        instances = pop.instances

        if celltype in cell_id_vs_cell.keys():
            pop_id_vs_cell[name] = cell_id_vs_cell[celltype]
        else:
            pop_id_vs_cell[name] = None

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
    :param max_colour: upper colour tuple (R, G, B)
    :type max_colour: tuple
    :returns: colour in hex representation
    :rtype: str
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


def rotate_cell(
    cell: neuroml.Cell,
    x: float = 0,
    y: float = 0,
    z: float = 0,
    order: str = "xyz",
    relative_to_soma: bool = False,
) -> neuroml.Cell:
    """Return a new cell object rotated in the provided order along the
    provided angles (in radians) relative to the soma position.

    :param cell: cell object to rotate
    :type cell: neuroml.Cell
    :param x: angle to rotate around x axis, in radians
    :type x: float
    :param y: angle to rotate around y axis, in radians
    :type y: float
    :param z: angle to rotate around z axis, in radians
    :type z: float
    :param order: rotation order in terms of x, y,  and z
    :type order: str
    :param relative_to_soma: whether rotation is relative to soma
    :type relative_to_soma: bool
    :returns: new neuroml.Cell object
    :rtype: neuroml.Cell

    Derived from LFPy's implementation:
    https://github.com/LFPy/LFPy/blob/master/LFPy/cell.py#L1600
    """

    valid_orders = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]
    if order not in valid_orders:
        raise ValueError(f"order must be one of {valid_orders}")

    soma_seg_id = cell.get_morphology_root()
    soma_seg = cell.get_segment(soma_seg_id)
    cell_origin = numpy.array(
        [soma_seg.proximal.x, soma_seg.proximal.y, soma_seg.proximal.z]
    )
    newcell = copy.deepcopy(cell)
    print(f"Rotating {newcell.id} by {x}, {y}, {z}")

    # calculate rotations
    if x != 0:
        anglex = x
        rotation_x = numpy.array(
            [
                [1, 0, 0],
                [0, math.cos(anglex), -math.sin(anglex)],
                [0, math.sin(anglex), math.cos(anglex)],
            ]
        )
        logger.debug(f"x matrix is: {rotation_x}")

    if y != 0:
        angley = y
        rotation_y = numpy.array(
            [
                [math.cos(angley), 0, math.sin(angley)],
                [0, 1, 0],
                [-math.sin(angley), 0, math.cos(angley)],
            ]
        )
        logger.debug(f"y matrix is: {rotation_y}")

    if z != 0:
        anglez = z
        rotation_z = numpy.array(
            [
                [math.cos(anglez), -math.sin(anglez), 0],
                [math.sin(anglez), math.cos(anglez), 0],
                [0, 0, 1],
            ]
        )
        logger.debug(f"z matrix is: {rotation_z}")

    # rotate each segment
    for aseg in newcell.morphology.segments:
        prox = dist = numpy.array([])
        # may not have a proximal
        try:
            prox = numpy.array([aseg.proximal.x, aseg.proximal.y, aseg.proximal.z])
        except AttributeError:
            pass

        # must have distal
        dist = numpy.array([aseg.distal.x, aseg.distal.y, aseg.distal.z])

        if relative_to_soma:
            if prox.any():
                prox = prox - cell_origin
            dist = dist - cell_origin

        # rotate
        for axis in order:
            if axis == "x" and x != 0:
                if prox.any():
                    prox = numpy.dot(prox, rotation_x)
                dist = numpy.dot(dist, rotation_x)

            if axis == "y" and y != 0:
                if prox.any():
                    prox = numpy.dot(prox, rotation_y)
                dist = numpy.dot(dist, rotation_y)

            if axis == "z" and z != 0:
                if prox.any():
                    prox = numpy.dot(prox, rotation_z)
                dist = numpy.dot(dist, rotation_z)

        if relative_to_soma:
            if prox.any():
                prox = prox + cell_origin
            dist = dist + cell_origin

        if prox.any():
            aseg.proximal.x = prox[0]
            aseg.proximal.y = prox[1]
            aseg.proximal.z = prox[2]

        aseg.distal.x = dist[0]
        aseg.distal.y = dist[1]
        aseg.distal.z = dist[2]

        logger.debug(f"prox is: {aseg.proximal}")
        logger.debug(f"distal is: {aseg.distal}")

    return newcell


def get_pyneuroml_tempdir(rootdir: str = ".", prefix: str = "pyneuroml"):
    """Generate a pyneuroml directory name that can be used for various
    purposes.

    Default format: {rootdir}/{prefix}_{timestamp}_{6 random characters}

    :param rootdir: root directory where to create the new directory
    :type rootdir: str
    :param prefix: prefix for directory name
    :type prefix: str
    :returns: generated directory name
    :rtype: str

    """
    timestamp = datetime.datetime.now().strftime("%y%m%d%H%M%S")
    random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    tdir = rootdir + "/" + f"{prefix}_{timestamp}_{random_suffix}/"

    return tdir
