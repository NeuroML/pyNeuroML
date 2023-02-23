#!/usr/bin/env python3
"""
Common utils to help with plotting

File: pyneuroml/utils/plot.py

Copyright 2023 NeuroML contributors
"""

import logging
import textwrap
import numpy
import typing
import random
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.axes import Axes
from matplotlib.patches import Rectangle
from matplotlib_scalebar.scalebar import ScaleBar
from vispy import scene
from vispy.scene import SceneCanvas


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def add_text_to_vispy_3D_plot(
    scene: SceneCanvas,
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
    :type scene: SceneCanvas
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
    )


def add_text_to_matplotlib_2D_plot(
    ax: matplotlib.axes.Axes,
    xv: typing.List[float],
    yv: typing.List[float],
    color: str,
    text: str,
    horizontal: str = "center",
    vertical: str = "bottom",
    clip_on: bool = True,
):
    """Add text to a matplotlib plot between two points

    Wrapper around matplotlib.axes.Axes.text.

    Rotates the text label to ensure it is at the same angle as the line.

    :param ax: matplotlib axis object
    :type ax: Axes
    :param xv: start and end coordinates in one axis
    :type xv: list[x1, x2]
    :param yv: start and end coordinates in second axix
    :type yv: list[y1, y2]
    :param color: color of text
    :type color: str
    :param text: text to write
    :type text: str
    :param clip_on: toggle clip_on (if False, text will also be shown outside plot)
    :type clip_on: bool

    """
    angle = int(numpy.rad2deg(numpy.arctan2((yv[1] - yv[0]), (xv[1] - xv[0]))))
    if angle > 90:
        angle -= 180
    elif angle < -90:
        angle += 180

    ax.text(
        (xv[0] + xv[1]) / 2,
        (yv[0] + yv[1]) / 2,
        text,
        color=color,
        horizontalalignment=horizontal,
        verticalalignment=vertical,
        rotation_mode="default",
        rotation=angle,
        clip_on=clip_on,
    )


def get_next_hex_color(my_random: typing.Optional[random.Random] = None) -> str:
    """Get a new randomly generated HEX colour code.

    You may pass a random.Random instance that you may be used. Otherwise the
    default Python random generator will be used.

    :param my_random: a random.Random object
    :type my_random: random.Random
    :returns: HEX colour code
    """
    if my_random is not None:
        return "#%06x" % my_random.randint(0, 0xFFFFFF)
    else:
        return "#%06x" % random.randint(0, 0xFFFFFF)


def add_box_to_matplotlib_2D_plot(ax, xy, height, width, color):
    """Add a box to a matplotlib plot, at xy of `height`, `width` and `color`.

    :param ax: matplotlib.axes.Axes object
    :type ax: matplotlob.axes.Axis
    :param xy: bottom left corner of box
    :type xy: typing.List[float]
    :param height: height of box
    :type height: float
    :param width: width of box
    :type width: float
    :param color: color of box for edge, face, fill
    :type color: str
    :returns: None

    """
    ax.add_patch(
        Rectangle(xy, width, height, edgecolor=color, facecolor=color, fill=True)
    )


