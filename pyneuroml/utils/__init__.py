#!/usr/bin/env python3
"""
The utils package contains various utility functions to aid users working with
PyNeuroML. Many of these methods are meant for internal use in the package and
so may change in the future: the API here is not considered stable.

Copyright 2024 NeuroML Contributors
"""

import copy
import logging
import math
import os
import pathlib
import random
import re
import string
import sys
import tempfile
import time
import typing
import zipfile
from datetime import datetime
from pathlib import Path

import neuroml
import numpy
import pyneuroml.utils.misc
from lems.model.model import Model
from neuroml.loaders import read_neuroml2_file
from pyneuroml.errors import UNKNOWN_ERR
from pyneuroml.utils.plot import get_next_hex_color


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    import libsedml
except ModuleNotFoundError:
    logger.warning("Please install optional dependencies to use SED-ML features:")
    logger.warning("pip install pyneuroml[combine]")


MAX_COLOUR = (255, 0, 0)  # type: typing.Tuple[int, int, int]
MIN_COLOUR = (255, 255, 0)  # type: typing.Tuple[int, int, int]

STANDARD_LEMS_FILES = [
    "Cells.xml",
    "Channels.xml",
    "Inputs.xml",
    "Networks.xml",
    "NeuroML2CoreTypes.xml",
    "NeuroMLCoreCompTypes.xml",
    "NeuroMLCoreDimensions.xml",
    "PyNN.xml",
    "Simulation.xml",
    "Synapses.xml",
]


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

    if s.startswith("m"):
        col = "#FF0000"
    elif s.startswith("k"):
        col = "#FF0000"
    elif s.startswith("r"):
        col = "#FF0000"
    elif s.startswith("h"):
        col = "#00FF00"
    elif s.startswith("l"):
        col = "#00FF00"
    elif s.startswith("n"):
        col = "#0000FF"
    elif s.startswith("a"):
        col = "#FF0000"
    elif s.startswith("b"):
        col = "#00FF00"
    elif s.startswith("c"):
        col = "#0000FF"
    elif s.startswith("q"):
        col = "#FF00FF"
    elif s.startswith("e"):
        col = "#00FFFF"
    elif s.startswith("f"):
        col = "#DDDD00"
    elif s.startswith("p"):
        col = "#880000"
    elif s.startswith("s"):
        col = "#888800"
    elif s.startswith("u"):
        col = "#880088"
    else:
        col = get_next_hex_color()

    return col


