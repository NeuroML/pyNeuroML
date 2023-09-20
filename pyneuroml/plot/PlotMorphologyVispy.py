#!/usr/bin/env python3
"""
Vispy interactive plotting.

Kept in a separate file so that the vispy dependency is not required elsewhere.

File: pyneuroml/plot/PlotMorphologyVispy.py

Copyright 2023 NeuroML contributors
"""


import logging
import random
import textwrap
import typing

import numpy
from neuroml import Cell, NeuroMLDocument, Segment, SegmentGroup
from neuroml.neuro_lex_ids import neuro_lex_ids
from pyneuroml.pynml import read_neuroml2_file
from pyneuroml.utils import extract_position_info
from pyneuroml.utils.plot import DEFAULTS, get_cell_bound_box, get_next_hex_color
from vispy import app, scene

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


VISPY_THEME = {
    "light": {"bg": "white", "fg": "black"},
    "dark": {"bg": "black", "fg": "white"},
}
PYNEUROML_VISPY_THEME = "light"


def add_text_to_vispy_3D_plot(
    current_scene: scene.SceneCanvas,
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
        parent=current_scene,
    )


def create_new_vispy_canvas(
    view_min: typing.Optional[typing.List[float]] = None,
    view_max: typing.Optional[typing.List[float]] = None,
    title: str = "",
    console_font_size: float = 10,
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
    canvas = scene.SceneCanvas(
        keys="interactive",
        show=True,
        bgcolor=VISPY_THEME[theme]["bg"],
        size=(800, 600),
        title="NeuroML viewer (VisPy)",
    )
    grid = canvas.central_widget.add_grid(margin=10)
    grid.spacing = 0

    title_widget = scene.Label(title, color=VISPY_THEME[theme]["fg"])
    title_widget.height_max = 80
    grid.add_widget(title_widget, row=0, col=0, col_span=1)

    console_widget = scene.Console(
        text_color=VISPY_THEME[theme]["fg"],
        font_size=console_font_size,
    )
    console_widget.height_max = 80
    grid.add_widget(console_widget, row=2, col=0, col_span=1)

    bottom_padding = grid.add_widget(row=3, col=0, col_span=1)
    bottom_padding.height_max = 10

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

    # console text
    console_text = "Controls: reset view: 0; quit: Esc/9"
    if len(cams) > 1:
        console_text += "; cycle camera: 1, 2 (fwd/bwd)"

    cam_text = {
        cam1: textwrap.dedent(
            """
            Left mouse button: pans view; right mouse button or scroll:
            zooms"""
        ),
        cam2: textwrap.dedent(
            """
            Left mouse button: orbits view around center point; right mouse
            button or scroll: change zoom level; Shift + left mouse button:
            translate center point; Shift + right mouse button: change field of
            view; r/R: view rotation animation"""
        ),
        cam3: textwrap.dedent(
            """
            Left mouse button: orbits view around center point; right
            mouse button or scroll: change zoom level; Shift + left mouse
            button: translate center point; Shift + right mouse button: change
            field of view"""
        ),
        cam4: textwrap.dedent(
            """
            Arrow keys/WASD to move forward/backwards/left/right; F/C to move
            up and down; Space to brake; Left mouse button/I/K/J/L to control
            pitch and yaw; Q/E for rolling"""
        ),
    }

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

    console_widget.write(f"Center: {view.camera.center}")
    console_widget.write(console_text)
    console_widget.write(
        f"Current camera: {view.camera.name}: "
        + cam_text[view.camera].replace("\n", " ").strip()
    )

    if axes_pos:
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

        console_widget.clear()
        # console_widget.write(f"Center: {view.camera.center}")
        console_widget.write(console_text)
        console_widget.write(
            f"Current camera: {view.camera.name}: "
            + cam_text[view.camera].replace("\n", " ").strip()
        )

    return scene, view


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
):
    """Plot interactive plots in 3D using Vispy

    https://vispy.org

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
    """
    if plot_type not in ["detailed", "constant", "schematic", "point"]:
        raise ValueError(
            "plot_type must be one of 'detailed', 'constant', 'schematic', 'point'"
        )

    if verbose:
        print(f"Plotting {nml_file}")

    if type(nml_file) is str:
        nml_model = read_neuroml2_file(
            nml_file,
            include_includes=False,
            check_validity_pre_include=False,
            verbose=False,
            optimized=True,
        )
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
    ) = extract_position_info(
        nml_model, verbose, nml_file if type(nml_file) is str else ""
    )

    # Collect all markers and only plot one markers object
    # this is more efficient than multiple markers, one for each point.
    # TODO: also collect all line points and only use one object rather than a
    # new object for each cell: will only work for the case where all lines
    # have the same width
    marker_sizes = []
    marker_points = []
    marker_colors = []

    logger.debug(f"positions: {positions}")
    logger.debug(f"pop_id_vs_cell: {pop_id_vs_cell}")
    logger.debug(f"cell_id_vs_cell: {cell_id_vs_cell}")
    logger.debug(f"pop_id_vs_color: {pop_id_vs_color}")
    logger.debug(f"pop_id_vs_radii: {pop_id_vs_radii}")

    # not used, clear up
    print(f"Plotting {len(cell_id_vs_cell)} cells")
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
            view_min = list(numpy.array(pos))

    current_scene, current_view = create_new_vispy_canvas(
        view_min, view_max, title, theme=theme
    )

    logger.debug(f"figure extents are: {view_min}, {view_max}")

    # process plot_spec
    point_cells = []  # type: typing.List[int]
    schematic_cells = []  # type: typing.List[int]
    constant_cells = []  # type: typing.List[int]
    detailed_cells = []  # type: typing.List[int]
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

    while pop_id_vs_cell:
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
            color = pop_id_vs_color[pop_id] if pop_id in pop_id_vs_color else None

            try:
                logging.info(f"Plotting {cell.id}")
            except AttributeError:
                logging.info(f"Plotting a point cell at {pos}")

            if cell is None:
                marker_points.extend([pos])
                marker_sizes.extend([radius])
                marker_colors.extend([color])
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
                    marker_points.extend([pos1])
                    # larger than the default soma width, which would be too
                    # small
                    marker_sizes.extend([25])
                    marker_colors.extend([color])
                elif plot_type == "schematic" or cell.id in schematic_cells:
                    plot_3D_schematic(
                        offset=pos,
                        cell=cell,
                        segment_groups=None,
                        color=color,
                        verbose=verbose,
                        current_scene=current_scene,
                        current_view=current_view,
                        nogui=True,
                    )
                elif (
                    plot_type == "detailed"
                    or cell.id in detailed_cells
                    or plot_type == "constant"
                    or cell.id in constant_cells
                ):
                    logger.debug(f"Cell for 3d is: {cell.id}")
                    pts, sizes, colors = plot_3D_cell_morphology(
                        offset=pos,
                        cell=cell,
                        color=color,
                        plot_type=plot_type,
                        verbose=verbose,
                        current_scene=current_scene,
                        current_view=current_view,
                        min_width=min_width,
                        nogui=True,
                    )
                    marker_points.extend(pts)
                    marker_sizes.extend(sizes)
                    marker_colors.extend(colors)

    if len(marker_points) > 0:
        scene.Markers(
            pos=numpy.array(marker_points),
            size=numpy.array(marker_sizes),
            spherical=True,
            face_color=marker_colors,
            edge_color=marker_colors,
            edge_width=0,
            parent=current_view.scene,
            scaling=True,
            antialias=0,
        )
    if not nogui:
        app.run()


