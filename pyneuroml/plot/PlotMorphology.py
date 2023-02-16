#!/usr/bin/env python3
"""
Utilities to plot NeuroML2 cell morphologies.

File: pyneuroml/plot/PlotMorphology.py

Copyright 2023 NeuroML contributors
"""


import argparse
import os
import sys
import random

import typing
import logging

import numpy
import matplotlib
from matplotlib import pyplot as plt
import plotly.graph_objects as go

from pyneuroml.pynml import read_neuroml2_file
from pyneuroml.utils.cli import build_namespace
from pyneuroml.utils import extract_position_info
from pyneuroml.utils.plot import (
    add_text_to_matplotlib_2D_plot,
    get_next_hex_color,
    add_box_to_matplotlib_2D_plot,
    get_new_matplotlib_morph_plot,
    autoscale_matplotlib_plot,
    add_scalebar_to_matplotlib_plot,
    add_line_to_matplotlib_2D_plot,
)
from neuroml import SegmentGroup, Cell
from neuroml.neuro_lex_ids import neuro_lex_ids


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


DEFAULTS = {
    "v": False,
    "nogui": False,
    "saveToFile": None,
    "interactive3d": False,
    "plane2d": "xy",
    "minwidth": 0.8,
    "square": False,
    "plotType": "Detailed",
}


def process_args():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=("A script which can generate plots of morphologies in NeuroML 2")
    )

    parser.add_argument(
        "nmlFile",
        type=str,
        metavar="<NeuroML 2 file>",
        help="Name of the NeuroML 2 file",
    )

    parser.add_argument(
        "-v", action="store_true", default=DEFAULTS["v"], help="Verbose output"
    )

    parser.add_argument(
        "-nogui",
        action="store_true",
        default=DEFAULTS["nogui"],
        help="Don't open plot window",
    )

    parser.add_argument(
        "-plane2d",
        type=str,
        metavar="<plane, e.g. xy, yz, zx>",
        default=DEFAULTS["plane2d"],
        help="Plane to plot on for 2D plot",
    )

    parser.add_argument(
        "-plotType",
        type=str,
        metavar="<type: Detailed, Constant, or Schematic>",
        default=DEFAULTS["plotType"],
        help="Plane to plot on for 2D plot",
    )
    parser.add_argument(
        "-minWidth",
        action="store_true",
        default=DEFAULTS["minwidth"],
        help="Minimum width of lines to use",
    )

    parser.add_argument(
        "-interactive3d",
        action="store_true",
        default=DEFAULTS["interactive3d"],
        help="Show interactive 3D plot",
    )

    parser.add_argument(
        "-saveToFile",
        type=str,
        metavar="<Image file name>",
        default=None,
        help="Name of the image file",
    )

    parser.add_argument(
        "-square",
        action="store_true",
        default=DEFAULTS["square"],
        help="Scale axes so that image is approximately square",
    )

    return parser.parse_args()


def main(args=None):
    if args is None:
        args = process_args()

    plot_from_console(a=args)


def plot_from_console(a: typing.Optional[typing.Any] = None, **kwargs: str):
    """Wrapper around functions for the console script.

    :param a: arguments object
    :type a:
    :param kwargs: other arguments
    """
    a = build_namespace(DEFAULTS, a, **kwargs)
    print(a)
    if a.interactive3d:
        plot_interactive_3D(a.nml_file, a.minwidth, a.v, a.nogui, a.save_to_file)
    else:
        plot_2D(
            a.nml_file,
            a.plane2d,
            a.minwidth,
            a.v,
            a.nogui,
            a.save_to_file,
            a.square,
            a.plot_type,
        )