def get_new_matplotlib_morph_plot(
    title: str = "", plane2d: str = "xy"
) -> typing.Tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]:
    """Get a new 2D matplotlib plot for morphology related plots.

    :param title: title of plot
    :type title: str
    :param plane2d: plane to use
    :type plane: str
    :returns: new [matplotlib.figure.Figure, matplotlib.axes.Axes]
    :rtype: [matplotlib.figure.Figure, matplotlib.axes.Axes]
    """
    fig, ax = plt.subplots(1, 1)  # noqa
    plt.get_current_fig_manager().set_window_title(title)

    ax.set_aspect("equal")

    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.yaxis.set_ticks_position("left")
    ax.xaxis.set_ticks_position("bottom")

    if plane2d == "xy":
        ax.set_xlabel("x (μm)")
        ax.set_ylabel("y (μm)")
    elif plane2d == "yx":
        ax.set_xlabel("y (μm)")
        ax.set_ylabel("x (μm)")
    elif plane2d == "xz":
        ax.set_xlabel("x (μm)")
        ax.set_ylabel("z (μm)")
    elif plane2d == "zx":
        ax.set_xlabel("z (μm)")
        ax.set_ylabel("x (μm)")
    elif plane2d == "yz":
        ax.set_xlabel("y (μm)")
        ax.set_ylabel("z (μm)")
    elif plane2d == "zy":
        ax.set_xlabel("z (μm)")
        ax.set_ylabel("y (μm)")
    else:
        raise ValueError(f"Invalid value for plane: {plane2d}")

    return fig, ax


class LineDataUnits(Line2D):
    """New Line class for making lines with specific widthS

    Reference:
        https://stackoverflow.com/questions/19394505/expand-the-line-with-specified-width-in-data-unit
    """

    def __init__(self, *args, **kwargs):
        _lw_data = kwargs.pop("linewidth", 1)
        super().__init__(*args, **kwargs)
        self._lw_data = _lw_data

    def _get_lw(self):
        if self.axes is not None:
            ppd = 72.0 / self.axes.figure.dpi
            trans = self.axes.transData.transform
            return ((trans((1, self._lw_data)) - trans((0, 0))) * ppd)[1]
        else:
            return 1

    def _set_lw(self, lw):
        self._lw_data = lw

    _linewidth = property(_get_lw, _set_lw)


def autoscale_matplotlib_plot(verbose: bool = False, square: bool = True) -> None:
    """Autoscale the current matplotlib plot

    :param verbose: toggle verbosity
    :type verbose: bool
    :param square: toggle squaring of plot
    :type square: bool
    :returns: None

    """
    plt.autoscale()
    xl = plt.xlim()
    yl = plt.ylim()
    if verbose:
        print("Auto limits - x: %s , y: %s" % (xl, yl))

    small = 0.1
    if xl[1] - xl[0] < small and yl[1] - yl[0] < small:  # i.e. only a point
        plt.xlim([-100, 100])
        plt.ylim([-100, 100])
    elif xl[1] - xl[0] < small:
        d_10 = (yl[1] - yl[0]) / 10
        m = xl[0] + (xl[1] - xl[0]) / 2.0
        plt.xlim([m - d_10, m + d_10])
    elif yl[1] - yl[0] < small:
        d_10 = (xl[1] - xl[0]) / 10
        m = yl[0] + (yl[1] - yl[0]) / 2.0
        plt.ylim([m - d_10, m + d_10])

    if square:
        if xl[1] - xl[0] > yl[1] - yl[0]:
            d2 = (xl[1] - xl[0]) / 2
            m = yl[0] + (yl[1] - yl[0]) / 2.0
            plt.ylim([m - d2, m + d2])

        if xl[1] - xl[0] < yl[1] - yl[0]:
            d2 = (yl[1] - yl[0]) / 2
            m = xl[0] + (xl[1] - xl[0]) / 2.0
            plt.xlim([m - d2, m + d2])


def add_scalebar_to_matplotlib_plot(axis_min_max, ax):
    """Add a scalebar to matplotlib plots.

    The scalebar is of magnitude 50 by default, but if the difference between
    max and min vals is less than 100, it's reduced to 5, and if the difference
    is less than 10, it's reduced to 1.

    :param axis_min_max: minimum, maximum value in plot
    :type axis_min_max: [float, float]
    :param ax: axis to plot scalebar at
    :type ax: matplotlib.axes.Axes
    :returns: None

    """
    # add a scalebar
    # ax = fig.add_axes([0, 0, 1, 1])
    sc_val = 50
    if axis_min_max[1] - axis_min_max[0] < 100:
        sc_val = 5
    if axis_min_max[1] - axis_min_max[0] < 10:
        sc_val = 1
    scalebar1 = ScaleBar(
        0.001,
        units="mm",
        dimension="si-length",
        scale_loc="top",
        location="lower right",
        fixed_value=sc_val,
        fixed_units="um",
        box_alpha=0.8,
    )
    ax.add_artist(scalebar1)


