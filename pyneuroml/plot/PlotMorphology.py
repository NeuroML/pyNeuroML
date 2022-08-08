#!/usr/bin/env python3
"""
Utilities to plot NeuroML2 cell morphologies.

File: pyneuroml/plot/PlotMorphology.py

Copyright 2022 NeuroML contributors
"""


import argparse
import os

import typing
import logging

from matplotlib import pyplot as plt
from matplotlib import rcParams

from pyneuroml.utils.cli import build_namespace


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


DEFAULTS = {
    "v": False,
    "nogui": False,
    "saveToFile": None,
    "interactive3d": False,
    "plane2d": "xy",
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
        action="store_true",
        default=DEFAULTS["plane2d"],
        help="Plane to plot on for 2D plot",
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
        plot_interactive_3D(a.nml_file, a.v, a.nogui, a.save_to_file)
    else:
        plot_2D(a.nml_file, a.plane2d, a.v, a.nogui, a.save_to_file)


def plot_2D(
    nml_file: str,
    plane2d: str = "xy",
    verbose: bool = False,
    nogui: bool = False,
    save_to_file: typing.Optional[str] = None
):
    """Plot cell morphology in 2D.

    This uses matplotlib to plot the morphology in 2D.

    :param nml_file: path to NeuroML cell file
    :type nml_file: str
    :param verbose: show extra information (default: False)
    :type verbose: bool
    :param nogui: do not show matplotlib GUI (default: false)
    :type nogui: bool
    :param save_to_file: optional filename to save generated morphology to
    :type save_to_file: str
    """

    if verbose:
        print("Plotting %s" % nml_file)

    from pyneuroml.pynml import read_neuroml2_file

    nml_model = read_neuroml2_file(nml_file)

    for cell in nml_model.cells:

        title = "2D plot of %s from %s" % (cell.id, nml_file)

        fig = plt.figure()  # noqa
        plt.axes().set_aspect("equal")

        plt.get_current_fig_manager().set_window_title(title)

        for seg in cell.morphology.segments:
            p = cell.get_actual_proximal(seg.id)
            d = seg.distal
            if verbose:
                print(
                    "\nSegment %s, id: %s has proximal point: %s, distal: %s"
                    % (seg.name, seg.id, p, d)
                )
            width = max(p.diameter, d.diameter)
            if plane2d == "xy":
                plt.plot([p.x, d.x], [p.y, d.y], linewidth=width, color="b")
            elif plane2d == "xz":
                plt.plot([p.x, d.x], [p.z, d.z], linewidth=width, color="b")
            else:
                plt.plot([p.y, d.y], [p.z, d.z], linewidth=width, color="b")

    if save_to_file:
        abs_file = os.path.abspath(save_to_file)
        plt.savefig(abs_file, bbox_inches="tight")
        print(f"Saved image on plane {plane2d} to {abs_file} of plot: {title}")

    if not nogui:
        plt.show()


def plot_interactive_3D(
    nml_file: str,
    verbose: bool = False,
    nogui: bool = False,
    save_to_file: typing.Optional[str] = None
):
    """Plot NeuroML2 cell morphology interactively using Plot.ly

    :param nml_file: path to NeuroML cell file
    :type nml_file: str
    :param verbose: show extra information (default: False)
    :type verbose: bool
    :param nogui: do not show matplotlib GUI (default: false)
    :type nogui: bool
    :param save_to_file: optional filename to save generated morphology to
    :type save_to_file: str
    """
    pass


if __name__ == "__main__":
    main()