def plot_2D(
    nml_file: str,
    plane2d: str = "xy",
    min_width: float = DEFAULTS["minwidth"],
    verbose: bool = False,
    nogui: bool = False,
    save_to_file: typing.Optional[str] = None,
    square: bool = False,
    plot_type: str = "Detailed",
    title: typing.Optional[str] = None,
    close_plot: bool = False
):
    """Plot cell morphologies in 2D.

    If a file with a network containing multiple cells is provided, it will
    plot all the cells.

    This uses matplotlib to plot the morphology in 2D.

    :param nml_file: path to NeuroML cell file
    :type nml_file: str
    :param plane2d: what plane to plot (xy/yx/yz/zy/zx/xz)
    :type plane2d: str
    :param min_width: minimum width for segments (useful for visualising very
        thin segments): default 0.8um
    :type min_width: float
    :param verbose: show extra information (default: False)
    :type verbose: bool
    :param nogui: do not show matplotlib GUI (default: false)
    :type nogui: bool
    :param save_to_file: optional filename to save generated morphology to
    :type save_to_file: str
    :param square: scale axes so that image is approximately square
    :type square: bool
    :param plot_type: type of plot, one of:
        - Detailed: show detailed morphology taking into account each segment's
          width
        - Constant: show morphology, but use constant line widths
        - Schematic: only plot each unbranched segment group as a straight
          line, not following each segment
    :type plot_type: str
    :param title: title of plot
    :type title: str
    :param close_plot: call pyplot.close() to close plot after plotting
    :type close_plot: bool
    """

    if plot_type not in ["Detailed", "Constant", "Schematic"]:
        raise ValueError(
            "plot_type must be one of 'Detailed', 'Constant', or 'Schematic'"
        )

    if verbose:
        print("Plotting %s" % nml_file)

    nml_model = read_neuroml2_file(
        nml_file,
        include_includes=True,
        check_validity_pre_include=False,
        verbose=False,
        optimized=True,
    )

    (
        cell_id_vs_cell,
        pop_id_vs_cell,
        positions,
        pop_id_vs_color,
        pop_id_vs_radii,
    ) = extract_position_info(nml_model, verbose)

    if title is None:
        title = "2D plot of %s from %s" % (nml_model.networks[0].id, nml_file)

    if verbose:
        logger.debug(f"positions: {positions}")
        logger.debug(f"pop_id_vs_cell: {pop_id_vs_cell}")
        logger.debug(f"cell_id_vs_cell: {cell_id_vs_cell}")
        logger.debug(f"pop_id_vs_color: {pop_id_vs_color}")
        logger.debug(f"pop_id_vs_radii: {pop_id_vs_radii}")

    fig, ax = get_new_matplotlib_morph_plot(title, plane2d)
    axis_min_max = [float("inf"), -1 * float("inf")]

    for pop_id in pop_id_vs_cell:
        cell = pop_id_vs_cell[pop_id]
        pos_pop = positions[pop_id]

        for cell_index in pos_pop:
            pos = pos_pop[cell_index]
            radius = pop_id_vs_radii[pop_id] if pop_id in pop_id_vs_radii else 10
            color = pop_id_vs_color[pop_id] if pop_id in pop_id_vs_color else None

            if plot_type == "Schematic":
                plot_2D_schematic(
                    offset=pos,
                    cell=cell,
                    segment_groups=None,
                    labels=True,
                    plane2d=plane2d,
                    min_width=min_width,
                    verbose=verbose,
                    fig=fig,
                    ax=ax,
                    scalebar=False,
                    nogui=True,
                    autoscale=False,
                    square=False,
                )
            else:
                plot_2D_cell_morphology(
                    offset=pos,
                    cell=cell,
                    plane2d=plane2d,
                    color=color,
                    soma_radius=radius,
                    plot_type=plot_type,
                    verbose=verbose,
                    fig=fig,
                    ax=ax,
                    min_width=min_width,
                    axis_min_max=axis_min_max,
                    scalebar=False,
                    nogui=True,
                    autoscale=False,
                    square=False,
                )

    add_scalebar_to_matplotlib_plot(axis_min_max, ax)
    autoscale_matplotlib_plot(verbose, square)

    if save_to_file:
        abs_file = os.path.abspath(save_to_file)
        plt.savefig(abs_file, dpi=200, bbox_inches="tight")
        print(f"Saved image on plane {plane2d} to {abs_file} of plot: {title}")

    if not nogui:
        plt.show()
    if close_plot:
        logger.info("Closing plot")
        plt.close()