def plot_3D_cell_morphology(
    offset: typing.List[float] = [0, 0, 0],
    cell: Cell = None,
    color: typing.Optional[str] = None,
    title: str = "",
    verbose: bool = False,
    current_scene: scene.SceneCanvas = None,
    current_view: scene.ViewBox = None,
    min_width: float = DEFAULTS["minWidth"],
    axis_min_max: typing.List = [float("inf"), -1 * float("inf")],
    nogui: bool = True,
    plot_type: str = "constant",
    theme="light",
):
    """Plot the detailed 3D morphology of a cell using vispy.
    https://vispy.org/

    .. versionadded:: 1.0.0

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
    :param current_scene: vispy scene.SceneCanvas to use (a new one is created if it is not
        provided)
    :type current_scene: scene.SceneCanvas
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
    :raises: ValueError if `cell` is None

    """
    if cell is None:
        raise ValueError(
            "No cell provided. If you would like to plot a network of point neurons, consider using `plot_2D_point_cells` instead"
        )

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

    if current_scene is None or current_view is None:
        view_min, view_max = get_cell_bound_box(cell)
        current_scene, current_view = create_new_vispy_canvas(
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

    # for lines/segments
    points = []
    toconnect = []
    colors = []
    # for any spheres which we plot as markers at once
    marker_points = []
    marker_colors = []
    marker_sizes = []

    for seg in cell.morphology.segments:
        p = cell.get_actual_proximal(seg.id)
        d = seg.distal
        width = (p.diameter + d.diameter) / 2

        if width < min_width:
            width = min_width

        if plot_type == "constant":
            width = min_width

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

        # check if for a spherical segment, add extra spherical node
        if p.x == d.x and p.y == d.y and p.z == d.z and p.diameter == d.diameter:
            marker_points.append([offset[0] + p.x, offset[1] + p.y, offset[2] + p.z])
            marker_colors.append(seg_color)
            marker_sizes.append(p.diameter)

        if plot_type == "constant":
            points.append([offset[0] + p.x, offset[1] + p.y, offset[2] + p.z])
            colors.append(seg_color)
            points.append([offset[0] + d.x, offset[1] + d.y, offset[2] + d.z])
            colors.append(seg_color)
            toconnect.append([len(points) - 2, len(points) - 1])
        # every segment plotted individually
        elif plot_type == "detailed":
            points = []
            toconnect = []
            colors = []
            points.append([offset[0] + p.x, offset[1] + p.y, offset[2] + p.z])
            colors.append(seg_color)
            points.append([offset[0] + d.x, offset[1] + d.y, offset[2] + d.z])
            colors.append(seg_color)
            toconnect.append([len(points) - 2, len(points) - 1])
            scene.Line(
                pos=points,
                color=colors,
                connect=numpy.array(toconnect),
                parent=current_view.scene,
                width=width,
            )

    if plot_type == "constant":
        scene.Line(
            pos=points,
            color=colors,
            connect=numpy.array(toconnect),
            parent=current_view.scene,
            width=width,
        )

    if not nogui:
        # markers
        if len(marker_points) > 0:
            scene.Markers(
                pos=numpy.array(marker_points),
                size=numpy.array(marker_sizes),
                spherical=True,
                face_color=marker_colors,
                edge_color=marker_colors,
                edge_width=0,
                parent=current_view.scene,
                scaling=True,
                antialias=0,
            )
        app.run()
    return marker_points, marker_sizes, marker_colors


def plot_3D_schematic(
    cell: Cell,
    segment_groups: typing.Optional[typing.List[SegmentGroup]],
    offset: typing.List[float] = [0, 0, 0],
    labels: bool = False,
    width: float = 5.0,
    verbose: bool = False,
    nogui: bool = False,
    title: str = "",
    current_scene: scene.SceneCanvas = None,
    current_view: scene.ViewBox = None,
    theme: str = "light",
    color: typing.Optional[str] = "Cell",
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
    :param current_scene: vispy scene.SceneCanvas to use (a new one is created if it is not
        provided)
    :type current_scene: scene.SceneCanvas
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
    if current_scene is None or current_view is None:
        view_min, view_max = get_cell_bound_box(cell)
        current_scene, current_view = create_new_vispy_canvas(
            view_min, view_max, title, theme=theme
        )

    points = []
    toconnect = []
    colors = []
    text = []
    textpoints = []
    # colors for cell
    cell_color_soma = get_next_hex_color()
    cell_color_axon = get_next_hex_color()
    cell_color_dendrites = get_next_hex_color()

    for sgid, segs in ord_segs.items():
        sgobj = cell.get_segment_group(sgid)
        if sgobj.neuro_lex_id != neuro_lex_ids["section"]:
            raise ValueError(
                f"{sgobj} does not have neuro_lex_id set to indicate it is an unbranched segment"
            )

        # get proximal and distal points
        first_seg = segs[0]  # type: Segment
        last_seg = segs[-1]  # type: Segment
        first_prox = cell.get_actual_proximal(first_seg.id)

        points.append(
            [
                offset[0] + first_prox.x,
                offset[1] + first_prox.y,
                offset[2] + first_prox.z,
            ]
        )
        points.append(
            [
                offset[0] + last_seg.distal.x,
                offset[1] + last_seg.distal.y,
                offset[2] + last_seg.distal.z,
            ]
        )
        if color is None:
            colors.append(get_next_hex_color())
            colors.append(get_next_hex_color())
        elif color == "Cell":
            colors.append(cell_color_soma)
            colors.append(cell_color_soma)
        elif color == "Default Groups":
            if first_seg.id in soma_segs:
                colors.append(cell_color_soma)
                colors.append(cell_color_soma)
            elif first_seg.id in axon_segs:
                colors.append(cell_color_axon)
                colors.append(cell_color_axon)
            elif first_seg.id in dend_segs:
                colors.append(cell_color_dendrites)
                colors.append(cell_color_dendrites)
            else:
                colors.append(get_next_hex_color())
                colors.append(get_next_hex_color())
        else:
            colors.append(color)
            colors.append(color)

        toconnect.append([len(points) - 2, len(points) - 1])

        # TODO: needs fixing to show labels
        if labels:
            text.append(f"{sgid}")
            textpoints.append(
                [
                    offset[0] + (first_prox.x + last_seg.distal.x) / 2,
                    offset[1] + (first_prox.y + last_seg.distal.y) / 2,
                    offset[2] + (first_prox.z + last_seg.distal.z) / 2,
                ]
            )
            """

            alabel = add_text_to_vispy_3D_plot(current_scene=current_view.scene, text=f"{sgid}",
                                               xv=[offset[0] + first_seg.proximal.x, offset[0] + last_seg.distal.x],
                                               yv=[offset[0] + first_seg.proximal.y, offset[0] + last_seg.distal.y],
                                               zv=[offset[1] + first_seg.proximal.z, offset[1] + last_seg.distal.z],
                                               color=colors[-1])
            alabel.font_size = 30
            """

    scene.Line(
        points,
        parent=current_view.scene,
        color=colors,
        width=width,
        connect=numpy.array(toconnect),
    )
    if labels:
        logger.debug("Text rendering")
        scene.Text(
            text, pos=textpoints, font_size=30, color="black", parent=current_view.scene
        )

    if not nogui:
        app.run()