def rotate_cell(
    cell: neuroml.Cell,
    x: float = 0,
    y: float = 0,
    z: float = 0,
    order: str = "xyz",
    relative_to_soma: bool = False,
    inplace: bool = False,
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
    :param inplace: toggle whether the cell object should be modified inplace
        or a copy created (creates and returns a copy by default)

    :type inplace: bool
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

    if not inplace:
        newcell = copy.deepcopy(cell)
    else:
        newcell = cell

    logger.info(f"Rotating {newcell.id} by {x}, {y}, {z}")

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


def translate_cell_to_coords(
    cell: neuroml.Cell,
    inplace: bool = False,
    dest: typing.List[float] = [0, 0, 0],
) -> neuroml.Cell:
    """Translate cell so that its soma moves to given coordinates

    .. versionadded:: 1.2.13

    :param cell: cell object to translate
    :type cell: neuroml.Cell
    :param inplace: toggle whether the cell object should be modified inplace
        or a copy created (creates and returns a copy by default)
    :type inplace: bool
    :param dest: destination coordinates (x,y,z) for cell's root
    :type dest: list[x,y,z]
    :returns: new neuroml.Cell object
    :rtype: neuroml.Cell

    """
    soma_seg_id = cell.get_morphology_root()
    soma_seg = cell.get_segment(soma_seg_id)
    cell_origin = [soma_seg.proximal.x, soma_seg.proximal.y, soma_seg.proximal.z]

    translation_x = cell_origin[0] - dest[0]
    translation_y = cell_origin[1] - dest[1]
    translation_z = cell_origin[2] - dest[2]

    if translation_x == translation_y == translation_z == 0:
        return cell

    if not inplace:
        newcell = copy.deepcopy(cell)
    else:
        newcell = cell

    logger.info(
        f"Translating {newcell.id} by x:{-translation_x}, y:{-translation_y}, z:{-translation_z}"
    )

    # translate each segment
    for aseg in newcell.morphology.segments:
        prox = numpy.array([])
        # may not have a proximal
        try:
            prox = numpy.array([aseg.proximal.x, aseg.proximal.y, aseg.proximal.z])
        except AttributeError:
            pass

        if prox.any():
            aseg.proximal.x -= translation_x
            aseg.proximal.y -= translation_y
            aseg.proximal.z -= translation_z

        aseg.distal.x -= translation_x
        aseg.distal.y -= translation_y
        aseg.distal.z -= translation_z

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
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    tdir = rootdir + "/" + f"{prefix}_{timestamp}_{random_suffix}/"

    return tdir


def get_model_file_list(
    rootfile: str,
    filelist: typing.List[str],
    rootdir: str = ".",
    lems_def_dir: typing.Optional[str] = None,
) -> typing.Optional[str]:
    """Get the list of files to archive.

    This method will take the rootfile, and recursively resolve all the files
    it uses.

    :param rootfile: main NeuroML/LEMS/SED-ML file to resolve
    :type rootfile: str
    :param filelist: list of file paths to append to
    :type filelist: list of strings
    :param rootdir: directory holding the root file
    :type rootdir: str
    :param lems_def_dir: path to directory holding lems definition files
    :type lems_def_dir: str
    :returns: value of lems_def_dir so that the temporary directory can be
        cleaned up. strings are immuatable in Python so the variable cannot be
        modified in the function.
    :raises ValueError: if a file that does not have ".xml" or ".nml" as extension is encountered
    """
    logger.debug(f"Processing {rootfile}")

    fullrootdir = pathlib.Path(rootdir).absolute()

    # Only store path of file relative to the rootdir, if it's a descendent of
    # rootdir
    if rootfile.startswith(str(fullrootdir)):
        relrootfile = rootfile.replace(str(fullrootdir), "")
        if relrootfile.startswith("/"):
            relrootfile = relrootfile[1:]
    else:
        relrootfile = rootfile

    if relrootfile in filelist:
        logger.debug(f"Already processed {rootfile}. No op.")
        return lems_def_dir

    logger.debug(f"Appending: {relrootfile}")
    filelist.append(relrootfile)

    if rootfile.endswith(".nml"):
        if pathlib.Path(rootfile).is_absolute():
            rootdoc = read_neuroml2_file(rootfile)
        else:
            rootdoc = read_neuroml2_file(rootdir + "/" + rootfile)
        logger.debug(f"Has includes: {rootdoc.includes}")
        for inc in rootdoc.includes:
            lems_def_dir = get_model_file_list(
                inc.href, filelist, rootdir, lems_def_dir
            )

    elif rootfile.endswith(".xml"):
        # extract the standard NeuroML2 LEMS definitions into a directory
        # so that the LEMS parser can find them
        if lems_def_dir is None:
            lems_def_dir = extract_lems_definition_files()

        if pathlib.Path(rootfile).is_absolute():
            fullrootfilepath = rootfile
        else:
            fullrootfilepath = rootdir + "/" + rootfile

        model = Model(include_includes=True, fail_on_missing_includes=True)
        model.add_include_directory(lems_def_dir)
        model.import_from_file(fullrootfilepath)

        for inc in model.included_files:
            incfile = pathlib.Path(inc).name
            logger.debug(f"Processing include file {incfile} ({inc})")
            if incfile in STANDARD_LEMS_FILES:
                logger.debug(f"Ignoring NeuroML2 standard LEMS file: {inc}")
                continue
            lems_def_dir = get_model_file_list(inc, filelist, rootdir, lems_def_dir)

    elif rootfile.endswith(".sedml"):
        if pathlib.Path(rootfile).is_absolute():
            rootdoc = libsedml.readSedMLFromFile(rootfile)
        else:
            rootdoc = libsedml.readSedMLFromFile(rootdir + "/" + rootfile)

        # there should only be one model
        assert rootdoc.getNumModels() == 1
        model = rootdoc.getModel(0)
        lems_file = model.getSource()
        logger.debug(f"Got {lems_file} from SED-ML file {rootdoc}")
        lems_def_dir = get_model_file_list(lems_file, filelist, rootdir, lems_def_dir)

    else:
        raise ValueError(
            f"File must have a .xml/.nml/.sedml extension. We got: {rootfile}"
        )

    return lems_def_dir


def extract_lems_definition_files(
    path: typing.Union[str, None, tempfile.TemporaryDirectory] = None,
) -> str:
    """Extract the NeuroML2 LEMS definition files to a directory and return its path.

    This function can be used by other LEMS related functions that need to
    include the NeuroML2 LEMS definitions.

    If a path is provided, the folder is created relative to the current
    working directory.

    If no path is provided, for repeated usage for example, the files are
    extracted to a temporary directory using Python's
    `tempfile.mkdtemp
    <https://docs.python.org/3/library/tempfile.html>`__ function.

    Note: in both cases, it is the user's responsibility to remove the created
    directory when it is no longer required, for example using.  the
    `shutil.rmtree()` Python function.

    :param path: path of directory relative to current working directory to extract to, or None
    :type path: str or None
    :returns: directory path
    """
    jar_path = pyneuroml.utils.misc.get_path_to_jnml_jar()
    logger.debug(
        "Loading standard NeuroML2 dimension/unit definitions from %s" % jar_path
    )
    jar = zipfile.ZipFile(jar_path, "r")
    namelist = [x for x in jar.namelist() if ".xml" in x and "NeuroML2CoreTypes" in x]
    logger.debug("NeuroML LEMS definition files in jar are: {}".format(namelist))

    # If a string is provided, ensure that it is relative to cwd
    if path and isinstance(path, str) and len(path) > 0:
        path = "./" + path
        try:
            os.makedirs(path)
        except FileExistsError:
            logger.warning(
                "{} already exists. Any NeuroML LEMS files in it will be overwritten".format(
                    path
                )
            )
        except OSError as err:
            logger.critical(err)
            sys.exit(UNKNOWN_ERR)
    else:
        path = tempfile.mkdtemp()

    logger.debug("Created directory: " + path)
    jar.extractall(path, namelist)
    path = path + "/NeuroML2CoreTypes/"
    logger.info("NeuroML LEMS definition files extracted to: {}".format(path))
    return path