def add_line_to_matplotlib_2D_plot(ax, xv, yv, width, color, axis_min_max):
    """Add a line to a matplotlib plot

    :param ax: matplotlib.axes.Axes object
    :type ax: matplotlib.axes.Axes
    :param xv: x values
    :type xv: [float, float]
    :param yv: y values
    :type yv: [float, float]
    :param width: width of line
    :type width: float
    :param color: color of line
    :type color: str
    :param axis_min_max: min, max value of axis
    :type axis_min_max: [float, float]"""

    if (
        abs(xv[0] - xv[1]) < 0.01 and abs(yv[0] - yv[1]) < 0.01
    ):  # looking at the cylinder from the top, OR a sphere, so draw a circle
        xv[1] = xv[1] + width / 1000.0
        yv[1] = yv[1] + width / 1000.0

        ax.add_line(
            LineDataUnits(xv, yv, linewidth=width, solid_capstyle="round", color=color)
        )

    ax.add_line(
        LineDataUnits(xv, yv, linewidth=width, solid_capstyle="butt", color=color)
    )

    axis_min_max[0] = min(axis_min_max[0], xv[0])
    axis_min_max[0] = min(axis_min_max[0], xv[1])
    axis_min_max[1] = max(axis_min_max[1], xv[0])
    axis_min_max[1] = max(axis_min_max[1], xv[1])


