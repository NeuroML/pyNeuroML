#!/usr/bin/env python3
"""
Common utils to help with plotting

File: pyneuroml/utils/plot.py

Copyright 2023 NeuroML contributors
"""

import logging
import os
import random
import typing

import matplotlib
import numpy
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib_scalebar.scalebar import ScaleBar
from neuroml import Cell, NeuroMLDocument, Segment
from neuroml.loaders import read_neuroml2_file

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


DEFAULTS = {
    "v": False,
    "nogui": False,
    "saveToFile": None,
    "interactive3d": False,
    "plane2d": "xy",
    "minWidth": 0.8,
    "square": False,
    "plotType": "detailed",
    "theme": "light",
    "pointFraction": 0,
}  # type: dict[str, typing.Any]


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
    plt.title(title)

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


def get_cell_bound_box(cell: Cell):
    """Get a boundary box for a cell

    :param cell: cell to get boundary box for
    :type cell: neuroml.Cell
    :returns: tuple (min view, max view)

    """
    seg0: Segment = cell.morphology.segments[0]
    ex1 = numpy.array([seg0.distal.x, seg0.distal.y, seg0.distal.z])
    seg1: Segment = cell.morphology.segments[-1]
    ex2 = numpy.array([seg1.distal.x, seg1.distal.y, seg1.distal.z])
    center = (ex1 + ex2) / 2
    diff = numpy.linalg.norm(ex2 - ex1)
    view_min = center - diff
    view_max = center + diff

    return view_min, view_max


def load_minimal_morphplottable__model(
    nml_model: NeuroMLDocument, nml_file_path: str = ""
):
    """Take a model that has been loaded without recursively including all
    bits, and load only information that is needed to plot it.

    :param nml_model: partially loaded model
    :type nml_model: neuroml.NeuroMLDocument
    :param nml_file_path: path of file corresponding to the model
    :type nml_file_path: str

    """
    logger.debug("Loading model bits necessary for plotting.")
    base_path = os.path.dirname(os.path.realpath(nml_file_path))
    # remove bits of the model we don't need
    model_members = list(vars(nml_model).keys())
    required_members = [
        "id",
        "cells",
        "cell2_ca_poolses",
        "networks",
        "populations",
        "includes",
    ]
    for m in model_members:
        if m not in required_members:
            setattr(nml_model, m, None)

    # if the model contains a network, use it
    if len(nml_model.networks) > 0:
        # remove network members we don't need
        network_members = list(vars(nml_model.networks[0]).keys())
        for m in network_members:
            if m != "populations":
                setattr(nml_model.networks[0], m, None)

        # get a list of what cell types are used in the various populations
        required_cell_types = [
            pop.component for pop in nml_model.networks[0].populations
        ]

        # add only required cells that are included in populations to the
        # document
        for inc in nml_model.includes:
            incl_loc = os.path.abspath(os.path.join(base_path, inc.href))
            if os.path.isfile(incl_loc):
                inc = read_neuroml2_file(incl_loc)
                for acell in inc.cells:
                    if acell.id in required_cell_types:
                        acell.biophysical_properties = None
                        nml_model.add(acell)
    else:
        # add any included cells to the main document
        for inc in nml_model.includes:
            incl_loc = os.path.abspath(os.path.join(base_path, inc.href))
            if os.path.isfile(incl_loc):
                inc = read_neuroml2_file(incl_loc)
                for acell in inc.cells:
                    acell.biophysical_properties = None
                    nml_model.add(acell)
