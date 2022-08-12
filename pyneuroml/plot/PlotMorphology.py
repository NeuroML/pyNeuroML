#!/usr/bin/env python3
"""
Utilities to plot NeuroML2 cell morphologies.

File: pyneuroml/plot/PlotMorphology.py

Copyright 2022 NeuroML contributors
"""


import argparse
import os
import sys

import typing
import logging

import numpy as np
from matplotlib import pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar
import plotly.graph_objects as go

from pyneuroml.pynml import read_neuroml2_file
from pyneuroml.utils.cli import build_namespace

import neuroml


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


DEFAULTS = {
    "v": False,
    "nogui": False,
    "saveToFile": None,
    "interactive3d": False,
    "plane2d": "xy",
    "minwidth": 0,
    "square": False,
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
    :param **kwargs: other arguments
    """
    a = build_namespace(DEFAULTS, a, **kwargs)
    print(a)
    if a.interactive3d:
        plot_interactive_3D(a.nml_file, a.minwidth, a.v, a.nogui, a.save_to_file)
    else:
        plot_2D(a.nml_file, a.plane2d, a.minwidth, a.v, a.nogui, a.save_to_file, a.square)

##########################################################################################
# Taken from https://stackoverflow.com/questions/19394505/expand-the-line-with-specified-width-in-data-unit
from matplotlib.lines import Line2D

class LineDataUnits(Line2D):
    def __init__(self, *args, **kwargs):
        _lw_data = kwargs.pop("linewidth", 1)
        super().__init__(*args, **kwargs)
        self._lw_data = _lw_data

    def _get_lw(self):
        if self.axes is not None:
            ppd = 72./self.axes.figure.dpi
            trans = self.axes.transData.transform
            return ((trans((1, self._lw_data))-trans((0, 0)))*ppd)[1]
        else:
            return 1

    def _set_lw(self, lw):
        self._lw_data = lw

    _linewidth = property(_get_lw, _set_lw)

##########################################################################################

def plot_2D(
    nml_file: str,
    plane2d: str = "xy",
    min_width: float = DEFAULTS["minwidth"],
    verbose: bool = False,
    nogui: bool = False,
    save_to_file: typing.Optional[str] = None,
    square: bool = False
):
    """Plot cell morphology in 2D.

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
    """

    if verbose:
        print("Plotting %s" % nml_file)

    nml_model = read_neuroml2_file(nml_file,
                        include_includes=True,
                        check_validity_pre_include=False,
                        verbose=False,
                        optimized=True,)


    from pyneuroml.utils import extract_position_info

    cell_id_vs_cell, pop_id_vs_cell, positions, pop_id_vs_color, pop_id_vs_radii = extract_position_info(nml_model, verbose)

    title = "2D plot of %s from %s" % (nml_model.networks[0].id, nml_file)

    if verbose:
        print("positions: %s"%positions)
        print("pop_id_vs_cell: %s"%pop_id_vs_cell)
        print("cell_id_vs_cell: %s"%cell_id_vs_cell)
        print("pop_id_vs_color: %s"%pop_id_vs_color)
        print("pop_id_vs_radii: %s"%pop_id_vs_radii)

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
        logger.error(f"Invalid value for plane: {plane2d}")
        sys.exit(-1)

    max_xaxis = -1*float('inf')
    min_xaxis = float('inf')

    for pop_id in pop_id_vs_cell:
        cell = pop_id_vs_cell[pop_id]
        pos_pop = positions[pop_id]

        for cell_index in pos_pop:
            pos = pos_pop[cell_index]

            try:
                soma_segs = cell.get_all_segments_in_group('soma_group')
            except:
                soma_segs = []
            try:
                dend_segs = cell.get_all_segments_in_group('dendrite_group')
            except:
                dend_segs = []
            try:
                axon_segs = cell.get_all_segments_in_group('axon_group')
            except:
                axon_segs = []

            if cell is None:

                radius = pop_id_vs_radii[pop_id] if pop_id in pop_id_vs_radii else 10
                color = 'b'
                if pop_id in pop_id_vs_color:
                    color = pop_id_vs_color[pop_id]

                if plane2d == "xy":
                    min_xaxis, max_xaxis = add_line(ax, [pos[0], pos[0]], [pos[1], pos[1]], radius, color, min_xaxis, max_xaxis)
                elif plane2d == "yx":
                    min_xaxis, max_xaxis = add_line(ax, [pos[1], pos[1]], [pos[0], pos[0]], radius, color, min_xaxis, max_xaxis)
                elif plane2d == "xz":
                    min_xaxis, max_xaxis = add_line(ax, [pos[0], pos[0]], [pos[2], pos[2]], radius, color, min_xaxis, max_xaxis)
                elif plane2d == "zx":
                    min_xaxis, max_xaxis = add_line(ax, [pos[2], pos[2]], [pos[0], pos[0]], radius, color, min_xaxis, max_xaxis)
                elif plane2d == "yz":
                    min_xaxis, max_xaxis = add_line(ax, [pos[1], pos[1]], [pos[2], pos[2]], radius, color, min_xaxis, max_xaxis)
                elif plane2d == "zy":
                    min_xaxis, max_xaxis = add_line(ax, [pos[2], pos[2]], [pos[1], pos[1]], radius, color, min_xaxis, max_xaxis)
                else:
                    raise Exception(f"Invalid value for plane: {plane2d}")

            else:

                for seg in cell.morphology.segments:
                    p = cell.get_actual_proximal(seg.id)
                    d = seg.distal
                    width = (p.diameter + d.diameter)/2

                    if width < min_width:
                        width = min_width

                    color = 'b'
                    if pop_id in pop_id_vs_color:
                        color = pop_id_vs_color[pop_id]
                    else:
                        if seg.id in soma_segs: color = 'g'
                        if seg.id in axon_segs: color = 'r'

                    spherical = p.x ==  d.x and p.y == d.y and p.z == d.z and p.diameter == d.diameter

                    if verbose:
                        print(
                            "\nSeg %s, id: %s%s has proximal: %s, distal: %s (width: %s, min_width: %s), color: %s"
                            % (seg.name, seg.id, ' (spherical)' if spherical else '', p, d, width, min_width, str(color))
                        )


                    if plane2d == "xy":
                        min_xaxis, max_xaxis = add_line(ax, [pos[0]+p.x, pos[0]+d.x], [pos[1]+p.y, pos[1]+d.y], width, color, min_xaxis, max_xaxis)
                    elif plane2d == "yx":
                        min_xaxis, max_xaxis = add_line(ax, [pos[1]+p.y, pos[1]+d.y], [pos[0]+p.x, pos[0]+d.x], width, color, min_xaxis, max_xaxis)
                    elif plane2d == "xz":
                        min_xaxis, max_xaxis = add_line(ax, [pos[0]+p.x, pos[0]+d.x], [pos[2]+p.z, pos[2]+d.z], width, color, min_xaxis, max_xaxis)
                    elif plane2d == "zx":
                        min_xaxis, max_xaxis = add_line(ax, [pos[2]+p.z, pos[2]+d.z], [pos[0]+p.x, pos[0]+d.x], width, color, min_xaxis, max_xaxis)
                    elif plane2d == "yz":
                        min_xaxis, max_xaxis = add_line(ax, [pos[1]+p.y, pos[1]+d.y], [pos[2]+p.z, pos[2]+d.z], width, color, min_xaxis, max_xaxis)
                    elif plane2d == "zy":
                        min_xaxis, max_xaxis = add_line(ax, [pos[2]+p.z, pos[2]+d.z], [pos[1]+p.y, pos[1]+d.y], width, color, min_xaxis, max_xaxis)
                    else:
                        raise Exception(f"Invalid value for plane: {plane2d}")

                    if verbose: print('Extent x: %s -> %s'%(min_xaxis, max_xaxis))

        # add a scalebar
        # ax = fig.add_axes([0, 0, 1, 1])
        sc_val = 50
        if max_xaxis-min_xaxis<100:
            sc_val = 5
        if max_xaxis-min_xaxis<10:
            sc_val = 1
        scalebar1 = ScaleBar(0.001, units="mm", dimension="si-length",
                             scale_loc="top", location="lower right",
                             fixed_value=sc_val, fixed_units="um", box_alpha=.8)
        ax.add_artist(scalebar1)

        plt.autoscale()
        xl = plt.xlim()
        yl = plt.ylim()
        if verbose: print('Auto limits - x: %s , y: %s'%(xl, yl))

        small = 0.1
        if xl[1]-xl[0]<small and yl[1]-yl[0]<small: # i.e. only a point
            plt.xlim([-100,100])
            plt.ylim([-100,100])
        elif xl[1]-xl[0]<small:
            d_10 = (yl[1]-yl[0])/10
            m = xl[0] + (xl[1]-xl[0])/2.
            plt.xlim([m-d_10,m+d_10])
        elif yl[1]-yl[0]<small:
            d_10 = (xl[1]-xl[0])/10
            m = yl[0] + (yl[1]-yl[0])/2.
            plt.ylim([m-d_10,m+d_10])

        if square:
            if xl[1]-xl[0]>yl[1]-yl[0]:
                d2 = (xl[1]-xl[0])/2
                m = yl[0] + (yl[1]-yl[0])/2.
                plt.ylim([m-d2,m+d2])

            if xl[1]-xl[0]<yl[1]-yl[0]:
                d2 = (yl[1]-yl[0])/2
                m = xl[0] + (xl[1]-xl[0])/2.
                plt.xlim([m-d2,m+d2])




    if save_to_file:
        abs_file = os.path.abspath(save_to_file)
        plt.savefig(abs_file, dpi=200, bbox_inches="tight")
        print(f"Saved image on plane {plane2d} to {abs_file} of plot: {title}")

    if not nogui:
        plt.show()

def add_line(ax, xv, yv, width, color, min_xaxis, max_xaxis):

    if abs(xv[0]-xv[1])<0.01 and abs(yv[0]-yv[1])<0.01: # looking at the cylinder from the top, OR a sphere, so draw a circle
        xv[1]=xv[1]+width/1000.
        yv[1]=yv[1]+width/1000.

        ax.add_line(LineDataUnits(xv, yv, linewidth=width, solid_capstyle='round',color=color))

    ax.add_line(LineDataUnits(xv, yv, linewidth=width, solid_capstyle='butt', color=color))

    min_xaxis=min(min_xaxis,xv[0])
    min_xaxis=min(min_xaxis,xv[1])
    max_xaxis=max(max_xaxis,xv[0])
    max_xaxis=max(max_xaxis,xv[1])
    return min_xaxis, max_xaxis

def plot_interactive_3D(
    nml_file: str,
    min_width: float = 0.8,
    verbose: bool = False,
    nogui: bool = False,
    save_to_file: typing.Optional[str] = None
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
    """
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
            (X, Y, Z) = get_cylinder_surface(p.x, p.y, p.z, p.diameter / 2, d.x, d.y, d.z, d.diameter / 2, 20)
            fig.add_trace(go.Surface(x=X, y=Y, z=Z, surfacecolor=(len(X) * len(Y) * ["blue"])))

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
                    title=dict(
                        text="extent (um)"
                    )
                ),
                yaxis=dict(
                    backgroundcolor="white",
                    showbackground=False,
                    showgrid=False,
                    showspikes=False,
                    title=dict(
                        text="extent (um)"
                    )
                ),
                zaxis=dict(
                    backgroundcolor="white",
                    showbackground=False,
                    showgrid=False,
                    showspikes=False,
                    title=dict(
                        text="extent (um)"
                    )
                )

            )
        )
        if not nogui:
            fig.show()
        if save_to_file:
            logger.info(
                "Saving image to %s of plot: %s" %
                (os.path.abspath(save_to_file), title)
            )
            fig.write_image(save_to_file, scale=2, width=1024, height=768)
            logger.info("Saved image to %s of plot: %s" % (save_to_file, title))


