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

from matplotlib import pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar
import plotly.graph_objects as go

from pyneuroml.pynml import read_neuroml2_file
from pyneuroml.utils.cli import build_namespace


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


DEFAULTS = {
    "v": False,
    "nogui": False,
    "saveToFile": None,
    "interactive3d": False,
    "plane2d": "xy",
    "minwidth": 0,
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
        plot_2D(a.nml_file, a.plane2d, a.minwidth, a.v, a.nogui, a.save_to_file)

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
    save_to_file: typing.Optional[str] = None
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
    """

    if verbose:
        print("Plotting %s" % nml_file)

    nml_model = read_neuroml2_file(nml_file)

    for cell in nml_model.cells:

        title = "2D plot of %s from %s" % (cell.id, nml_file)

        fig, ax = plt.subplots(1, 1)  # noqa
        plt.get_current_fig_manager().set_window_title(title)

        ax.set_aspect("equal")

        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        ax.yaxis.set_ticks_position("left")
        ax.xaxis.set_ticks_position("bottom")


        if plane2d == "xy":
            ax.set_xlabel("x (um)")
            ax.set_ylabel("y (um)")
        elif plane2d == "yx":
            ax.set_xlabel("y (um)")
            ax.set_ylabel("x (um)")
        elif plane2d == "xz":
            ax.set_xlabel("x (um)")
            ax.set_ylabel("z (um)")
        elif plane2d == "zx":
            ax.set_xlabel("z (um)")
            ax.set_ylabel("x (um)")
        elif plane2d == "yz":
            ax.set_xlabel("y (um)")
            ax.set_ylabel("z (um)")
        elif plane2d == "zy":
            ax.set_xlabel("z (um)")
            ax.set_ylabel("y (um)")
        else:
            logger.error(f"Invalid value for plane: {plane2d}")
            sys.exit(-1)

        for seg in cell.morphology.segments:
            p = cell.get_actual_proximal(seg.id)
            d = seg.distal
            width = (p.diameter + d.diameter)/2
            if verbose:
                print(
                    "\nSegment %s, id: %s has proximal point: %s, distal: %s (so width: %s)"
                    % (seg.name, seg.id, p, d, width)
                )
            if width < min_width:
                width = min_width

            max_xaxis = -1*float('inf')
            min_xaxis = float('inf')

            if p.x ==  d.x and p.y == d.y and p.z == d.z and p.diameter == d.diameter:
                if verbose: print("Segment is spherical")
                ax.add_line(LineDataUnits([p.x+width/1000., d.x], [p.y, d.y+width/1000.], linewidth=width, solid_capstyle='round',color='r'))
            else:
                if plane2d == "xy":
                    add_line(ax, [p.x, d.x], [p.y, d.y], width, min_xaxis, max_xaxis)
                    '''
                    ax.add_line(LineDataUnits([p.x, d.x], [p.y, d.y], linewidth=width, solid_capstyle='butt'))
                    min_xaxis=min(min_xaxis,p.x)
                    min_xaxis=min(min_xaxis,d.x)
                    max_xaxis=max(max_xaxis,p.x)
                    max_xaxis=max(max_xaxis,d.x)'''
                elif plane2d == "yx":
                    ax.add_line(LineDataUnits([p.y, d.y], [p.x, d.x], linewidth=width, solid_capstyle='butt'))
                elif plane2d == "xz":
                    ax.add_line(LineDataUnits([p.x, d.x], [p.z, d.z], linewidth=width, solid_capstyle='butt'))
                elif plane2d == "zx":
                    ax.add_line(LineDataUnits([p.z, d.z], [p.x, d.x], linewidth=width, solid_capstyle='butt'))
                elif plane2d == "yz":
                    ax.add_line(LineDataUnits([p.y, d.y], [p.z, d.z], linewidth=width, solid_capstyle='butt'))
                elif plane2d == "zy":
                    ax.add_line(LineDataUnits([p.z, d.z], [p.y, d.y], linewidth=width, solid_capstyle='butt'))
                else:
                    logger.error(f"Invalid value for plane: {plane2d}")
                    sys.exit(-1)

        print('Extent x: %s -> %s'%(min_xaxis, max_xaxis))
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

    if save_to_file:
        abs_file = os.path.abspath(save_to_file)
        plt.savefig(abs_file, dpi=200, bbox_inches="tight")
        print(f"Saved image on plane {plane2d} to {abs_file} of plot: {title}")

    if not nogui:
        plt.show()

def add_line(ax, xv, yv, width, min_xaxis, max_xaxis):

    ax.add_line(LineDataUnits(xv, yv, linewidth=width, solid_capstyle='butt'))
    min_xaxis=min(min_xaxis,xv[0])
    min_xaxis=min(min_xaxis,xv[1])
    max_xaxis=max(max_xaxis,yv[0])
    max_xaxis=max(max_xaxis,yv[1])
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
            width = max(p.diameter, d.diameter)
            if width < min_width:
                width = min_width
            fig.add_trace(go.Scatter3d(
                x=[p.x, d.x], y=[p.y, d.y], z=[p.z, d.z],
                name=None,
                marker={"size": 2, "color": "blue"},
                line={"width": width, "color": "blue"},
                mode="lines",
                showlegend=False,
                hoverinfo="skip"
            ))

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


if __name__ == "__main__":
    main()
