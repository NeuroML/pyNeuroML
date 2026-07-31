#!/usr/bin/env python3
"""
Vispy interactive plotting.

Kept in a separate file so that the vispy dependency is not required elsewhere.

File: pyneuroml/plot/PlotMorphologyVispy.py

Copyright 2023 NeuroML contributors
"""

import logging
import math
import random
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, TypedDict, Union

import numpy
import progressbar
from frozendict import frozendict
from matplotlib.colors import to_rgb
from neuroml import (
    Cell,
    Morphology,
    NeuroMLDocument,
    Point3DWithDiam,
    Segment,
    SegmentGroup,
)
from neuroml.neuro_lex_ids import neuro_lex_ids
from neuroml.utils import fix_external_morphs_biophys_in_cell
from scipy.spatial.transform import Rotation

from pyneuroml.pynml import read_neuroml2_file
from pyneuroml.swc.ExportNML import convert_swc_to_neuroml
from pyneuroml.utils import extract_position_info, make_cell_upright
from pyneuroml.utils.plot import (
    DEFAULTS,
    get_cell_bound_box,
    get_next_hex_color,
    load_minimal_morphplottable__model,
)

# define special type for plot_spec dictionary
PlotSpec = TypedDict(
    "PlotSpec",
    {
        "point_fraction": float,
        "point_cells": List[str],
        "schematic_cells": List[str],
        "constant_cells": List[str],
        "detailed_cells": List[str],
    },
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

pynml_in_jupyter = False

try:
    from vispy import app, scene, use
    from vispy.color import get_color_dict, get_color_names
    from vispy.geometry.generation import create_sphere
    from vispy.geometry.meshdata import MeshData
    from vispy.io.mesh import write_mesh
    from vispy.scene.visuals import Mesh
    from vispy.scene.widgets.viewbox import ViewBox
    from vispy.util.transforms import rotate
    from vispy.visuals.filters import FacePickingFilter, ShadingFilter

    if app.Application.is_interactive(app):
        pynml_in_jupyter = True
        from IPython.display import display

except ImportError:
    logger.warning("Please install optional dependencies to use vispy features:")
    logger.warning("pip install pyneuroml[vispy]")
    logger.warning("or (for Qt5):")
    logger.warning("pip install pyneuroml[vispy-qt5]")

VISPY_THEME = {
    "light": {"bg": "white", "fg": "black"},
    "dark": {"bg": "black", "fg": "white"},
}
PYNEUROML_VISPY_THEME = "light"


def add_text_to_vispy_3D_plot(
    current_canvas: scene.SceneCanvas,
    xv: List[float],
    yv: List[float],
    zv: List[float],
    color: str,
    text: str,
):
    """Add text to a vispy plot between two points.

    Wrapper around vispy.scene.visuals.Text

    Rotates the text label to ensure it is at the same angle as the line.

    :param scene: vispy scene object
    :type scene: scene.SceneCanvas
    :param xv: start and end coordinates in one axis
    :type xv: list[x1, x2]
    :param yv: start and end coordinates in second axis
    :type yv: list[y1, y2]
    :param zv: start and end coordinates in third axix
    :type zv: list[z1, z2]
    :param color: color of text
    :type color: str
    :param text: text to write
    :type text: str
    """

    angle = int(numpy.rad2deg(numpy.arctan2((yv[1] - yv[0]), (xv[1] - xv[0]))))
    if angle > 90:
        angle -= 180
    elif angle < -90:
        angle += 180

    return scene.Text(
        pos=((xv[0] + xv[1]) / 2, (yv[0] + yv[1]) / 2, (zv[0] + zv[1]) / 2),
        text=text,
        color=color,
        rotation=angle,
        parent=current_canvas,
    )


def create_new_vispy_canvas(
    view_min: Optional[List[float]] = None,
    view_max: Optional[List[float]] = None,
    title: str = "",
    axes_pos: Optional[
        Union[Tuple[float, float, float], Tuple[int, int, int], str]
    ] = None,
    axes_length: float = 100,
    axes_width: int = 2,
    theme=PYNEUROML_VISPY_THEME,
    view_center: Optional[List[float]] = None,
) -> Tuple[scene.SceneCanvas, ViewBox]:
    """Create a new vispy scene canvas with a view and optional axes lines

    Reference: https://vispy.org/gallery/scene/axes_plot.html

    :param view_min: min view co-ordinates
    :type view_min: [float, float, float]
    :param view_max: max view co-ordinates
    :type view_max: [float, float, float]
    :param view_center: center view co-ordinates, calculated from view max/min if omitted
    :type view_center: [float, float, float]
    :param title: title of plot
    :type title: str
    :param axes_pos: add x, y, z axes centered at given position with colours red,
        green, blue for x, y, z axis respecitvely.

        A few special values are supported:

            - None: disable axes (default)
            - "origin": automatically added at origin
            - "bottom left": automatically added at bottom left

    :type axes_pos: (float, float, float) or (int, int, int) or None or str
    :param axes_length: length of axes
    :type axes_length: float
    :param axes_width: width of axes lines
    :type axes_width: float
    :returns: scene, view
    :raises ValueError: if incompatible value of `axes_pos` is passed
    """
    # vispy: full gl+ context is required for instanced rendering
    use(gl="gl+")

    canvas = scene.SceneCanvas(
        keys="interactive",
        show=False,
        bgcolor=VISPY_THEME[theme]["bg"],
        size=(800, 600),
        title="NeuroML viewer (VisPy)",
    )
    grid = canvas.central_widget.add_grid(margin=10)
    grid.spacing = 0

    title_widget = scene.Label(title, color=VISPY_THEME[theme]["fg"])
    title_widget.height_max = 80
    grid.add_widget(title_widget, row=0, col=0, col_span=1)
    view = grid.add_view(row=1, col=0, border_color=None)

    # create cameras
    # https://vispy.org/gallery/scene/flipped_axis.html
    cam1 = scene.cameras.PanZoomCamera(parent=view.scene, name="PanZoom", up="y")

    cam2 = scene.cameras.TurntableCamera(parent=view.scene, name="Turntable", up="y")

    cam3 = scene.cameras.ArcballCamera(parent=view.scene, name="Arcball", up="y")

    cam4 = scene.cameras.FlyCamera(parent=view.scene, name="Fly", up="y")
    # do not keep z up
    cam4.autoroll = False

    cams = [cam4, cam2]

    # Turntable is default
    cam_index = 1
    view.camera = cams[cam_index]

    calc_axes_pos: Optional[Union[Tuple[float, float, float], Tuple[int, int, int]]] = (
        None
    )

    if view_min is not None and view_max is not None:
        x_width = abs(view_min[0] - view_max[0])
        y_width = abs(view_min[1] - view_max[1])
        z_width = abs(view_min[2] - view_max[2])

        xrange = (
            (view_min[0] - x_width * 0.02, view_max[0] + x_width * 0.02)
            if x_width > 0
            else (-100, 100)
        )
        yrange = (
            (view_min[1] - y_width * 0.02, view_max[1] + y_width * 0.02)
            if y_width > 0
            else (-100, 100)
        )
        zrange = (
            (view_min[2] - z_width * 0.02, view_max[2] + z_width * 0.02)
            if z_width > 0
            else (-100, 100)
        )
        logger.debug(f"Ranges: {xrange}, {yrange}, {zrange}")
        logger.debug(f"Widths: {x_width}, {y_width}, {z_width}")

        for acam in cams:
            acam.set_range(x=xrange, y=yrange, z=zrange)

        # Calculate view center if it is None
        if view_center is None:
            view_center = (numpy.array(view_max) + numpy.array(view_min)) / 2
        logger.debug(f"Center is {view_center}")

        cam1.center = [view_center[0], view_center[1]]
        cam2.center = view_center
        cam3.center = view_center
        cam4.center = view_center

        # calculate origin of the axes
        if axes_pos is not None and isinstance(axes_pos, str):
            if axes_pos == "bottom left":
                try:
                    x_bit = view_min[0] - pow(10, int(math.log(x_width, 10) - 1))
                except ValueError:
                    x_bit = view_min[0]

                try:
                    z_bit = view_min[0] - pow(10, int(math.log(z_width, 10) - 1))
                except ValueError:
                    z_bit = view_min[0]

                calc_axes_pos = (x_bit, view_min[1], z_bit)
            elif axes_pos == "origin":
                calc_axes_pos = (0.0, 0.0, 0.0)
            else:
                raise ValueError(f"Invalid value for axes_pos: {axes_pos}")
        # if it's either None, or a point
        else:
            calc_axes_pos = axes_pos

    logger.debug(f"Axes origin is {calc_axes_pos}")

    for acam in cams:
        acam.set_default_state()

    if calc_axes_pos is not None:
        points = [
            calc_axes_pos,  # origin
            [calc_axes_pos[0] + axes_length, calc_axes_pos[1], calc_axes_pos[2]],
            [calc_axes_pos[0], calc_axes_pos[1] + axes_length, calc_axes_pos[2]],
            [calc_axes_pos[0], calc_axes_pos[1], calc_axes_pos[2] + axes_length],
        ]

        scene.Line(
            [points[0], points[1]],
            parent=view.scene,
            color="red",
            width=axes_width,
        )
        scene.Line(
            [points[0], points[2]],
            parent=view.scene,
            color="green",
            width=axes_width,
        )
        scene.Line(
            [points[0], points[3]],
            parent=view.scene,
            color="blue",
            width=axes_width,
        )

    def vispy_rotate(self):
        view.camera.orbit(azim=1, elev=0)

    rotation_timer = app.Timer(connect=vispy_rotate)

    @canvas.events.key_press.connect
    def vispy_on_key_press(event):
        nonlocal cam_index

        # Disable camera cycling. The fly camera looks sufficient.
        # Keeping views/ranges same when switching cameras is not simple.
        # Prev
        if event.text == "1":
            cam_index = (cam_index - 1) % len(cams)
            view.camera = cams[cam_index]
        # next
        elif event.text == "2":
            cam_index = (cam_index + 1) % len(cams)
            view.camera = cams[cam_index]
        # for turntable only: rotate animation
        elif event.text == "R" or event.text == "r":
            if view.camera == cam2:
                if rotation_timer.running:
                    rotation_timer.stop()
                else:
                    rotation_timer.start()
        # reset
        elif event.text == "0":
            view.camera.reset()
        # quit
        elif event.text == "9":
            canvas.app.quit()

    return canvas, view


def plot_interactive_3D(
    nml_file: Union[str, Cell, Morphology, NeuroMLDocument],
    min_width: float = DEFAULTS["minWidth"],
    verbose: bool = False,
    plot_type: str = "detailed",
    axes_pos: Optional[
        Union[Tuple[float, float, float], Tuple[int, int, int], str]
    ] = None,
    title: Optional[str] = None,
    theme: str = "light",
    nogui: bool = False,
    plot_spec: Optional[PlotSpec] = None,
    highlight_spec: Optional[Dict[Any, Any]] = None,
    upright: bool = False,
    save_mesh_to: Optional[str] = None,
):
    """Plot interactive plots in 3D using Vispy

    https://vispy.org

    Note that on Linux systems using Wayland, one may need to set the
    environment variable for PyOpenGL to work correctly:

    .. code-block:: bash

        QT_QPA_PLATFORM=wayland-egl

    .. versionadded:: 1.1.12
        The highlight_spec parameter

    If a file with a network containing multiple cells is provided, it will
    plot all the cells. For detailed neuroml.Cell types, it will plot their
    complete morphology. For point neurons, we only plot the points (locations)
    where they are as spheres. For single cell SWC files, it will first convert
    them to NeuroML and then plot them.

    :param nml_file: path to NeuroML cell file or single cell SWC file or
        :py:class:`neuroml.NeuroMLDocument` or :py:class:`neuroml.Cell`
        or :py:class:`neuroml.Morphology` object
    :type nml_file: str or neuroml.NeuroMLDocument or neuroml.Cell or
        neuroml.Morphology
    :param min_width: minimum width for segments (useful for visualising very
        thin segments): default 0.8um
    :type min_width: float
    :param verbose: show extra information (default: False)
    :type verbose: bool
    :param plot_type: type of plot, one of:

        - "detailed": show detailed morphology taking into account each segment's
          width
        - "constant": show morphology, but use "min_width" for line widths; the
          soma is made thicker to make it easy to see
        - "schematic": only plot each unbranched segment group as a straight
          line, not following each segment
        - "point": show all cells as points

        This is only applicable for neuroml.Cell cells (ones with some
        morphology)

    :type plot_type: str
    :param axes_pos: add x, y, z axes centered at given position with colours red,
        green, blue for x, y, z axis respecitvely.

        A few special values are supported:

            - None: disable axes (default)
            - "origin": automatically added at origin
            - "bottom left": automatically added at bottom left

    :type axes_pos: (float, float, float) or (int, int, int) or None or str
    :param title: title of plot
    :type title: str
    :param theme: theme to use (light/dark)
    :type theme: str
    :param nogui: toggle showing gui (for testing only)
    :type nogui: bool
    :param plot_spec: dictionary that allows passing some specifications that
        control how a plot is generated. This is mostly useful for large
        network plots where one may want to have a mix of full morphology and
        schematic, and point representations of cells. Possible keys are:

        - point_fraction: what fraction of each population to plot as point cells:
          these cells will be randomly selected
        - points_cells: list of cell ids to plot as point cells
        - schematic_cells: list of cell ids to plot as schematics
        - constant_cells: list of cell ids to plot as constant widths
        - detailed_cells: list of cell ids to plot in full detail

        The lists override the point_fraction setting. If a cell id is not
        included in the spec here, it will follow the plot_type provided
        before.
    :type plot_spec: dict
    :param highlight_spec: dictionary that allows passing some
        specifications to allow highlighting of particular elements.  Only used
        when plotting multi-compartmental cells for marking segments on them
        ("plot_type" is "detailed", since for "constant" `min_width` is always
        used.)

        Each key in the dictionary will be of the cell id and the values will
        be a "cell_color" or more dictionaries, with the segment id as key and
        the following keys in it:

        - marker_color: color of the marker (str)
        - marker_size: (diameter 1, diameter 2) (tuple) (in case of sphere, the
          first value is used)
        - marker_type: "sphere" (str) (otherwise the default shape of the
          segment is used, which could either be a sphere or a cylinder)

        E.g.:

        .. code-block:: python

            {
                "cell id1": {
                "cell_color": "red",                # string
                    "seg id1": {
                        "marker_color": "blue",     # string
                        "marker_size": (0.1, 0.1),  # tuple
                        "marker_type": "sphere"     # string
                    }
                }
            }


        The `cell_color` can be one of:

        - valid color options of :py:func:`plot_3D_cell_morphology` for a "detailed" plot_type
        - valid color options of :py:func:`plot_3D_schematic` for a "schematic" plot_type

        Please see the function docstrings for more information.

    :type highlight_spec: dict
    :param upright: bool only applicable for single cells: Makes cells "upright"
        (along Y axis) by calculating its PCA, rotating it so it is along the Y axis,
        and transforming cell co-ordinates to align along the rotated first principal
        component. If the rotation around the z axis needed is < 0, then the cell is
        rotated an additional 180 degrees. This is empirically found to rotate the cell
        "upwards" instead of "downwards" in most cases. Note that the original cell object
        is unchanged, this is for visualization purposes only.
    :type upright: bool
    :param save_mesh_to: name of file to save mesh object to
    :type save_mesh_to: str or None

    :throws ValueError: if `plot_type` is not one of "detailed", "constant",
        "schematic", or "point"
    :throws TypeError: if model is not a NeuroML file path, nor a neuroml.Cell, nor a neuroml.NeuroMLDocument
    :throws AttributeError: if `upright=True` for non single-cell models
    """
    if plot_type not in ["detailed", "constant", "schematic", "point"]:
        raise ValueError(
            "plot_type must be one of 'detailed', 'constant', 'schematic', 'point'"
        )

    if highlight_spec is None:
        highlight_spec = {}

    # convert axes_pos from list to tuple, it needs to be hashable for
    # functions that use caching
    if axes_pos:
        if isinstance(axes_pos, list):
            axes_pos = tuple(axes_pos)

    if plot_type != "detailed" and len(highlight_spec.items()) > 0:
        if plot_type == "constant":
            logger.warning(
                "Plot type is 'constant', `marker_size` in `highlight_spec` will be ignored and provided `min_width` used"
            )
        elif plot_type == "schematic" or plot_type == "point":
            logger.warning(
                f"Plot type is '{plot_type}', `highlight_spec` will be ignored"
            )
        logger.warning(
            "Please use `plot_type='detailed' if you also want to use `marker_size`"
        )

    if verbose:
        logger.info(f"Visualising {nml_file}")

    # if it's a file, load it first
    if isinstance(nml_file, str):
        # load without optimization for older HDF5 API
        # TODO: check if this is required: must for MultiscaleISN
        if nml_file.endswith(".h5"):
            nml_model = read_neuroml2_file(nml_file)
        elif nml_file.endswith(".swc"):
            nml_model_doc = convert_swc_to_neuroml(
                nml_file,
                neuroml_file=None,
                standalone_morphology=False,
                unbranched_segment_groups=False,
            )
            nml_model = nml_model_doc.cells[0]
        else:
            # do not fix external morphs here, we do it later below
            nml_model = read_neuroml2_file(
                nml_file,
                include_includes=False,
                check_validity_pre_include=False,
                verbose=False,
                optimized=True,
                fix_external_morphs_biophys=False,
            )
            # If it's a model that refers to external files for cells, and
            # other bits, only load ones that we need for visualization
            load_minimal_morphplottable__model(nml_model, nml_file)
            # Note that from this point, the model object is not necessarily valid,
            # because we've removed lots of bits that are not required for
            # visualization.

            # call manually so we can only load morphology, not biophysics
            fix_external_morphs_biophys_in_cell(
                nml_model, load_morphology=True, load_biophysical_properties=False
            )
    else:
        nml_model = nml_file

    # if it isn't a NeuroMLDocument, create one
    if isinstance(nml_model, Cell):
        logger.debug("Got a cell")
        if nml_model.morphology is None:
            if nml_model.morphology_attr is None:
                logger.error(
                    "Neither morphology nor a reference to an external morphology are included in the Cell. Cannot plot."
                )
                return
            else:
                logger.error(
                    "An external morphology is has been reference in the cell but I do not have the whole document to load it. Please pass the NeuroMLDocument or filename to the function instead."
                )
                return

        plottable_nml_model = NeuroMLDocument(id="newdoc")
        plottable_nml_model.add(nml_model)
        logger.debug(f"plottable cell model is: {plottable_nml_model.cells[0]}")
        if title is None:
            title = f"{plottable_nml_model.cells[0].id}"

    # if it's only a morphology, add it to an empty cell in a document
    elif isinstance(nml_model, Morphology):
        logger.debug("Received morph, adding to a dummy cell")
        plottable_nml_model = NeuroMLDocument(id="newdoc")
        plottable_nml_model.add(
            Cell, id=nml_model.id, morphology=nml_model, validate=False
        )
        logger.debug(f"plottable cell model is: {plottable_nml_model.cells[0]}")
        if title is None:
            title = f"{plottable_nml_model.cells[0].id}"

    # if it's a document, figure out if it's a cell or morphology
    elif isinstance(nml_model, NeuroMLDocument):
        logger.debug("Received document, checking for cells/morphologies")
        if len(nml_model.cells) > 0:
            logger.debug("Received document with cells")
            plottable_nml_model = fix_external_morphs_biophys_in_cell(
                nml_model,
                overwrite=False,
                load_morphology=True,
                load_biophysical_properties=False,
            )
        elif len(nml_model.morphology) > 0:
            logger.debug("Received document with morphologies, adding to dummy cells")
            plottable_nml_model = NeuroMLDocument(id="newdoc")
            for m in nml_model.morphology:
                plottable_nml_model.add(Cell, id=m.id, morphology=m, validate=False)
            logger.debug(f"plottable cell model is: {plottable_nml_model.cells[0]}")
            # use title from original model document
            title = nml_model.id
        # other networks
        else:
            plottable_nml_model = nml_model

        logger.debug(plottable_nml_model.info(show_contents=True))

    # what did we get?
    else:
        raise ValueError(f"Could not process argument: {nml_model}")

    if title is None:
        title = f"{plottable_nml_model.id}"

    (
        cell_id_vs_cell,
        pop_id_vs_cell,
        positions,
        pop_id_vs_color,
        pop_id_vs_radii,
    ) = extract_position_info(plottable_nml_model, verbose)

    logger.debug(f"positions: {positions}")
    logger.debug(f"pop_id_vs_cell: {pop_id_vs_cell}")
    logger.debug(f"cell_id_vs_cell: {cell_id_vs_cell}")
    logger.debug(f"pop_id_vs_color: {pop_id_vs_color}")
    logger.debug(f"pop_id_vs_radii: {pop_id_vs_radii}")

    # calculate total cells and segments to be plotted
    total_cells = 0
    for pop_id, cell in pop_id_vs_cell.items():
        total_cells += len(positions[pop_id])

    logger.info("Processing %s cells" % total_cells)

    # not used later, clear up
    del cell_id_vs_cell

    if len(positions) > 1:
        if upright:
            raise AttributeError("Argument upright can be True only for single cells")
        only_pos = []
        for posdict in positions.values():
            for poss in posdict.values():
                only_pos.append(poss)

        pos_array = numpy.array(only_pos)
        center = numpy.array(
            [
                numpy.mean(pos_array[:, 0]),
                numpy.mean(pos_array[:, 1]),
                numpy.mean(pos_array[:, 2]),
            ]
        )
        x_min = numpy.min(pos_array[:, 0])
        x_max = numpy.max(pos_array[:, 0])
        x_len = abs(x_max - x_min)

        y_min = numpy.min(pos_array[:, 1])
        y_max = numpy.max(pos_array[:, 1])
        y_len = abs(y_max - y_min)

        z_min = numpy.min(pos_array[:, 2])
        z_max = numpy.max(pos_array[:, 2])
        z_len = abs(z_max - z_min)

        view_min = center - numpy.array([x_len, y_len, z_len]) / 2
        view_max = center + numpy.array([x_len, y_len, z_len]) / 2
    else:
        cell = list(pop_id_vs_cell.values())[0]

        if cell is not None and isinstance(cell, Cell):
            view_min, view_max = get_cell_bound_box(cell)
        else:
            logger.debug("Got a point cell")
            pos = list((list(positions.values())[0]).values())[0]
            view_min = list(numpy.array(pos))
            view_max = list(numpy.array(pos))

    if upright:
        view_center = [0.0, 0.0, 0.0]
    else:
        view_center = None

    logger.debug(
        f"Before canvas creation: center, view_min, max are {view_center}, {view_min}, {view_max}"
    )

    current_canvas, current_view = create_new_vispy_canvas(
        view_min,
        view_max,
        title if title else "",
        axes_pos=axes_pos,
        theme=theme,
        view_center=view_center,
    )

    logger.debug(
        f"After canvas creation: center, view_min, max are {view_center}, {view_min}, {view_max}"
    )

    # process plot_spec
    point_cells: List[str] = []
    schematic_cells: List[str] = []
    constant_cells: List[str] = []
    detailed_cells: List[str] = []
    if plot_spec is not None:
        try:
            point_cells = plot_spec["point_cells"]
        except KeyError:
            pass
        try:
            schematic_cells = plot_spec["schematic_cells"]
        except KeyError:
            pass
        try:
            constant_cells = plot_spec["constant_cells"]
        except KeyError:
            pass
        try:
            detailed_cells = plot_spec["detailed_cells"]
        except KeyError:
            pass

    meshdata = []  # type: List[Any]

    # do not show this pbar in jupyter notebooks
    if not pynml_in_jupyter:
        pbar = progressbar.ProgressBar(
            max_value=total_cells,
            widgets=[
                progressbar.SimpleProgress(),
                progressbar.Bar(),
                progressbar.Timer(),
            ],
            redirect_stdout=True,
        )
    else:
        pbar = None

    pbar_ctr = 0
    while pop_id_vs_cell:
        if pbar is not None:
            pbar.update(pbar_ctr)
        pop_id, cell = pop_id_vs_cell.popitem()
        pos_pop = positions[pop_id]

        # reinit point_cells for each loop
        point_cells_pop = []
        if len(point_cells) == 0 and plot_spec is not None:
            cell_indices = list(pos_pop.keys())
            try:
                point_cells_pop = random.sample(
                    cell_indices,
                    int(len(cell_indices) * float(plot_spec["point_fraction"])),
                )
            except KeyError:
                pass

        while pos_pop:
            cell_index, pos = pos_pop.popitem()
            radius = pop_id_vs_radii[pop_id] if pop_id in pop_id_vs_radii else 10

            # use color if specified in property
            try:
                color = pop_id_vs_color[pop_id]
            except KeyError:
                # if single cell only, use default groups
                if total_cells == 1:
                    logger.debug("Only one detailed cell, using default color groups")
                    color = "default groups"
                # if multiple cells, use different colors for each cell
                else:
                    color = random.choice(get_color_names())

            # if hightlight spec has a color for the cell, use that
            try:
                color = highlight_spec[cell.id]["cell_color"]
            # no key for this cell
            except KeyError:
                pass
            # point cell
            except AttributeError:
                pass

            try:
                logging.debug(f"Plotting {cell.id}")
            except AttributeError:
                logging.debug(f"Plotting a point cell at {pos}")

            # a point cell component type
            if cell is None or not isinstance(cell, Cell):
                meshdata.append(
                    (
                        f"{radius:.1f}",
                        f"{radius:.1f}",
                        f"{radius:.1f}",
                        None,
                        None,
                        color,
                        pos,
                    )
                )
            else:
                if (
                    plot_type == "point"
                    or cell_index in point_cells_pop
                    or cell.id in point_cells
                ):
                    # assume that soma is 0, plot point at where soma should be
                    soma_x_y_z = cell.get_actual_proximal(0)
                    pos1 = [
                        pos[0] + soma_x_y_z.x,
                        pos[1] + soma_x_y_z.y,
                        pos[2] + soma_x_y_z.z,
                    ]
                    meshdata.append(
                        (
                            f"{radius:.1f}",
                            f"{radius:.1f}",
                            f"{radius:.1f}",
                            None,
                            None,
                            color,
                            pos1,
                        )
                    )
                    logger.debug(f"meshdata added: {meshdata[-1]}")

                elif plot_type == "schematic" or cell.id in schematic_cells:
                    logger.debug(f"Cell for 3d schematic is: {cell.id}")
                    # Pass no offset (pos) here to take advantage of the
                    # lru_cache.  The offset is not really used in anyway other
                    # than to create the meshdata. So we can add it to the
                    # mesdata after. This means that the plot_3D_cell_morphology
                    # function will not be run if the same cell object is
                    # passed to it, a common usecase for networks where there
                    # are populations of the same cell. Instead, the cache will
                    # be used.
                    new_meshdata = plot_3D_schematic(
                        offset=None,
                        cell=cell,
                        segment_groups=None,
                        color=color,
                        verbose=verbose,
                        current_canvas=current_canvas,
                        current_view=current_view,
                        axes_pos=axes_pos,
                        nogui=True,
                        meshdata=None,
                        upright=upright,
                        save_mesh_to=None,
                    )
                    assert new_meshdata is not None
                    mesh_data_with_offset = [(*x, pos) for x in new_meshdata]
                    meshdata.extend(mesh_data_with_offset)
                elif (
                    plot_type == "detailed"
                    or cell.id in detailed_cells
                    or plot_type == "constant"
                    or cell.id in constant_cells
                ):
                    logger.debug(f"Cell for 3d is: {cell.id}")
                    cell_highlight_spec = {}
                    try:
                        cell_highlight_spec = highlight_spec[cell.id]
                    except KeyError:
                        pass

                    # Pass no offset (pos) here to take advantage of the
                    # lru_cache.  The offset is not really used in anyway other
                    # than to create the meshdata. So we can add it to the
                    # mesdata after. This means that the plot_3D_cell_morphology
                    # function will not be run if the same cell object is
                    # passed to it, a common usecase for networks where there
                    # are populations of the same cell. Instead, the cache will
                    # be used.
                    new_meshdata = plot_3D_cell_morphology(
                        offset=None,
                        cell=cell,
                        color=color,
                        plot_type=plot_type,
                        verbose=verbose,
                        current_canvas=current_canvas,
                        current_view=current_view,
                        axes_pos=axes_pos,
                        min_width=min_width,
                        nogui=True,
                        meshdata=None,
                        highlight_spec=frozendict(cell_highlight_spec),
                        upright=upright,
                        save_mesh_to=None,
                    )
                    assert new_meshdata is not None
                    mesh_data_with_offset = [(*x, pos) for x in new_meshdata]
                    meshdata.extend(mesh_data_with_offset)

            pbar_ctr += 1

    if not nogui:
        if pbar is not None:
            pbar.finish()
        create_mesh(
            meshdata,
            current_view,
            save_mesh_to=save_mesh_to,
            current_canvas=current_canvas,
        )
        if pynml_in_jupyter:
            display(current_canvas)
        else:
            current_canvas.show()
            app.run()


@lru_cache(maxsize=100)
def plot_3D_cell_morphology(
    offset: Optional[Tuple[float, float, float]] = (0.0, 0.0, 0.0),
    cell: Optional[Cell] = None,
    color: Optional[str] = None,
    title: str = "",
    verbose: bool = False,
    current_canvas: Optional[scene.SceneCanvas] = None,
    current_view: Optional[scene.ViewBox] = None,
    min_width: float = DEFAULTS["minWidth"],
    axis_min_max: Tuple = (float("inf"), -1 * float("inf")),
    axes_pos: Optional[
        Union[Tuple[float, float, float], Tuple[int, int, int], str]
    ] = None,
    nogui: bool = False,
    plot_type: str = "detailed",
    theme: str = "light",
    meshdata: Optional[List[Any]] = None,
    highlight_spec: Optional[Union[Dict, frozendict]] = None,
    upright: bool = False,
    save_mesh_to: Optional[str] = None,
) -> Optional[List[Any]]:
    """Plot the detailed 3D morphology of a cell using vispy.
    https://vispy.org/

    .. versionadded:: 1.0.0

    .. versionadded:: 1.1.12
        The highlight_spec parameter

    .. seealso::

        :py:func:`plot_interactive_3D`
            general function for plotting

        :py:func:`plot_3D_schematic`
            for plotting only segmeng groups with their labels

    :param offset: offset for cell
        Note that this is only used in creating the meshdata. If set to None,
        this is ommitted from the meshdata, and the mesh creator will set it to
        origin.
    :type offset: (float, float, float) or None
    :param cell: cell to plot
    :type cell: neuroml.Cell
    :param color: color to use for segments, with some special values:

        - if a color string is given, use that
        - if None, each segment is given a new unique color
        - if "Groups", each unbranched segment group is given a unique color,
          and segments that do not belong to an unbranched segment group are in
          white
        - if "Default Groups", axonal segments are in red, dendritic in blue,
          somatic in green, and others in white

    :type color: str
    :param min_width: minimum width for segments (useful for visualising very
    :type min_width: float
    :param axis_min_max: min, max value of axes
    :type axis_min_max: [float, float]
    :param axes_pos: add x, y, z axes centered at given position with colours red,
        green, blue for x, y, z axis respecitvely.

        A few special values are supported:

            - None: disable axes (default)
            - "origin": automatically added at origin
            - "bottom left": automatically added at bottom left

    :type axes_pos: (float, float, float) or None or str
    :param title: title of plot
    :type title: str
    :param verbose: show extra information (default: False)
    :type verbose: bool
    :param nogui: do not show image immediately
    :type nogui: bool
    :param current_canvas: vispy scene.SceneCanvas to use (a new one is created if it is not
        provided)
    :type current_canvas: scene.SceneCanvas
    :param current_view: vispy viewbox to use
    :type current_view: ViewBox
    :param plot_type: type of plot, one of:

        - "detailed": show detailed morphology taking into account each segment's
          width.
        - "constant": show morphology, but use min_width for line widths; the
          soma is made 5 times thicker to make it easier to see.

        This is only applicable for neuroml.Cell cells (ones with some
        morphology)

    :type plot_type: str
    :param theme: theme to use (dark/light)
    :type theme: str
    :param meshdata: list used to store mesh related data for vispy
        visualisation
    :type meshdata: list
    :param highlight_spec: dictionary that allows passing some
        specifications to allow highlighting of particular elements. Mostly
        only helpful for marking segments on multi-compartmental cells. In the
        main dictionary are more dictionaries, one for each segment id which
        will be the key:

        - marker_color: color of the marker (str)
        - marker_size: (diameter 1, diameter 2) (tuple) (in case of sphere, the first value
          is used)
        - marker_type: "sphere" (str) (otherwise the default shape of the segment is
          used, which could either be a sphere or a cylinder)

    :type highlight_spec: dict
    :param upright: bool only applicable for single cells: Makes cells "upright"
        (along Y axis) by calculating its PCA, rotating it so it is along the Y axis,
        and transforming cell co-ordinates to align along the rotated first principal
        component. If the rotation around the z axis needed is < 0, then the cell is
        rotated an additional 180 degrees. This is empirically found to rotate the cell
        "upwards" instead of "downwards" in most cases. Note that the original cell object
        is unchanged, this is for visualization purposes only.
    :type upright: bool
    :param save_mesh_to: name of file to save mesh object to
    :type save_mesh_to: str or None
    :returns: meshdata
    :raises: ValueError if `cell` is None

    """
    if cell is None:
        raise ValueError(
            "No cell provided. If you would like to plot a network of point neurons, consider using `plot_2D_point_cells` instead"
        )

    if cell.morphology is None:
        logger.error("Cell does not contain a morphology. Cannot visualise.")
        logger.error(
            "If the cell is referencing an external morphology, please use the `plot_interactive_3D` function and pass the complete document and we will try to load the morphology."
        )
        return None

    if highlight_spec is None:
        highlight_spec = {}
    logging.debug("highlight_spec is " + str(highlight_spec))

    view_center = None
    if upright:
        cell = make_cell_upright(cell)
        current_canvas = current_view = None
        view_center = [0.0, 0.0, 0.0]
    try:
        soma_segs = cell.get_all_segments_in_group("soma_group")
    except Exception:
        soma_segs = []
    try:
        dend_segs = cell.get_all_segments_in_group("dendrite_group")
    except Exception:
        dend_segs = []
    try:
        axon_segs = cell.get_all_segments_in_group("axon_group")
    except Exception:
        axon_segs = []

    if current_canvas is None or current_view is None:
        view_min, view_max = get_cell_bound_box(cell)
        current_canvas, current_view = create_new_vispy_canvas(
            view_min,
            view_max,
            title,
            theme=theme,
            axes_pos=axes_pos,
            view_center=view_center,
        )

    if color == "Groups":
        color_dict = {}
        # if no segment groups are given, do them all
        segment_groups = []
        for sg in cell.morphology.segment_groups:
            if sg.neuro_lex_id == neuro_lex_ids["section"]:
                segment_groups.append(sg.id)

        ord_segs = cell.get_ordered_segments_in_groups(
            segment_groups, check_parentage=False
        )

        for sgs, segs in ord_segs.items():
            c = get_next_hex_color()
            for s in segs:
                color_dict[s.id] = c

    if meshdata is None:
        meshdata = []

    for seg in cell.morphology.segments:
        p = cell.get_actual_proximal(seg.id)
        d = seg.distal
        length = cell.get_segment_length(seg.id)

        r1 = p.diameter / 2
        r2 = d.diameter / 2

        # ensure larger than provided minimum width
        if r1 < min_width:
            r1 = min_width
        if r2 < min_width:
            r2 = min_width

        # if plot is a constant type, fix the widths
        if plot_type == "constant":
            r1 = min_width
            r2 = min_width
            # let soma be thicker so that it can be easily made out
            if seg.id in soma_segs:
                r1 = r1 * 5
                r2 = r2 * 5

        segment_spec = {
            "marker_size": None,
            "marker_color": None,
            "marker_type": None,
        }
        try:
            segment_spec.update(highlight_spec[str(seg.id)])
        # if there's no spec for this segment
        except KeyError:
            logger.debug("No segment highlight spec found for segment" + str(seg.id))
        # also test if segment id is given as int
        try:
            segment_spec.update(highlight_spec[seg.id])
        # if there's no spec for this segment
        except KeyError:
            logger.debug("No segment highlight spec found for segment" + str(seg.id))

        logger.debug("segment_spec for " + str(seg.id) + " is" + str(segment_spec))

        if segment_spec["marker_size"] is not None:
            if not isinstance(segment_spec["marker_size"], (tuple)):
                raise RuntimeError("The marker size must be a tuple")
            r1 = float(segment_spec["marker_size"][0]) / 2
            r2 = float(segment_spec["marker_size"][1]) / 2

        seg_color = "white"
        if color is None:
            seg_color = get_next_hex_color()
        elif isinstance(color, str) and color.lower() == "groups":
            try:
                seg_color = color_dict[seg.id]
            except KeyError:
                print(f"Unbranched segment found: {seg.id}")
                if seg.id in soma_segs:
                    seg_color = "green"
                elif seg.id in axon_segs:
                    seg_color = "red"
                elif seg.id in dend_segs:
                    seg_color = "blue"
        elif isinstance(color, str) and color.lower() == "default groups":
            if seg.id in soma_segs:
                seg_color = "green"
            elif seg.id in axon_segs:
                seg_color = "red"
            elif seg.id in dend_segs:
                seg_color = "blue"
        else:
            seg_color = color

        if segment_spec["marker_color"] is not None:
            seg_color = segment_spec["marker_color"]

        if offset is not None:
            meshdata.append(
                (f"{r1}", f"{r2}", f"{length}", p, d, seg_color, seg.id, cell, offset)
            )
        else:
            meshdata.append(
                (f"{r1}", f"{r2}", f"{length}", p, d, seg_color, seg.id, cell)
            )
        logger.debug(f"meshdata added: {meshdata[-1]}")

    if not nogui:
        create_mesh(
            meshdata,
            current_view,
            save_mesh_to=save_mesh_to,
            current_canvas=current_canvas,
        )
        if pynml_in_jupyter:
            display(current_canvas)
        else:
            current_canvas.show()
            app.run()
    return meshdata


@lru_cache(maxsize=100)
def plot_3D_schematic(
    cell: Cell,
    segment_groups: Optional[List[SegmentGroup]] = None,
    offset: Optional[Tuple[float, float, float]] = (0.0, 0.0, 0.0),
    labels: bool = False,
    width: float = 1.0,
    verbose: bool = False,
    nogui: bool = False,
    title: str = "",
    current_canvas: Optional[scene.SceneCanvas] = None,
    current_view: Optional[scene.ViewBox] = None,
    axes_pos: Optional[
        Union[Tuple[float, float, float], Tuple[int, int, int], str]
    ] = None,
    theme: str = "light",
    color: Optional[str] = "Cell",
    meshdata: Optional[List[Any]] = None,
    upright: bool = False,
    save_mesh_to: Optional[str] = None,
) -> Optional[List[Any]]:
    """Plot a 3D schematic of the provided segment groups using vispy.
    layer..

    This plots each segment group as a straight line between its first and last
    segment.

    .. versionadded:: 1.0.0

    .. seealso::

        :py:func:`plot_2D_schematic`
            general function for plotting

        :py:func:`plot_2D`
            general function for plotting

        :py:func:`plot_2D_point_cells`
            for plotting point cells

        :py:func:`plot_2D_cell_morphology`
            for plotting cells with detailed morphologies

    :param offset: offset for cell
        Note that this is only used in creating the meshdata. If set to None,
        this is ommitted from the meshdata, and the mesh creator will set it to
        origin.
    :type offset: (float, float, float) or None
    :param cell: cell to plot
    :type cell: neuroml.Cell
    :param segment_groups: list of unbranched segment groups to plot, all if None
    :type segment_groups: list(SegmentGroup)
    :param labels: toggle labelling of segment groups
    :type labels: bool
    :param width: width for lines for segment groups
    :type width: float
    :param verbose: show extra information (default: False)
    :type verbose: bool
    :param title: title of plot
    :type title: str
    :param nogui: toggle if plot should be shown or not
    :type nogui: bool
    :param current_canvas: vispy scene.SceneCanvas to use (a new one is created if it is not
        provided)
    :type current_canvas: scene.SceneCanvas
    :param current_view: vispy viewbox to use
    :type current_view: ViewBox
    :param axes_pos: add x, y, z axes centered at given position with colours red,
        green, blue for x, y, z axis respecitvely.

        A few special values are supported:

            - None: disable axes (default)
            - "origin": automatically added at origin
            - "bottom left": automatically added at bottom left

    :type axes_pos: (float, float, float) or (int, int, int) or None or str
    :param theme: theme to use (light/dark)
    :type theme: str
    :param color: color to use for segment groups with some special values:

        - if None, each unbranched segment group is given a unique color,
        - if "Cell", the whole cell is given one color
        - if "Default Groups", each cell is given unique colors for all axons,
          dendrites, and soma segments

    :type color: str
    :param meshdata: dictionary used to store mesh related data for vispy
        visualisation
    :type meshdata: dict
    :param upright: bool only applicable for single cells: Makes cells "upright"
        (along Y axis) by calculating its PCA, rotating it so it is along the Y axis,
        and transforming cell co-ordinates to align along the rotated first principal
        component. If the rotation around the z axis needed is < 0, then the cell is
        rotated an additional 180 degrees. This is empirically found to rotate the cell
        "upwards" instead of "downwards" in most cases. Note that the original cell object
        is unchanged, this is for visualization purposes only.
    :type upright: bool
    :param save_mesh_to: name of file to save mesh object to
    :type save_mesh_to: str or None
    :returns: meshdata
    """
    if title == "":
        title = f"3D schematic of segment groups from {cell.id}"

    if cell.morphology is None:
        logger.error("Cell does not contain a morphology. Cannot visualise.")
        logger.error(
            "If the cell is referencing an external morphology, please use the `plot_interactive_3D` function and pass the complete document and we will try to load the morphology."
        )
        return None

    view_center = None
    if upright:
        cell = make_cell_upright(cell)
        current_canvas = current_view = None
        view_center = [0.0, 0.0, 0.0]
    try:
        soma_segs = cell.get_all_segments_in_group("soma_group")
    except Exception:
        soma_segs = []
    try:
        dend_segs = cell.get_all_segments_in_group("dendrite_group")
    except Exception:
        dend_segs = []
    try:
        axon_segs = cell.get_all_segments_in_group("axon_group")
    except Exception:
        axon_segs = []

    # if no segment groups are given, do them all
    if segment_groups is None:
        segment_groups = []
        for sg in cell.morphology.segment_groups:
            if sg.neuro_lex_id == neuro_lex_ids["section"]:
                segment_groups.append(sg.id)

    ord_segs = cell.get_ordered_segments_in_groups(
        segment_groups, check_parentage=False
    )

    if current_canvas is None or current_view is None:
        view_min, view_max = get_cell_bound_box(cell)
        current_canvas, current_view = create_new_vispy_canvas(
            view_min,
            view_max,
            title,
            theme=theme,
            axes_pos=axes_pos,
            view_center=view_center,
        )

    # colors for cell
    cell_color_soma = get_next_hex_color()
    cell_color_axon = get_next_hex_color()
    cell_color_dendrites = get_next_hex_color()

    if meshdata is None:
        meshdata = []

    for sgid, segs in ord_segs.items():
        sgobj = cell.get_segment_group(sgid)
        if sgobj.neuro_lex_id != neuro_lex_ids["section"]:
            raise ValueError(
                f"{sgobj} does not have neuro_lex_id set to indicate it is an unbranched segment"
            )

        # get proximal and distal points
        first_seg: Segment = segs[0]
        last_seg: Segment = segs[-1]
        first_prox: Point3DWithDiam = cell.get_actual_proximal(first_seg.id)
        last_dist: Point3DWithDiam = last_seg.distal

        length = math.dist(
            (first_prox.x, first_prox.y, first_prox.z),
            (last_dist.x, last_dist.y, last_dist.z),
        )

        seg_width = width

        if first_seg.id in soma_segs and last_seg.id in soma_segs:
            seg_width = width * 5

        branch_color = color
        if color is None:
            branch_color = get_next_hex_color()
        elif isinstance(color, str) and color.lower() == "cell":
            branch_color = cell_color_soma
        elif isinstance(color, str) and color.lower() == "default groups":
            if first_seg.id in soma_segs:
                branch_color = cell_color_soma
            elif first_seg.id in axon_segs:
                branch_color = cell_color_axon
            elif first_seg.id in dend_segs:
                branch_color = cell_color_dendrites
            else:
                branch_color = get_next_hex_color()
        else:
            branch_color = color

        if offset is not None:
            meshdata.append(
                (
                    seg_width,
                    seg_width,
                    f"{length}",
                    first_prox,
                    last_dist,
                    branch_color,
                    offset,
                )
            )
        else:
            meshdata.append(
                (
                    seg_width,
                    seg_width,
                    f"{length}",
                    first_prox,
                    last_dist,
                    branch_color,
                )
            )

    if not nogui:
        create_mesh(
            meshdata,
            current_view,
            save_mesh_to=save_mesh_to,
            current_canvas=current_canvas,
        )
        if pynml_in_jupyter:
            display(current_canvas)
        else:
            current_canvas.show()
            app.run()
    return meshdata


@lru_cache(maxsize=10000)
def create_spherical_mesh(
    rows=10,
    cols=10,
    depth=10,
    radius=1.0,
    offset=True,
    subdivisions=3,
    method="latitude",
):
    """Wrapper around vispy.geometry.create_sphere to allow the use of a cache"""
    return create_sphere(
        rows=rows,
        cols=cols,
        depth=depth,
        radius=radius,
        offset=offset,
        subdivisions=subdivisions,
        method=method,
    )


@lru_cache(maxsize=100)
def compute_faces_of_cylindrical_mesh(rows: int, cols: int, closed: bool):
    """Compute faces for cylindrical meshes

    Since we tend to use a constant set of rows and cols, this function should
    be called repeatedly with the same values, and thus benefits from caching.

    :param rows: number of rows in mesh
    :type rows: int
    :param cols: number of cols in mesh
    :type cols: int
    :param closed: toggle whether mesh is closed or open
    :type closed: bool
    :returns: numpy array with faces (triplets of vertex indices)

    """
    faces = numpy.empty((rows * cols * 2, 3), dtype=numpy.uint32)
    rowtemplate1 = (
        (numpy.arange(cols).reshape(cols, 1) + numpy.array([[0, 1, 0]])) % cols
    ) + numpy.array([[0, 0, cols]])
    logger.debug(f"Template1 is: {rowtemplate1}")

    rowtemplate2 = (
        (numpy.arange(cols).reshape(cols, 1) + numpy.array([[0, 1, 1]])) % cols
    ) + numpy.array([[cols, 0, cols]])
    # logger.debug(f"Template2 is: {rowtemplate2}")

    for row in range(rows):
        start = row * cols * 2
        faces[start : start + cols] = rowtemplate1 + row * cols
        faces[start + cols : start + (cols * 2)] = rowtemplate2 + row * cols

    num_verts = (rows + 1) * cols
    # used below:
    # index of center of first cap = num_verts
    # index of center of second cap = num_verts + 1

    # add extra faces to cover the caps
    if closed is True:
        cap1 = numpy.arange(cols).reshape(cols, 1)
        cap1 = numpy.concatenate(
            (numpy.full((cols, 1), num_verts), cap1, numpy.roll(cap1, 1)), axis=1
        )
        logger.debug(f"cap1 is {cap1}")

        cap2 = numpy.arange(rows * cols, (rows + 1) * cols).reshape(cols, 1)
        cap2 = numpy.concatenate(
            (numpy.full((cols, 1), num_verts + 1), cap2, numpy.roll(cap2, 1)), axis=1
        )
        logger.debug(f"cap2 is {cap2}")

        faces = numpy.append(faces, cap1, axis=0)
        faces = numpy.append(faces, cap2, axis=0)

    logger.debug(f"Faces are: {faces}")
    return faces


@lru_cache(maxsize=10000)
def create_cylindrical_mesh(
    rows: int,
    cols: int,
    radius: Union[float, Tuple[float, float]] = (1.0, 1.0),
    length: float = 1.0,
    closed: bool = True,
):
    """Create a cylinderical mesh, adapted from vispy's generation method:
    https://github.com/vispy/vispy/blob/main/vispy/geometry/generation.py#L451

    :param rows: number of rows to use for mesh
    :type rows: int
    :param cols: number of columns
    :type cols: int
    :param radius: float or pair of floats for the two radii of the cylinder
    :type radius: float or (float, float)
    :param length: length of cylinder
    :type length: float
    :param closed: whether the cylinder should be closed
    :type closed: bool
    :returns: Vertices and faces computed for a cylindrical surface.
    :rtype: MeshData

    """
    verts = numpy.empty((rows + 1, cols, 3), dtype=numpy.float32)
    if isinstance(radius, int) or isinstance(radius, float):
        radius = (radius, radius)  # convert to tuple

    # compute theta values
    th = numpy.linspace(2 * numpy.pi, 0, cols).reshape(1, cols)
    logger.debug(f"Thetas are: {th}")

    # radius as a function of z
    r = numpy.linspace(radius[0], radius[1], num=rows + 1, endpoint=True).reshape(
        rows + 1, 1
    )

    verts[..., 0] = r * numpy.cos(th)  # x = r cos(th)
    verts[..., 1] = r * numpy.sin(th)  # y = r sin(th)
    verts[..., 2] = numpy.linspace(0, length, num=rows + 1, endpoint=True).reshape(
        rows + 1, 1
    )  # z
    # just reshape: no redundant vertices...
    verts = verts.reshape((rows + 1) * cols, 3)

    # add extra points for center of two circular planes that form the caps
    if closed is True:
        verts = numpy.append(verts, [[0.0, 0.0, 0.0], [0.0, 0.0, length]], axis=0)
    logger.debug(f"Verts are: {verts}")

    faces = compute_faces_of_cylindrical_mesh(rows, cols, closed)

    return MeshData(vertices=verts, faces=faces)


def create_mesh(
    meshdata: List[
        Tuple[
            float,
            float,
            float,
            Point3DWithDiam,
            Point3DWithDiam,
            Union[str, Tuple[float, float, float]],
            int,
            Cell,
            Optional[Tuple[float, float, float]],
        ]
    ],
    current_view: ViewBox,
    save_mesh_to: Optional[str],
    current_canvas: scene.SceneCanvas,
):
    """Internal function to create a mesh from the mesh data

    See: https://vispy.org/api/vispy.scene.visuals.html#vispy.scene.visuals.Mesh

    :param meshdata: meshdata to plot: list with:
        [(r1, r2, length, prox, dist, color, seg id, cell object offset)]
    :type meshdata: list of tuples
    :param current_view: vispy viewbox to use
    :type current_view: ViewBox
    :param save_mesh_to: name of file to save mesh object to
    :type save_mesh_to: str or None
    :param scene: vispy scene object
    :type scene: scene.SceneCanvas
    """
    mesh_start = time.time()
    total_mesh_instances = len(meshdata)
    logger.info(f"Processing {total_mesh_instances} segments")

    pbar_interval = max(1, pow(10, (len(str(total_mesh_instances)) - 3)))

    vispy_color_dict = get_color_dict()

    main_mesh_vertices = []
    num_vertices = 0
    main_mesh_faces = []
    main_mesh_colors = []
    # dictionary storing faces as keys and corresponding segment ids as values
    faces_to_segment = {}

    pbar = progressbar.ProgressBar(
        max_value=total_mesh_instances,
        widgets=[progressbar.SimpleProgress(), progressbar.Bar(), progressbar.Timer()],
        redirect_stdout=True,
    )
    progress_ctr = 0
    for d in meshdata:
        r1 = float(d[0])
        r2 = float(d[1])
        length = float(d[2])
        prox = d[3]
        dist = d[4]
        color = d[5]
        if len(d) >= 8:
            seg_id = d[6]
            cell = d[7]
            offset = d[8]
        else:
            seg_id = None
            cell = None
            offset = d[6]
        if offset is None:
            offset = (0.0, 0.0, 0.0)

        seg_mesh = None
        # 1: for points, we set the prox/dist to None since they only have
        # positions.
        # 2: single compartment cells with r1, r2, and length 0
        # Note: we can't check if r1 == r2 == length because there
        # may be cylinders with such a set of parameters

        if r1 == r2 and ((prox is None and dist is None) or (length == 0.0)):
            seg_mesh = create_spherical_mesh(9, 9, radius=r1)
            logger.debug(f"Created spherical mesh template with radius {r1}")
        else:
            rows = 2 + int(length / 2)
            seg_mesh = create_cylindrical_mesh(
                rows=rows, cols=9, radius=(r1, r2), length=length, closed=True
            )
            logger.debug(
                f"Created cylinderical mesh template with radii {r1}, {r2}, {length}"
            )

        logger.debug(f"Color is {color}")
        if isinstance(color, str):
            if color.startswith("#"):
                color = to_rgb(color)
            else:
                try:
                    vispy_color_hash = vispy_color_dict[color.lower()]
                    color = to_rgb(vispy_color_hash)
                except KeyError:
                    logger.warning(f"{color} is not recognised by vispy")
                    logger.warning(
                        "Valid colors can be seen using `vispy.color.get_color_names`, or you may use the hex notation"
                    )
                    # get a new random color, and add it to dict so it's used
                    # everywhere in the mesh
                    new_color = random.choice(list(vispy_color_dict.keys()))
                    vispy_color_dict[color] = vispy_color_dict[new_color]
                    logger.warning(f"Using {new_color} instead")
                    color = to_rgb(vispy_color_dict[color])

        # cylinders
        if prox is not None and dist is not None:
            orig_vec = [0, 0, length]
            dir_vector = [dist.x - prox.x, dist.y - prox.y, dist.z - prox.z]
            k = numpy.cross(orig_vec, dir_vector)
            mag_k = numpy.linalg.norm(k)

            vertices = seg_mesh.get_vertices()

            if mag_k != 0.0:
                k = k / mag_k
                theta = math.acos(
                    numpy.dot(orig_vec, dir_vector)
                    / (numpy.linalg.norm(orig_vec) * numpy.linalg.norm(dir_vector))
                )
                logger.debug(f"k is {k}, theta is {theta}")
                rot_matrix = rotate(math.degrees(theta), k).T
                rot_obj = Rotation.from_matrix(rot_matrix[:3, :3])
                rotated_vertices = rot_obj.apply(vertices)
            else:
                logger.debug("k is [0..], skipping rotation")
                rotated_vertices = vertices

            translator = numpy.array(
                [offset[0] + prox.x, offset[1] + prox.y, offset[2] + prox.z]
            )
            translated_vertices = rotated_vertices + translator
            main_mesh_faces.append(seg_mesh.get_faces() + num_vertices)
            # Faces to segments
            if seg_id is not None:
                for face in seg_mesh.get_faces() + num_vertices:
                    faces_to_segment[tuple(face)] = seg_id

            main_mesh_vertices.append(translated_vertices)
            main_mesh_colors.append([[*color, 1]] * len(vertices))

            num_vertices += len(vertices)
        else:
            # only translation here
            translator = numpy.array([offset[0], offset[1], offset[2]])
            vertices = seg_mesh.get_vertices()
            translated_vertices = vertices + translator

            main_mesh_faces.append(seg_mesh.get_faces() + num_vertices)
            # Faces to segments
            if seg_id is not None:
                for face in seg_mesh.get_faces() + num_vertices:
                    faces_to_segment[tuple(face)] = seg_id

            main_mesh_vertices.append(translated_vertices)
            main_mesh_colors.append([[*color, 1]] * len(vertices))

            num_vertices += len(translated_vertices)

        if (progress_ctr % pbar_interval) == 0:
            pbar.update(progress_ctr)
        progress_ctr += 1

    numpy_mesh_vertices = numpy.concatenate(main_mesh_vertices, axis=0)
    numpy_mesh_faces = numpy.concatenate(main_mesh_faces, axis=0)
    numpy_mesh_colors = numpy.concatenate(main_mesh_colors, axis=0)
    face_colors = numpy.tile((0.5, 0.0, 0.5, 1.0), (len(numpy_mesh_faces), 1))

    logger.debug(f"Vertices: {numpy_mesh_vertices.shape}")
    logger.debug(f"Faces: {numpy_mesh_faces.shape}")

    mesh = Mesh(
        vertices=numpy_mesh_vertices,
        faces=numpy_mesh_faces,
        parent=current_view.scene,
        vertex_colors=numpy_mesh_colors,
        face_colors=face_colors.copy(),
    )
    mesh.interactive = True

    assert mesh is not None
    pbar.finish()
    mesh_end = time.time()
    logger.debug(f"Mesh creation took {(mesh_end - mesh_start)}")

    # lighting
    # light dir from the front right and above
    # for vispy, y is up, z is to the right, and x is inwards
    # so, go diagonally from bounds to get the light vector, not quite
    # diagonally
    cam = current_view.camera
    cam_center = cam.center
    logger.debug(f"Cam center is {cam_center}")
    logger.debug(f"Cam lims are {cam._xlim}, {cam._ylim}, {cam._zlim}")
    light_dir = (
        cam._xlim[1] - cam._xlim[0] / 2,
        -1 * (cam._ylim[1] - cam._ylim[0] / 2),
        -1 * (cam._zlim[1] - cam._zlim[0] / 2),
        0,
    )
    logger.debug(f"Light dir is: {light_dir}")
    shading_filter = ShadingFilter(
        shading="flat",
        shininess=10,
        ambient_light=(1, 1, 1, 0.5),
        specular_light=(1, 1, 1, 0.5),
        light_dir=light_dir[:3],
    )
    face_picking_filter = FacePickingFilter()
    mesh.attach(shading_filter)
    mesh.attach(face_picking_filter)

    def attach_headlight(current_view):
        shading_filter.light_dir = light_dir[:3]
        initial_light_dir = current_view.camera.transform.imap(light_dir)

        @current_view.scene.transform.changed.connect
        def on_transform_change(event):
            transform = current_view.camera.transform
            shading_filter.light_dir = transform.map(initial_light_dir)[:3]

    # For handling mouse press
    # currently identifies the segment and prints some information out to the
    # terminal about it.
    @current_canvas.events.mouse_press.connect
    def on_mouse_press(event):
        clicked_mesh = current_canvas.visual_at(event.pos)
        if isinstance(clicked_mesh, Mesh) and seg_id is not None:
            # adjust the event position for hidpi screens
            render_size = tuple(
                d * current_canvas.pixel_scale for d in current_canvas.size
            )
            x_pos = event.pos[0] * current_canvas.pixel_scale
            y_pos = render_size[1] - (event.pos[1] * current_canvas.pixel_scale)

            # render a small patch around the mouse cursor
            restore_state = not face_picking_filter.enabled
            face_picking_filter.enabled = True
            mesh.update_gl_state(blend=False)
            picking_render = current_canvas.render(
                region=(x_pos - 1, y_pos - 1, 3, 3),
                size=(3, 3),
                bgcolor=(0, 0, 0, 0),
                alpha=True,
            )
            if restore_state:
                face_picking_filter.enabled = False
            mesh.update_gl_state(blend=not face_picking_filter.enabled)

            # unpack the face index from the color in the center pixel
            face_idx = (picking_render.view(numpy.uint32) - 1)[1, 1, 0]
            picked_face = tuple(mesh._meshdata._faces[face_idx])
            picked_seg_id = faces_to_segment[picked_face]

            logger.debug(f"face id is: {face_idx}")
            logger.debug(f"face is: {picked_face}")
            logger.debug(f"corresponding segment is: {picked_seg_id}")

            clicked_on_seg(picked_seg_id, cell)

    attach_headlight(current_view)

    if save_mesh_to is not None:
        if not save_mesh_to.endswith((".obj", ".gz")):
            logger.info(
                f"Vispy requires mesh file to end in '.obj' or '.gz', appending '.obj' to {save_mesh_to}"
            )
            save_mesh_to += ".obj"

        logger.info(f"Saving mesh to {save_mesh_to}")
        write_mesh(
            fname=save_mesh_to,
            vertices=mesh.mesh_data.get_vertices(),
            faces=mesh.mesh_data.get_faces(),
            normals=None,
            texcoords=None,
            overwrite=False,
        )


def clicked_on_seg(seg_id: int, cell: Cell):
    """
    Callback function called when a segment is clicked on.

    Prints information about the segment.

    Based on Vispy examples:
    https://vispy.org/gallery/scene/face_picking.html#sphx-glr-gallery-scene-face-picking-py

    :param seg_id: id of segment
    :type seg_id: int
    :param cell: cell object that segment belongs to
    :type cell: Cell
    """
    print(f"Clicked on: Cell: {cell.id}; segment: {seg_id}.")
    print(f"Segment info: {cell.get_segment_location_info(seg_id)}")