def create_new_vispy_canvas(view_min: typing.List[float], view_max:
                            typing.List[float], title: str = "", axes_pos:
                            typing.Optional[typing.List] = None, axes_length: float = 100,
                            axes_width: int = 2):
    """Create a new vispy scene canvas with a view and optional axes lines

    Reference: https://vispy.org/gallery/scene/axes_plot.html

    :param view_min: min view co-ordinates
    :type view_min: [float, float, float]
    :param view_max: max view co-ordinates
    :type view_max: [float, float, float]
    :param title: title of canvas
    :type title: str
    :param axes_pos: position to draw axes at
    :type axes_pos: [float, float, float]
    :param axes_length: length of axes
    :type axes_length: float
    :param axes_width: width of axes lines
    :type axes_width: float
    :returns: scene, view
    """
    canvas = scene.SceneCanvas(keys='interactive', show=True,
                               bgcolor="white", size=(800, 600))
    grid = canvas.central_widget.add_grid(margin=10)
    grid.spacing = 0

    view_center = (numpy.array(view_max) - numpy.array(view_min)) / 2

    title_widget = scene.Label(title, color="black")
    title_widget.height_max = 40
    grid.add_widget(title_widget, row=0, col=0, col_span=2)

    console_widget = scene.Console(text_color="black", font_size=8)
    console_widget.height_max = 40
    grid.add_widget(console_widget, row=3, col=1, col_span=1)
    console_text = "\tKeys: 0 reset, 5 changes camera"

    yaxis = scene.AxisWidget(orientation='left',
                             axis_label='Extent (Y)',
                             axis_font_size=12,
                             axis_label_margin=60,
                             axis_color='black',
                             tick_color='black',
                             tick_label_margin=5,
                             text_color='black')
    yaxis.width_max = 80
    grid.add_widget(yaxis, row=1, col=0)

    xaxis = scene.AxisWidget(orientation='bottom',
                             axis_label='Extent (X)',
                             axis_font_size=12,
                             axis_label_margin=40,
                             axis_color='black',
                             tick_color='black',
                             text_color='black',
                             tick_label_margin=5)

    xaxis.height_max = 60
    grid.add_widget(xaxis, row=2, col=1)

    right_padding = grid.add_widget(row=0, col=2, row_span=4)
    right_padding.width_max = 50

    bottom_padding = grid.add_widget(row=4, col=0, col_span=3)
    bottom_padding.height_max = 40

    view = grid.add_view(row=1, col=1, border_color='black')
    # create cameras
    # https://vispy.org/gallery/scene/flipped_axis.html
    cam1 = scene.cameras.PanZoomCamera(parent=view.scene, aspect=1,
                                       name='PanZoom')
    cam1.center = [view_center[0], view_center[1]]
    cam2 = scene.cameras.TurntableCamera(parent=view.scene, name='Turntable')
    cam2.center = view_center
    cam3 = scene.cameras.ArcballCamera(parent=view.scene, name='Arcball')
    cam3.center = view_center
    cam4 = scene.cameras.FlyCamera(parent=view.scene, name='Fly')
    cam4.center = view_center
    cam4.autoroll = False

    cams = {
        cam1: cam2,
        cam2: cam3,
        cam3: cam4,
        cam4: cam1,
    }

    cam_text = {
        cam1: """
        Left mouse button: pans view; right mouse button or scroll:
        zooms""",
        cam2: """
        Left mouse button: orbits view around center point; right
        mouse button or scroll: change zoom level; Shift + left mouse button:
        translate center point; Shift + right mouse button: change field of
        view""",
        cam3: """
        Left mouse button: orbits view around center point; right
        mouse button or scroll: change zoom level; Shift + left mouse button:
        translate center point; Shift + right mouse button: change field of
        view""",
        cam4: """
        Arrow keys/WASD to move forward/backwards/left/right; F/C to
        move up and down; Space to brake; Left mouse button/I/K/J/L to
        control pitch and yaw; Q/E for rolling"""
    }

    for acam in cams.values():
        acam.set_range(
            x=(view_min[0], view_max[0]),
            y=(view_min[1], view_max[1]),
            z=(view_min[2], view_max[2])
        )

    # Fly is default

    view.camera = cam4
    xaxis.link_view(view)
    yaxis.link_view(view)

    console_widget.write(console_text + f" ({view.camera.name})")

    @canvas.events.key_press.connect
    def vispy_on_key_press(event):
        if event.text == '5':
            state = view.camera.get_state()
            view.camera = cams[view.camera]
            console_widget.clear()
            console_widget.write(console_text + f"({view.camera.name})")
            try:
                console_widget.write(textwrap.dedent(cam_text[view.camera]).replace("\n", " "))
            except KeyError:
                pass
            # PanZoom doesn't like it
            if view.camera.name != "PanZoom":
                try:
                    view.camera.center = state['center']
                    view.camera.scale_factor = state['scale_factor']
                    view.camera.fov = state['fov']
                except KeyError:
                    pass
            else:
                view.camera.set_range(
                    x=(view_min[0], view_max[0]),
                    y=(view_min[1], view_max[1]),
                    z=(view_min[2], view_max[2])
                )
        elif event.text == '0':
            for acam in cams.values():
                acam.set_range(
                    x=(view_min[0], view_max[0]),
                    y=(view_min[1], view_max[1]),
                    z=(view_min[2], view_max[2])
                )

    # xyz axis for orientation
    # TODO improve placement
    if axes_pos:
        scene.Line([axes_pos, [axes_pos[0] + axes_length, axes_pos[1], axes_pos[2]]],
                   parent=view.scene, color="black",
                   width=axes_width)
        scene.Line([axes_pos, [axes_pos[1], axes_pos[1] + axes_length, axes_pos[2]]],
                   parent=view.scene, color="black",
                   width=axes_width)
        scene.Line([axes_pos, [axes_pos[1], axes_pos[1], axes_pos[2] + axes_length]],
                   parent=view.scene, color="black",
                   width=axes_width)

    return scene, view