def get_sphere_surface(
    x: float, y: float, z: float, radius: float, resolution: int = 20
) -> typing.Any:
    """Get surface points of a sphere centered at x, y, z with radius.

    Reference: https://stackoverflow.com/a/71053527/375067

    :param x: center x
    :type x: float
    :param y: center y
    :type y: float
    :param z: center z
    :type z: float
    :param radius: radius of sphere
    :type radius: float
    :param resolution: resolution (number of points in the surface)
    :type resolution: int
    :returns: list of [x, y, z] values


    """
    u, v = np.mgrid[0:2 * np.pi:resolution * 2j, 0:np.pi:resolution * 1j]  # noqa
    X = radius * np.cos(u) * np.sin(v) + x
    Y = radius * np.sin(u) * np.sin(v) + y
    Z = radius * np.cos(v) + z

    fig = go.Figure()
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, surfacecolor=(len(Z) * ["blue"])))
    fig.show()

    return (X, Y, Z)


def get_cylinder_surface(
    x1: float, y1: float, z1: float,
    radius1: float,
    x2: float, y2: float, z2: float,
    radius2: typing.Optional[float] = None,
    resolution: int = 20,
    angular_resolution: int = 15
) -> typing.Any:
    """Get surface points of a cylinder centered at x, y, z with radius.

    Reference: https://stackoverflow.com/a/32383775/375067

    :param x1: proximal center x
    :type x1: float
    :param y1: proximal center y
    :type y1: float
    :param z1: proximal center z
    :type z1: float
    :param radius1: proximal of cylinder
    :type radius1: float
    :param x1: distal center x
    :type x1: float
    :param y1: distal center y
    :type y1: float
    :param z1: distal center z
    :type z1: float
    :param radius2: distal of cylinder
    :type radius2: float
    :param resolution: resolution (number of points in the surface)
    :type resolution: int
    :param angular_resolution: resolution (number of angles for drawing the surface)
        More angles would result in a smoother surface, but also in a heavier
        (and so possibly slower) plot
    :type angular_resolution: int
    :returns: list of [x, y, z] values

    """

    print(f"Got: {x1}, {y1}, {z1}, {radius1} -> {x2}, {y2}, {z2}, {radius2}")

    radius = radius1
    p1 = np.array([x1, y1, z1])
    p2 = np.array([x2, y2, z2])
    axis_vector = p2 - p1
    axis_mag = np.linalg.norm(axis_vector)

    axis_unit_vector = axis_vector / axis_mag

    somev = np.array([1, 0, 0])
    if (axis_unit_vector == somev).all():
        somev = np.array([0, 1, 0])

    perpv1 = np.cross(axis_unit_vector, somev)
    perpv1_unit = perpv1 / np.linalg.norm(perpv1)
    perpv2_unit = np.cross(axis_unit_vector, perpv1_unit)

    t = np.linspace(0, axis_mag, resolution)
    theta = np.linspace(0, 2 * np.pi, angular_resolution)

    t_grid, theta_grid = np.meshgrid(t, theta)

    X, Y, Z = [p1[i] + axis_unit_vector[i] * t_grid + radius * np.sin(theta_grid) * perpv1_unit[i] + radius * np.cos(theta_grid) * perpv2_unit[i] for i in [0, 1, 2]]

    return X, Y, Z


if __name__ == "__main__":
    main()