def plot_interactive_3D(
    nml_file: str,
    min_width: float = 0.8,
    verbose: bool = False,
    nogui: bool = False,
    save_to_file: typing.Optional[str] = None,
    plot_type: str = "Detailed",
):
    """Plot NeuroML2 cell morphology interactively using Plot.ly

    Please note that the interactive plot uses Plotly, which uses WebGL. So,
    you need to use a WebGL enabled browser, and performance here may be
    hardware dependent.

    https://plotly.com/python/webgl-vs-svg/
    https://en.wikipedia.org/wiki/WebGL

    :param nml_file: path to NeuroML cell file
    :type nml_file: str
    :param min_width: minimum width for segments (useful for visualising very
        thin segments): default 0.8um
    :type min_width: float
    :param verbose: show extra information (default: False)
    :type verbose: bool
    :param nogui: do not show matplotlib GUI (default: false)
    :type nogui: bool
    :param save_to_file: optional filename to save generated morphology to
    :type save_to_file: str
    :param plot_type: type of plot, one of:
        - Detailed: show detailed morphology taking into account each segment's
          width
        - Constant: show morphology, but use constant line widths
        - Schematic: only plot each unbranched segment group as a straight
          line, not following each segment
    :type plot_type: str
    """
    if plot_type not in ["Detailed", "Constant", "Schematic"]:
        raise ValueError(
            "plot_type must be one of 'Detailed', 'Constant', or 'Schematic'"
        )

    nml_model = read_neuroml2_file(nml_file)

    fig = go.Figure()
    for cell in nml_model.cells:
        title = f"3D plot of {cell.id} from {nml_file}"

        for seg in cell.morphology.segments:
            p = cell.get_actual_proximal(seg.id)
            d = seg.distal
            if verbose:
                print(
                    f"\nSegment {seg.name}, id: {seg.id} has proximal point: {p}, distal: {d}"
                )
            width = max(p.diameter, d.diameter)
            if width < min_width:
                width = min_width
            if plot_type == "Constant":
                width = min_width
            fig.add_trace(
                go.Scatter3d(
                    x=[p.x, d.x],
                    y=[p.y, d.y],
                    z=[p.z, d.z],
                    name=None,
                    marker={"size": 2, "color": "blue"},
                    line={"width": width, "color": "blue"},
                    mode="lines",
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

        fig.update_layout(
            title={"text": title},
            hovermode=False,
            plot_bgcolor="white",
            scene=dict(
                xaxis=dict(
                    backgroundcolor="white",
                    showbackground=False,
                    showgrid=False,
                    showspikes=False,
                    title=dict(text="extent (um)"),
                ),
                yaxis=dict(
                    backgroundcolor="white",
                    showbackground=False,
                    showgrid=False,
                    showspikes=False,
                    title=dict(text="extent (um)"),
                ),
                zaxis=dict(
                    backgroundcolor="white",
                    showbackground=False,
                    showgrid=False,
                    showspikes=False,
                    title=dict(text="extent (um)"),
                ),
            ),
        )
        if not nogui:
            fig.show()
        if save_to_file:
            logger.info(
                "Saving image to %s of plot: %s"
                % (os.path.abspath(save_to_file), title)
            )
            fig.write_image(save_to_file, scale=2, width=1024, height=768)
            logger.info("Saved image to %s of plot: %s" % (save_to_file, title))


def plot_2D_cell_morphology(
    offset: typing.List[float] = [0, 0],
    cell: Cell = None,
    plane2d: str = "xy",
    color: typing.Optional[str] = None,
    soma_radius: float = 0.0,
    title: str = "",
    verbose: bool = False,
    fig: matplotlib.figure.Figure = None,
    ax: matplotlib.axes.Axes = None,
    min_width: float = DEFAULTS["minwidth"],
    axis_min_max: typing.List = [float("inf"), -1 * float("inf")],
    scalebar: bool = False,
    nogui: bool = True,
    autoscale: bool = True,
    square: bool = False,
    plot_type: str = "Detailed",
    save_to_file: typing.Optional[str] = None,
    close_plot: bool = False
):
    """Plot the detailed 2D morphology of a cell in provided plane

    :param offset: offset for cell
    :type offset: [float, float]
    :param cell: cell to plot
    :type cell: neuroml.Cell
    :param plane2d: plane to plot on
    :type plane2d: str
    :param color: color to use for all segments
    :type color: str
    :param soma_radius: radius of soma (uses min_width if provided)
    :type soma_radius: float
    :param fig: a matplotlib.figure.Figure object to use
    :type fig: matplotlib.figure.Figure
    :param ax: a matplotlib.axes.Axes object to use
    :type ax: matplotlib.axes.Axes
    :param min_width: minimum width for segments (useful for visualising very
        thin segments): default 0.8um
    :type min_width: float
    :param axis_min_max: min, max value of axes
    :type axis_min_max: [float, float]
    :param title: title of plot
    :type title: str
    :param verbose: show extra information (default: False)
    :type verbose: bool
    :param nogui: do not show matplotlib GUI (default: false)
    :type nogui: bool
    :param save_to_file: optional filename to save generated morphology to
    :type save_to_file: str
    :param square: scale axes so that image is approximately square
    :type square: bool
    :param autoscale: toggle autoscaling
    :type autoscale: bool
    :param scalebar: toggle scalebar
    :type scalebar: bool
    :param close_plot: call pyplot.close() to close plot after plotting
    :type close_plot: bool

    :raises: ValueError if `cell` is None

    """
    if cell is None:
        raise ValueError("No cell provided")

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

    if fig is None:
        fig, ax = get_new_matplotlib_morph_plot(title)

    # random default color
    cell_color = get_next_hex_color()
    if cell is None:
        if soma_radius is None:
            soma_radius = 10

        if plot_type == "Constant":
            soma_radius = min_width

        if plane2d == "xy":
            add_line_to_matplotlib_2D_plot(
                ax,
                [offset[0], offset[0]],
                [offset[1], offset[1]],
                soma_radius,
                cell_color if color is None else color,
                axis_min_max,
            )
        elif plane2d == "yx":
            add_line_to_matplotlib_2D_plot(
                ax,
                [offset[1], offset[1]],
                [offset[0], offset[0]],
                soma_radius,
                cell_color if color is None else color,
                axis_min_max,
            )
        elif plane2d == "xz":
            add_line_to_matplotlib_2D_plot(
                ax,
                [offset[0], offset[0]],
                [offset[2], offset[2]],
                soma_radius,
                cell_color if color is None else color,
                axis_min_max,
            )
        elif plane2d == "zx":
            add_line_to_matplotlib_2D_plot(
                ax,
                [offset[2], offset[2]],
                [offset[0], offset[0]],
                soma_radius,
                cell_color if color is None else color,
                axis_min_max,
            )
        elif plane2d == "yz":
            add_line_to_matplotlib_2D_plot(
                ax,
                [offset[1], offset[1]],
                [offset[2], offset[2]],
                soma_radius,
                cell_color if color is None else color,
                axis_min_max,
            )
        elif plane2d == "zy":
            add_line_to_matplotlib_2D_plot(
                ax,
                [offset[2], offset[2]],
                [offset[1], offset[1]],
                soma_radius,
                cell_color if color is None else color,
                axis_min_max,
            )
        else:
            raise Exception(f"Invalid value for plane: {plane2d}")

    else:
        for seg in cell.morphology.segments:
            p = cell.get_actual_proximal(seg.id)
            d = seg.distal
            width = (p.diameter + d.diameter) / 2

            if width < min_width:
                width = min_width

            if plot_type == "Constant":
                width = min_width

            seg_color = "b"
            if seg.id in soma_segs:
                seg_color = "g"
            elif seg.id in axon_segs:
                seg_color = "r"

            spherical = (
                p.x == d.x and p.y == d.y and p.z == d.z and p.diameter == d.diameter
            )

            if verbose:
                print(
                    "\nSeg %s, id: %s%s has proximal: %s, distal: %s (width: %s, min_width: %s), color: %s"
                    % (
                        seg.name,
                        seg.id,
                        " (spherical)" if spherical else "",
                        p,
                        d,
                        width,
                        min_width,
                        str(seg_color),
                    )
                )

            if plane2d == "xy":
                add_line_to_matplotlib_2D_plot(
                    ax,
                    [offset[0] + p.x, offset[0] + d.x],
                    [offset[1] + p.y, offset[1] + d.y],
                    width,
                    seg_color if color is None else color,
                    axis_min_max,
                )
            elif plane2d == "yx":
                add_line_to_matplotlib_2D_plot(
                    ax,
                    [offset[1] + p.y, offset[1] + d.y],
                    [offset[0] + p.x, offset[0] + d.x],
                    width,
                    seg_color if color is None else color,
                    axis_min_max,
                )
            elif plane2d == "xz":
                add_line_to_matplotlib_2D_plot(
                    ax,
                    [offset[0] + p.x, offset[0] + d.x],
                    [offset[2] + p.z, offset[2] + d.z],
                    width,
                    seg_color if color is None else color,
                    axis_min_max,
                )
            elif plane2d == "zx":
                add_line_to_matplotlib_2D_plot(
                    ax,
                    [offset[2] + p.z, offset[2] + d.z],
                    [offset[0] + p.x, offset[0] + d.x],
                    width,
                    seg_color if color is None else color,
                    axis_min_max,
                )
            elif plane2d == "yz":
                add_line_to_matplotlib_2D_plot(
                    ax,
                    [offset[1] + p.y, offset[1] + d.y],
                    [offset[2] + p.z, offset[2] + d.z],
                    width,
                    seg_color if color is None else color,
                    axis_min_max,
                )
            elif plane2d == "zy":
                add_line_to_matplotlib_2D_plot(
                    ax,
                    [offset[2] + p.z, offset[2] + d.z],
                    [offset[1] + p.y, offset[1] + d.y],
                    width,
                    seg_color if color is None else color,
                    axis_min_max,
                )
            else:
                raise Exception(f"Invalid value for plane: {plane2d}")

            if verbose:
                print("Extent x: %s -> %s" % (axis_min_max[0], axis_min_max[1]))

    if scalebar:
        add_scalebar_to_matplotlib_plot(axis_min_max, ax)
    if autoscale:
        autoscale_matplotlib_plot(verbose, square)

    if save_to_file:
        abs_file = os.path.abspath(save_to_file)
        plt.savefig(abs_file, dpi=200, bbox_inches="tight")
        print(f"Saved image on plane {plane2d} to {abs_file} of plot: {title}")

    if not nogui:
        plt.show()
    if close_plot:
        logger.info("closing plot")
        plt.close()


def plot_2D_schematic(
    cell: Cell,
    segment_groups: typing.Optional[typing.List[SegmentGroup]],
    offset: typing.List[float] = [0, 0],
    labels: bool = False,
    plane2d: str = "xy",
    min_width: float = DEFAULTS["minwidth"],
    verbose: bool = False,
    square: bool = False,
    nogui: bool = False,
    save_to_file: typing.Optional[str] = None,
    scalebar: bool = True,
    autoscale: bool = True,
    fig: matplotlib.figure.Figure = None,
    ax: matplotlib.axes.Axes = None,
    title: str = "",
    close_plot: bool = False,
) -> None:
    """Plot a 2D schematic of the provided segment groups.

    This plots each segment group as a straight line between its first and last
    segment.

    :param offset: offset for cell
    :type offset: [float, float]
    :param cell: cell to plot
    :type cell: neuroml.Cell
    :param segment_groups: list of unbranched segment groups to plot
    :type segment_groups: list(SegmentGroup)
    :param labels: toggle labelling of segment groups
    :type labels: bool
    :param plane2d: what plane to plot (xy/yx/yz/zy/zx/xz)
    :type plane2d: str
    :param min_width: minimum width for segments (useful for visualising very
        thin segments): default 0.8um
    :type min_width: float
    :param verbose: show extra information (default: False)
    :type verbose: bool
    :param square: scale axes so that image is approximately square
    :type square: bool
    :param nogui: do not show matplotlib GUI (default: false)
    :type nogui: bool
    :param save_to_file: optional filename to save generated morphology to
    :type save_to_file: str
    :param fig: a matplotlib.figure.Figure object to use
    :type fig: matplotlib.figure.Figure
    :param ax: a matplotlib.axes.Axes object to use
    :type ax: matplotlib.axes.Axes
    :param title: title of plot
    :type title: str
    :param square: scale axes so that image is approximately square
    :type square: bool
    :param autoscale: toggle autoscaling
    :type autoscale: bool
    :param scalebar: toggle scalebar
    :type scalebar: bool
    :param close_plot: call pyplot.close() to close plot after plotting
    :type close_plot: bool

    """
    if title == "":
        title = f"2D schematic of segment groups from {cell.id}"

    # if no segment groups are given, do them all
    if segment_groups is None:
        segment_groups = []
        for sg in cell.morphology.segment_groups:
            if sg.neuro_lex_id == neuro_lex_ids["section"]:
                segment_groups.append(sg.id)

    ord_segs = cell.get_ordered_segments_in_groups(
        segment_groups, check_parentage=False
    )

    if fig is None:
        logger.debug("No figure provided, creating new fig and ax")
        fig, ax = get_new_matplotlib_morph_plot(title, plane2d)

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
        logger.error(f"Invalid value for plane: {plane2d}")
        sys.exit(-1)

    # use a mutable object so it can be passed as an argument to methods, using
    # float (immuatable) variables requires us to return these from all methods
    axis_min_max = [float("inf"), -1 * float("inf")]
    width = 1

    for sgid, segs in ord_segs.items():
        sgobj = cell.get_segment_group(sgid)
        if sgobj.neuro_lex_id != neuro_lex_ids["section"]:
            raise ValueError(
                f"{sgobj} does not have neuro_lex_id set to indicate it is an unbranched segment"
            )

        # get proximal and distal points
        first_seg = segs[0]  # type: Segment
        last_seg = segs[-1]  # type: Segment

        # unique color for each segment group
        color = get_next_hex_color()

        if plane2d == "xy":
            add_line_to_matplotlib_2D_plot(
                ax,
                [offset[0] + first_seg.proximal.x, offset[0] + last_seg.distal.x],
                [offset[1] + first_seg.proximal.y, offset[1] + last_seg.distal.y],
                width,
                color,
                axis_min_max,
            )
            if labels:
                add_text_to_matplotlib_2D_plot(
                    ax,
                    [offset[0] + first_seg.proximal.x, offset[0] + last_seg.distal.x],
                    [offset[1] + first_seg.proximal.y, offset[1] + last_seg.distal.y],
                    color=color,
                    text=sgid,
                )

        elif plane2d == "yx":
            add_line_to_matplotlib_2D_plot(
                ax,
                [offset[0] + first_seg.proximal.y, offset[0] + last_seg.distal.y],
                [offset[1] + first_seg.proximal.x, offset[1] + last_seg.distal.x],
                width,
                color,
                axis_min_max,
            )
            if labels:
                add_text_to_matplotlib_2D_plot(
                    ax,
                    [offset[0] + first_seg.proximal.y, offset[0] + last_seg.distal.y],
                    [offset[1] + first_seg.proximal.x, offset[1] + last_seg.distal.x],
                    color=color,
                    text=sgid,
                )
        elif plane2d == "xz":
            add_line_to_matplotlib_2D_plot(
                ax,
                [offset[0] + first_seg.proximal.x, offset[0] + last_seg.distal.x],
                [offset[1] + first_seg.proximal.z, offset[1] + last_seg.distal.z],
                width,
                color,
                axis_min_max,
            )
            if labels:
                add_text_to_matplotlib_2D_plot(
                    ax,
                    [offset[0] + first_seg.proximal.x, offset[0] + last_seg.distal.x],
                    [offset[1] + first_seg.proximal.z, offset[1] + last_seg.distal.z],
                    color=color,
                    text=sgid,
                )
        elif plane2d == "zx":
            add_line_to_matplotlib_2D_plot(
                ax,
                [offset[0] + first_seg.proximal.z, offset[0] + last_seg.distal.z],
                [offset[1] + first_seg.proximal.x, offset[1] + last_seg.distal.x],
                width,
                color,
                axis_min_max,
            )
            if labels:
                add_text_to_matplotlib_2D_plot(
                    ax,
                    [offset[0] + first_seg.proximal.z, offset[0] + last_seg.distal.z],
                    [offset[1] + first_seg.proximal.x, offset[1] + last_seg.distal.x],
                    color=color,
                    text=sgid,
                )
        elif plane2d == "yz":
            add_line_to_matplotlib_2D_plot(
                ax,
                [offset[0] + first_seg.proximal.y, offset[0] + last_seg.distal.y],
                [offset[1] + first_seg.proximal.z, offset[1] + last_seg.distal.z],
                width,
                color,
                axis_min_max,
            )
            if labels:
                add_text_to_matplotlib_2D_plot(
                    ax,
                    [offset[0] + first_seg.proximal.y, offset[0] + last_seg.distal.y],
                    [offset[1] + first_seg.proximal.z, offset[1] + last_seg.distal.z],
                    color=color,
                    text=sgid,
                )
        elif plane2d == "zy":
            add_line_to_matplotlib_2D_plot(
                ax,
                [offset[0] + first_seg.proximal.z, offset[0] + last_seg.distal.z],
                [offset[1] + first_seg.proximal.y, offset[1] + last_seg.distal.y],
                width,
                color,
                axis_min_max,
            )
            if labels:
                add_text_to_matplotlib_2D_plot(
                    ax,
                    [offset[0] + first_seg.proximal.z, offset[0] + last_seg.distal.z],
                    [offset[1] + first_seg.proximal.y, offset[1] + last_seg.distal.y],
                    color=color,
                    text=sgid,
                )
        else:
            raise Exception(f"Invalid value for plane: {plane2d}")

        if verbose:
            print("Extent x: %s -> %s" % (axis_min_max[0], axis_min_max[1]))

    if scalebar:
        add_scalebar_to_matplotlib_plot(axis_min_max, ax)
    if autoscale:
        autoscale_matplotlib_plot(verbose, square)

    if save_to_file:
        abs_file = os.path.abspath(save_to_file)
        plt.savefig(abs_file, dpi=200, bbox_inches="tight")
        print(f"Saved image on plane {plane2d} to {abs_file} of plot: {title}")

    if not nogui:
        plt.show()
    if close_plot:
        logger.info("closing plot")
        plt.close()


def plot_segment_groups_curtain_plots(
    cell: Cell,
    segment_groups: typing.List[SegmentGroup],
    labels: bool = False,
    verbose: bool = False,
    nogui: bool = False,
    save_to_file: typing.Optional[str] = None,
    overlay_data: typing.Dict[str, typing.List[typing.Any]] = None,
    overlay_data_label: str = "",
    width: typing.Union[float, int] = 4,
    colormap_name: str = "viridis",
    title: str = "SegmentGroup",
    datamin: typing.Optional[float] = None,
    datamax: typing.Optional[float] = None,
    close_plot: bool = False
) -> None:
    """Plot curtain plots of provided segment groups.

    :param cell: cell to plot
    :type cell: neuroml.Cell
    :param segment_groups: list of unbranched segment groups to plot
    :type segment_groups: list(SegmentGroup)
    :param labels: toggle labelling of segment groups
    :type labels: bool
    :param verbose: show extra information (default: False)
    :type verbose: bool
    :param square: scale axes so that image is approximately square
    :type square: bool
    :param nogui: do not show matplotlib GUI (default: false)
    :type nogui: bool
    :param save_to_file: optional filename to save generated morphology to
    :type save_to_file: str
    :param overlay_data: data to overlay over the curtain plots;
        this must be a dictionary with segment group ids as keys, and lists of
        values to overlay as values. Each list should have a value for every
        segment in the segment group.
    :type overlay_data: dict, keys are segment group ids, values are lists of
        magnitudes to overlay on curtain plots
    :param overlay_data_label: label of data being overlaid
    :type overlay_data_label: str
    :param width: width of each segment group
    :type width: float/int
    :param colormap_name: name of matplotlib colourmap to use for data overlay
        See:
        https://matplotlib.org/stable/api/matplotlib_configuration_api.html#matplotlib.colormaps
        Note: random colours are used for each segment if no data is to be overlaid
    :type colormap_name: str
    :param title: plot title, displayed at bottom
    :type title: str
    :param datamin: min limits of data (useful to compare different plots)
    :type datamin: float
    :param datamax: max limits of data (useful to compare different plots)
    :type datamax: float
    :param close_plot: call pyplot.close() to close plot after plotting
    :type close_plot: bool
    :returns: None

    :raises ValueError: if keys in `overlay_data` do not match
        ids of segment groups of `segment_groups`
    :raises ValueError: if number of items for each key in `overlay_data` does
        not match the number of segments in the corresponding segment group
    """
    # use a random number generator so that the colours are always the same
    myrandom = random.Random()
    myrandom.seed(122436)

    (ord_segs, cumulative_lengths) = cell.get_ordered_segments_in_groups(
        segment_groups, check_parentage=False, include_cumulative_lengths=True
    )

    # plot setup
    fig, ax = plt.subplots(1, 1)  # noqa
    plt.get_current_fig_manager().set_window_title(title)

    # overlaying data related checks
    data_max = -1 * float("inf")
    data_min = float("inf")
    acolormap = None
    norm = None
    if overlay_data:
        if set(overlay_data.keys()) != set(ord_segs.keys()):
            raise ValueError(f"Keys of overlay_data ({overlay_data.keys()}) and ord_segs ({ord_segs.keys()})must match.")
        for key in overlay_data.keys():
            if len(overlay_data[key]) != len(ord_segs[key]):
                raise ValueError(
                    f"Number of values for key {key} does not match in overlay_data({len(overlay_data[key])}) and the segment group ({len(ord_segs[key])})"
                )

            # since lists are of different lengths, one cannot use `numpy.max`
            # on all the values directly
            this_max = numpy.max(list(overlay_data[key]))
            this_min = numpy.min(list(overlay_data[key]))
            if this_max > data_max:
                data_max = this_max
            if this_min < data_min:
                data_min = this_min

        if datamin is not None:
            data_min = datamin
        if datamax is not None:
            data_max = datamax

        acolormap = matplotlib.colormaps[colormap_name]
        norm = matplotlib.colors.Normalize(vmin=data_min, vmax=data_max)
        fig.colorbar(
            matplotlib.cm.ScalarMappable(norm=norm, cmap=acolormap),
            label=overlay_data_label,
        )

    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.yaxis.set_ticks_position("left")
    ax.xaxis.set_ticks_position("none")
    ax.xaxis.set_ticks([])

    ax.set_xlabel(title)
    ax.set_ylabel("length (μm)")

    # column counter
    column = 0
    for sgid, segs in ord_segs.items():
        column += 1
        length = 0

        cumulative_lengths_sg = cumulative_lengths[sgid]

        sgobj = cell.get_segment_group(sgid)
        if sgobj.neuro_lex_id != neuro_lex_ids["section"]:
            raise ValueError(
                f"{sgobj} does not have neuro_lex_id set to indicate it is an unbranched segment"
            )

        for seg_num in range(0, len(segs)):
            seg = segs[seg_num]
            cumulative_len = cumulative_lengths_sg[seg_num]

            if overlay_data and acolormap and norm:
                color = acolormap(norm(overlay_data[sgid][seg_num]))
            else:
                color = get_next_hex_color(myrandom)

            logger.debug(f"color is {color}")

            add_box_to_matplotlib_2D_plot(
                ax,
                [column * width - width * 0.10, -1 * length],
                height=cumulative_len,
                width=width * 0.8,
                color=color,
            )

            length += cumulative_len

        if labels:
            add_text_to_matplotlib_2D_plot(
                ax,
                [column * width + width / 2, column * width + width / 2],
                [50, 100],
                color="black",
                text=sgid,
                vertical="bottom",
                horizontal="center",
                clip_on=False,
            )

    plt.autoscale()
    xl = plt.xlim()
    yl = plt.ylim()
    if verbose:
        print("Auto limits - x: %s , y: %s" % (xl, yl))

    plt.ylim(top=0)
    ax.set_yticklabels(abs(ax.get_yticks()))

    if save_to_file:
        abs_file = os.path.abspath(save_to_file)
        plt.savefig(abs_file, dpi=200, bbox_inches="tight")
        print(f"Saved image to {abs_file} of plot: {title}")

    if not nogui:
        plt.show()
    if close_plot:
        logger.info("Closing plot")
        plt.close()


if __name__ == "__main__":
    main()
