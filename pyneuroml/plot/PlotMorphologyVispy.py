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
import typing
from typing import Optional

import numpy
import progressbar
from neuroml import Cell, NeuroMLDocument, SegmentGroup
from neuroml.neuro_lex_ids import neuro_lex_ids
from scipy.spatial.transform import Rotation

from pyneuroml.pynml import read_neuroml2_file
from pyneuroml.utils import extract_position_info
from pyneuroml.utils.plot import (
    DEFAULTS,
    get_cell_bound_box,
    get_next_hex_color,
    load_minimal_morphplottable__model,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    from vispy import app, scene, use
    from vispy.geometry.generation import create_sphere
    from vispy.geometry.meshdata import MeshData
    from vispy.scene.visuals import InstancedMesh
    from vispy.util.transforms import rotate
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

MAX_MESH_PRECISION = 3


def add_text_to_vispy_3D_plot(
    current_canvas: scene.SceneCanvas,
    xv: typing.List[float],
    yv: typing.List[float],
    zv: typing.List[float],
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
    view_min: typing.Optional[typing.List[float]] = None,
    view_max: typing.Optional[typing.List[float]] = None,
    title: str = "",
    axes_pos: typing.Optional[typing.List] = None,
    axes_length: float = 100,
    axes_width: int = 2,
    theme=PYNEUROML_VISPY_THEME,
):
    """Create a new vispy scene canvas with a view and optional axes lines

    Reference: https://vispy.org/gallery/scene/axes_plot.html

    :param view_min: min view co-ordinates
    :type view_min: [float, float, float]
    :param view_max: max view co-ordinates
    :type view_max: [float, float, float]
    :param title: title of plot
    :type title: str
    :param axes_pos: position to draw axes at
    :type axes_pos: [float, float, float]
    :param axes_length: length of axes
    :type axes_length: float
    :param axes_width: width of axes lines
    :type axes_width: float
    :returns: scene, view
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
    cam1 = scene.cameras.PanZoomCamera(parent=view.scene, name="PanZoom")

    cam2 = scene.cameras.TurntableCamera(parent=view.scene, name="Turntable")

    cam3 = scene.cameras.ArcballCamera(parent=view.scene, name="Arcball")

    cam4 = scene.cameras.FlyCamera(parent=view.scene, name="Fly")
    # do not keep z up
    cam4.autoroll = False

    cams = [cam4, cam2]

    # Turntable is default
    cam_index = 1
    view.camera = cams[cam_index]

    if view_min is not None and view_max is not None:
        view_center = (numpy.array(view_max) + numpy.array(view_min)) / 2
        logger.debug(f"Center is {view_center}")
        cam1.center = [view_center[0], view_center[1]]
        cam2.center = view_center
        cam3.center = view_center
        cam4.center = view_center

        for acam in cams:
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
            logger.debug(f"{xrange}, {yrange}, {zrange}")

            acam.set_range(x=xrange, y=yrange, z=zrange)

    for acam in cams:
        acam.set_default_state()

    if axes_pos is not None:
        # can't get XYZAxis to work, so create manually
        points = [
            axes_pos,  # origin
            [axes_pos[0] + axes_length, axes_pos[1], axes_pos[2]],
            [axes_pos[0], axes_pos[1] + axes_length, axes_pos[2]],
            [axes_pos[0], axes_pos[1], axes_pos[2] + axes_length],
        ]
        scene.Line(
            points,
            connect=numpy.array([[0, 1], [0, 2], [0, 3]]),
            parent=view.scene,
            color=VISPY_THEME[theme]["fg"],
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
    nml_file: typing.Union[str, Cell, NeuroMLDocument],
    min_width: float = DEFAULTS["minWidth"],
    verbose: bool = False,
    plot_type: str = "constant",
    title: typing.Optional[str] = None,
    theme: str = "light",
    nogui: bool = False,
    plot_spec: typing.Optional[
        typing.Dict[str, typing.Union[str, typing.List[int], float]]
    ] = None,
    highlight_spec: typing.Optional[typing.Dict[typing.Any, typing.Any]] = None,
    precision: typing.Tuple[int, int] = (4, 200),
):
    """Plot interactive plots in 3D using Vispy

    https://vispy.org

    Note that on Linux systems using Wayland, one may need to set the
    environment variable for PyOpenGL to work correctly:

    .. code-block:: bash

        QT_QPA_PLATFORM=wayland-egl

    .. versionadded:: 1.1.12
        The hightlight_spec parameter


    :param nml_file: path to NeuroML cell file or
        :py:class:`neuroml.NeuroMLDocument` or :py:class:`neuroml.Cell` object
    :type nml_file: str or neuroml.NeuroMLDocument or neuroml.Cell
    :param min_width: minimum width for segments (useful for visualising very
        thin segments): default 0.8um
    :type min_width: float
    :param verbose: show extra information (default: False)
    :type verbose: bool
    :param plot_type: type of plot, one of:

        - "detailed": show detailed morphology taking into account each segment's
          width
        - "constant": show morphology, but use constant line widths
        - "schematic": only plot each unbranched segment group as a straight
          line, not following each segment
        - "point": show all cells as points

        This is only applicable for neuroml.Cell cells (ones with some
        morphology)

    :type plot_type: str
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

        The last three lists override the point_fraction setting. If a cell id
        is not included in the spec here, it will follow the plot_type provided
        before.
    :type plot_spec: dict
    :param highlight_spec: dictionary that allows passing some
        specifications to allow highlighting of particular elements.  Only used
        when plotting multi-compartmental cells for marking segments on them
        ("plot_type" is either "constant" or "detailed")

        Each key in the dictionary will be of the cell id and the values will
        be more dictionaries, with the segment id as key and the following keys
        in it:

        - marker_color: color of the marker
        - marker_size: [diameter 1, diameter 2] (in case of sphere, the first value
          is used)

        E.g.:

        .. code-block:: python

            {
                "cell id1": {
                    "seg id1": {
                        "marker_color": "blue",
                        "marker_size": [0.1, 0.1]
                    }
                }
            }

    :type highlight_spec: dict
    :param precision: tuple containing two values: (number of decimal places,
        maximum number of meshes). The first is used to group segments into
        meshes to create instances. More precision means fewer segments will be
        grouped into meshes---this may increase detail, but will reduce
        performance. The second argument is used to limit the total number of
        meshes. The function will keep reducing precision until the number of
        meshes is fewer than the value provided here.

        If you have a good GPU, you can increase both these values to get more
        detailed visualizations
    :type precision: (int, int)
    """
    if plot_type not in ["detailed", "constant", "schematic", "point"]:
        raise ValueError(
            "plot_type must be one of 'detailed', 'constant', 'schematic', 'point'"
        )

    if highlight_spec is None:
        highlight_spec = {}

    if verbose:
        logger.info(f"Visualising {nml_file}")

    if isinstance(nml_file, str):
        # load without optimization for older HDF5 API
        # TODO: check if this is required: must for MultiscaleISN
        if nml_file.endswith(".h5"):
            nml_model = read_neuroml2_file(nml_file)
        else:
            nml_model = read_neuroml2_file(
                nml_file,
                include_includes=False,
                check_validity_pre_include=False,
                verbose=False,
                optimized=True,
            )
            load_minimal_morphplottable__model(nml_model, nml_file)

        if title is None:
            try:
                title = f"{nml_model.networks[0].id} from {nml_file}"
            except IndexError:
                title = f"{nml_model.cells[0].id} from {nml_file}"

    elif isinstance(nml_file, Cell):
        nml_model = NeuroMLDocument(id="newdoc")
        nml_model.add(nml_file)
        if title is None:
            title = f"{nml_model.cells[0].id}"

    elif isinstance(nml_file, NeuroMLDocument):
        nml_model = nml_file
        if title is None:
            try:
                title = f"{nml_model.networks[0].id} from {nml_file.id}"
            except IndexError:
                title = f"{nml_model.cells[0].id} from {nml_file.id}"
    else:
        raise TypeError(
            "Passed model is not a NeuroML file path, nor a neuroml.Cell, nor a neuroml.NeuroMLDocument"
        )

    (
        cell_id_vs_cell,
        pop_id_vs_cell,
        positions,
        pop_id_vs_color,
        pop_id_vs_radii,
    ) = extract_position_info(nml_model, verbose)

    logger.debug(f"positions: {positions}")
    logger.debug(f"pop_id_vs_cell: {pop_id_vs_cell}")
    logger.debug(f"cell_id_vs_cell: {cell_id_vs_cell}")
    logger.debug(f"pop_id_vs_color: {pop_id_vs_color}")
    logger.debug(f"pop_id_vs_radii: {pop_id_vs_radii}")

    # calculate total cells and segments to be plotted
    total_cells = 0
    total_segments = 0
    for pop_id, cell in pop_id_vs_cell.items():
        total_cells += len(positions[pop_id])
        try:
            total_segments += len(positions[pop_id]) * len(cell.morphology.segments)
        except AttributeError:
            total_segments += len(positions[pop_id])

    logger.info(
        f"Visualising {total_segments} segments in {total_cells} cells in {len(pop_id_vs_cell)} populations"
    )
    logger.info(
        f"Grouping into mesh instances by diameters at {precision[0]} decimal places"
    )
    # not used later, clear up
    del cell_id_vs_cell

    if len(positions) > 1:
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

        view_min = center - numpy.array([x_len, y_len, z_len])
        view_max = center + numpy.array([x_len, y_len, z_len])
        logger.debug(f"center, view_min, max are {center}, {view_min}, {view_max}")

    else:
        cell = list(pop_id_vs_cell.values())[0]
        if cell is not None:
            view_min, view_max = get_cell_bound_box(cell)
        else:
            logger.debug("Got a point cell")
            pos = list((list(positions.values())[0]).values())[0]
            view_min = list(numpy.array(pos))
            view_max = list(numpy.array(pos))

    current_canvas, current_view = create_new_vispy_canvas(
        view_min, view_max, title, theme=theme
    )

    logger.debug(f"figure extents are: {view_min}, {view_max}")

    # process plot_spec
    point_cells = []
    schematic_cells = []
    constant_cells = []
    detailed_cells = []
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

    meshdata = {}  # type: typing.Dict[typing.Any, typing.Any]
    logger.info("Processing cells")
    pbar = progressbar.ProgressBar(
        max_value=total_cells,
        widgets=[progressbar.SimpleProgress(), progressbar.Bar(), progressbar.Timer()],
        redirect_stdout=True,
    )
    pbar_ctr = 0
    while pop_id_vs_cell:
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
            color = (
                pop_id_vs_color[pop_id]
                if pop_id in pop_id_vs_color
                else get_next_hex_color()
            )

            try:
                logging.debug(f"Plotting {cell.id}")
            except AttributeError:
                logging.debug(f"Plotting a point cell at {pos}")

            if cell is None:
                key = (f"{radius:.1f}", f"{radius:.1f}", f"{radius:.1f}")
                try:
                    meshdata[key].append((None, None, color, pos))
                except KeyError:
                    meshdata[key] = [(None, None, color, pos)]
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
                    key = (f"{radius:.1f}", f"{radius:.1f}", f"{radius:.1f}")
                    try:
                        meshdata[key].append((None, None, color, pos1))
                    except KeyError:
                        meshdata[key] = [(None, None, color, pos1)]
                    logger.debug(f"meshdata added: {key}: {meshdata[key]}")

                elif plot_type == "schematic" or cell.id in schematic_cells:
                    logger.debug(f"Cell for 3d schematic is: {cell.id}")
                    plot_3D_schematic(
                        offset=pos,
                        cell=cell,
                        segment_groups=None,
                        color=color,
                        verbose=verbose,
                        current_canvas=current_canvas,
                        current_view=current_view,
                        nogui=True,
                        meshdata=meshdata,
                        mesh_precision=precision[0],
                    )
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

                    plot_3D_cell_morphology(
                        offset=pos,
                        cell=cell,
                        color=color,
                        plot_type=plot_type,
                        verbose=verbose,
                        current_canvas=current_canvas,
                        current_view=current_view,
                        min_width=min_width,
                        nogui=True,
                        meshdata=meshdata,
                        mesh_precision=precision[0],
                        highlight_spec=cell_highlight_spec,
                    )

            # if too many meshes, reduce precision and retry, recursively
            if (len(meshdata.keys()) > precision[1]) and (precision[0] > 0):
                precision = (precision[0] - 1, precision[1])
                pbar.finish(dirty=True)
                logger.info(
                    f"More meshes than threshold ({len(meshdata.keys())}/{precision[1]}), reducing precision to {precision[0]} and re-calculating."
                )
                plot_interactive_3D(
                    nml_file=nml_model,
                    min_width=min_width,
                    verbose=verbose,
                    plot_type=plot_type,
                    title=title,
                    theme=theme,
                    nogui=nogui,
                    plot_spec=plot_spec,
                    precision=precision,
                    highlight_spec=highlight_spec,
                )
                # break the recursion, don't plot in the calling method
                return

            pbar_ctr += 1

    if not nogui:
        pbar.finish()
        create_instanced_meshes(meshdata, plot_type, current_view, min_width)
        current_canvas.show()
        app.run()


def plot_3D_cell_morphology(
    offset: typing.List[float] = [0, 0, 0],
    cell: Optional[Cell] = None,
    color: typing.Optional[str] = None,
    title: str = "",
    verbose: bool = False,
    current_canvas: Optional[scene.SceneCanvas] = None,
    current_view: Optional[scene.ViewBox] = None,
    min_width: float = DEFAULTS["minWidth"],
    axis_min_max: typing.List = [float("inf"), -1 * float("inf")],
    nogui: bool = True,
    plot_type: str = "constant",
    theme: str = "light",
    meshdata: typing.Optional[typing.Dict[typing.Any, typing.Any]] = None,
    mesh_precision: int = 2,
    highlight_spec: typing.Optional[typing.Dict[typing.Any, typing.Any]] = None,
):
    """Plot the detailed 3D morphology of a cell using vispy.
    https://vispy.org/

    .. versionadded:: 1.0.0

    .. versionadded:: 1.1.12
        The hightlight_spec parameter

    .. seealso::

        :py:func:`plot_2D`
            general function for plotting

        :py:func:`plot_2D_schematic`
            for plotting only segmeng groups with their labels

        :py:func:`plot_2D_point_cells`
            for plotting point cells

    :param offset: offset for cell
    :type offset: [float, float]
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
          width. This is not performant, because a new line is required for
          each segment. To only be used for cells with small numbers of
          segments
        - "constant": show morphology, but use constant line widths

        This is only applicable for neuroml.Cell cells (ones with some
        morphology)

    :type plot_type: str
    :param theme: theme to use (dark/light)
    :type theme: str
    :param meshdata: dictionary used to store mesh related data for vispy
        visualisation
    :type meshdata: dict
    :param mesh_precision: what decimal places to use to group meshes into
        instances: more precision means more detail (meshes), means less
        performance
    :type mesh_precision: int
    :param highlight_spec: dictionary that allows passing some
        specifications to allow highlighting of particular elements. Mostly
        only helpful for marking segments on multi-compartmental cells. In the
        main dictionary are more dictionaries, one for each segment id which
        will be the key:

        - marker_color: color of the marker
        - marker_size: [diameter 1, diameter 2] (in case of sphere, the first value
          is used)

    :type highlight_spec: dict
    :raises: ValueError if `cell` is None

    """
    if cell is None:
        raise ValueError(
            "No cell provided. If you would like to plot a network of point neurons, consider using `plot_2D_point_cells` instead"
        )

    if highlight_spec is None:
        highlight_spec = {}
    logging.debug("highlight_spec is " + str(highlight_spec))

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
            view_min, view_max, title, theme=theme
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
        meshdata = {}

    for seg in cell.morphology.segments:
        p = cell.get_actual_proximal(seg.id)
        d = seg.distal
        length = cell.get_segment_length(seg.id)

        # round up to precision
        r1 = round(p.diameter / 2, mesh_precision)
        r2 = round(d.diameter / 2, mesh_precision)

        segment_spec = {
            "marker_size": None,
            "marker_color": None,
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
            if not isinstance(segment_spec["marker_size"], list):
                raise RuntimeError("The marker size must be a list")
            r1 = round(float(segment_spec["marker_size"][0]) / 2, mesh_precision)
            r2 = round(float(segment_spec["marker_size"][1]) / 2, mesh_precision)

        key = (
            f"{r1:.{mesh_precision}f}",
            f"{r2:.{mesh_precision}f}",
            f"{round(length, mesh_precision):.{mesh_precision}f}",
        )

        seg_color = "white"
        if color is None:
            seg_color = get_next_hex_color()
        elif color == "Groups":
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
        elif color == "Default Groups":
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

        try:
            meshdata[key].append((p, d, seg_color, offset))
        except KeyError:
            meshdata[key] = [(p, d, seg_color, offset)]
        logger.debug(f"meshdata added: {key}: {(p, d, seg_color, offset)}")

    if not nogui:
        create_instanced_meshes(meshdata, plot_type, current_view, min_width)
        current_canvas.show()
        app.run()
    return meshdata


def create_instanced_meshes(meshdata, plot_type, current_view, min_width):
    """Internal function to plot instanced meshes from mesh data.

    It is more efficient to collect all the segments that require the same
    cylindrical mesh and to create instanced meshes for them.

    See: https://vispy.org/api/vispy.scene.visuals.html#vispy.scene.visuals.InstancedMesh

    :param meshdata: meshdata to plot: dictionary with:
        key: (r1, r2, length)
        value: [(prox, dist, color, offset)]
    :param plot_type: type of plot
    :type plot_type: str
    :param current_view: vispy viewbox to use
    :type current_view: ViewBox
    :param min_width: minimum width of tubes
    :type min_width: float
    """
    total_mesh_instances = 0
    for d, i in meshdata.items():
        total_mesh_instances += len(i)
    logger.info(
        f"Visualising {len(meshdata.keys())} meshes with {total_mesh_instances} instances"
    )

    pbar = progressbar.ProgressBar(
        max_value=total_mesh_instances,
        widgets=[progressbar.SimpleProgress(), progressbar.Bar(), progressbar.Timer()],
        redirect_stdout=True,
    )
    progress_ctr = 0
    for d, i in meshdata.items():
        r1 = float(d[0])
        r2 = float(d[1])
        length = float(d[2])

        # actual plotting bits
        if plot_type == "constant":
            r1 = min_width
            r2 = min_width

        if r1 < min_width:
            r1 = min_width
        if r2 < min_width:
            r2 = min_width

        seg_mesh = None
        # 1: for points, we set the prox/dist to None since they only have
        # positions.
        # 2: single compartment cells with r1, r2, and length 0
        # Note: we can't check if r1 == r2 == length because there
        # may be cylinders with such a set of parameters

        if r1 == r2 and ((i[0][0] is None and i[0][1] is None) or (length == 0.0)):
            seg_mesh = create_sphere(9, 9, radius=r1)
            logger.debug(f"Created spherical mesh template with radius {r1}")
        else:
            rows = 2 + int(length / 2)
            seg_mesh = create_cylindrical_mesh(
                rows=rows, cols=9, radius=[r1, r2], length=length, closed=True
            )
            logger.debug(
                f"Created cylinderical mesh template with radii {r1}, {r2}, {length}"
            )

        instance_positions = []
        instance_transforms = []
        instance_colors = []
        for im in i:
            pbar.update(progress_ctr)
            progress_ctr += 1
            prox = im[0]
            dist = im[1]
            color = im[2]
            offset = im[3]

            # points, spherical meshes
            if prox is not None and dist is not None:
                orig_vec = [0, 0, length]
                dir_vector = [dist.x - prox.x, dist.y - prox.y, dist.z - prox.z]
                k = numpy.cross(orig_vec, dir_vector)
                mag_k = numpy.linalg.norm(k)

                if mag_k != 0.0:
                    k = k / mag_k
                    theta = math.acos(
                        numpy.dot(orig_vec, dir_vector)
                        / (numpy.linalg.norm(orig_vec) * numpy.linalg.norm(dir_vector))
                    )
                    logger.debug(f"k is {k}, theta is {theta}")
                    rot_matrix = rotate(math.degrees(theta), k).T
                    rot_obj = Rotation.from_matrix(rot_matrix[:3, :3])
                else:
                    logger.debug("k is [0..], using zeros for rotation matrix")
                    rot_matrix = numpy.zeros((3, 3))
                    rot_obj = Rotation.from_matrix(rot_matrix)

                instance_positions.append(
                    [offset[0] + prox.x, offset[1] + prox.y, offset[2] + prox.z]
                )
            else:
                instance_positions.append(offset)
                rot_matrix = numpy.zeros((3, 3))
                rot_obj = Rotation.from_matrix(rot_matrix)

            instance_transforms.append(rot_obj.as_matrix())
            instance_colors.append(color)

        assert len(instance_positions) == len(instance_transforms)
        logger.debug(
            f"Instanced: positions: {instance_positions}, transforms: {instance_transforms}"
        )

        mesh = InstancedMesh(
            meshdata=seg_mesh,
            instance_positions=instance_positions,
            instance_transforms=instance_transforms,
            instance_colors=instance_colors,
            parent=current_view.scene,
        )
        # TODO: add a shading filter for light?
        assert mesh is not None
    pbar.finish()


def plot_3D_schematic(
    cell: Cell,
    segment_groups: typing.Optional[typing.List[SegmentGroup]],
    offset: typing.List[float] = [0, 0, 0],
    labels: bool = False,
    width: float = 5.0,
    verbose: bool = False,
    nogui: bool = False,
    title: str = "",
    current_canvas: Optional[scene.SceneCanvas] = None,
    current_view: Optional[scene.ViewBox] = None,
    theme: str = "light",
    color: typing.Optional[str] = "Cell",
    meshdata: typing.Optional[typing.Dict[typing.Any, typing.Any]] = None,
    mesh_precision: int = 2,
) -> None:
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
    :type offset: [float, float, float]
    :param cell: cell to plot
    :type cell: neuroml.Cell
    :param segment_groups: list of unbranched segment groups to plot
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
    :param theme: theme to use (light/dark)
    :type theme: str
    :param color: color to use for segment groups with some special values:

        - if None, each unbranched segment group is given a unique color,
        - if "Cell", each cell is given a unique color
        - if "Default Groups", each cell is given unique colors for all axons,
          dendrites, and soma segments

    :type color: str
    """
    if title == "":
        title = f"3D schematic of segment groups from {cell.id}"

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

    # if no canvas is defined, define a new one
    if current_canvas is None or current_view is None:
        view_min, view_max = get_cell_bound_box(cell)
        current_canvas, current_view = create_new_vispy_canvas(
            view_min, view_max, title, theme=theme
        )

    # colors for cell
    cell_color_soma = get_next_hex_color()
    cell_color_axon = get_next_hex_color()
    cell_color_dendrites = get_next_hex_color()

    if meshdata is None:
        meshdata = {}

    for sgid, segs in ord_segs.items():
        sgobj = cell.get_segment_group(sgid)
        if sgobj.neuro_lex_id != neuro_lex_ids["section"]:
            raise ValueError(
                f"{sgobj} does not have neuro_lex_id set to indicate it is an unbranched segment"
            )

        # get proximal and distal points
        first_seg = segs[0]  # type: Segment
        last_seg = segs[-1]  # type: Segment
        first_prox = cell.get_actual_proximal(first_seg.id)  # type: Point3DWithDiam
        last_dist = last_seg.distal  # type: Point3DWithDiam

        length = math.dist(
            (first_prox.x, first_prox.y, first_prox.z),
            (last_dist.x, last_dist.y, last_dist.z),
        )

        key = (
            f"{round(first_prox.diameter/2, mesh_precision):.{mesh_precision}f}",
            f"{round(last_dist.diameter/2, mesh_precision):.{mesh_precision}f}",
            f"{round(length, mesh_precision):.{mesh_precision}f}",
        )

        branch_color = color
        if color is None:
            branch_color = get_next_hex_color()
        elif color == "Cell":
            branch_color = cell_color_soma
        elif color == "Default Groups":
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

        try:
            meshdata[key].append((first_prox, last_dist, branch_color, offset))
        except KeyError:
            meshdata[key] = [(first_prox, last_dist, branch_color, offset)]

    if not nogui:
        create_instanced_meshes(meshdata, "Detailed", current_view, width)
        app.run()


def create_cylindrical_mesh(
    rows: int,
    cols: int,
    radius: typing.Union[float, typing.List[float]] = [1.0, 1.0],
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
    :type radius: float or [float, float][]
    :param length: length of cylinder
    :type length: float
    :param closed: whether the cylinder should be closed
    :type closed: bool
    :returns: Vertices and faces computed for a cylindrical surface.
    :rtype: MeshData

    """
    verts = numpy.empty((rows + 1, cols, 3), dtype=numpy.float32)
    if isinstance(radius, int) or isinstance(radius, float):
        radius = [radius, radius]  # convert to list

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
        verts = numpy.append(verts, [[0.0, 0.0, 0.0], [0.0, 0.0, 1.0]], axis=0)
    logger.debug(f"Verts are: {verts}")

    # compute faces
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

    # add extra faces to cover the caps
    if closed is True:
        cap1 = (numpy.arange(cols).reshape(cols, 1) + numpy.array([[0, 0, 1]])) % cols
        cap1[..., 0] = len(verts) - 2
        cap2 = (numpy.arange(cols).reshape(cols, 1) + numpy.array([[0, 0, 1]])) % cols
        cap2[..., 0] = len(verts) - 1

        logger.debug(f"cap1 is {cap1}")
        logger.debug(f"cap2 is {cap2}")

        faces = numpy.append(faces, cap1, axis=0)
        faces = numpy.append(faces, cap2, axis=0)

    logger.debug(f"Faces are: {faces}")

    return MeshData(vertices=verts, faces=faces)
