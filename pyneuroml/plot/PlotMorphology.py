#!/usr/bin/env python3
"""
Utilities to plot NeuroML2 cell morphologies.

File: pyneuroml/plot/PlotMorphology.py

Copyright 2023 NeuroML contributors
"""

import argparse
import logging
import os
import random
import sys
import typing
from typing import Optional

import matplotlib
import numpy
from matplotlib import pyplot as plt
from neuroml import Cell, NeuroMLDocument, SegmentGroup
from neuroml.neuro_lex_ids import neuro_lex_ids

from pyneuroml.pynml import read_neuroml2_file
from pyneuroml.utils import extract_position_info
from pyneuroml.utils.cli import build_namespace
from pyneuroml.utils.plot import (
    DEFAULTS,
    add_box_to_matplotlib_2D_plot,
    add_line_to_matplotlib_2D_plot,
    add_scalebar_to_matplotlib_plot,
    add_text_to_matplotlib_2D_plot,
    autoscale_matplotlib_plot,
    get_new_matplotlib_morph_plot,
    get_next_hex_color,
    load_minimal_morphplottable__model,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
        "-pointFraction",
        type=str,
        metavar="<fraction of each population to plot as point cells>",
        default=DEFAULTS["pointFraction"],
        help="Fraction of network to plot as point cells",
    )
    parser.add_argument(
        "-plotType",
        type=str,
        metavar="<type: detailed, constant, schematic, or point>",
        default=DEFAULTS["plotType"],
        help="Level of detail to plot in",
    )
    parser.add_argument(
        "-theme",
        type=str,
        metavar="<theme: light, dark>",
        default=DEFAULTS["theme"],
        help="Theme to use for interactive 3d plotting (not used for 2d plotting)",
    )
    parser.add_argument(
        "-minWidth",
        type=float,
        metavar="<min width of lines>",
        default=DEFAULTS["minWidth"],
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
        help="Name of the image file, for 2D plot",
    )

    parser.add_argument(
        "-square",
        action="store_true",
        default=DEFAULTS["square"],
        help="Scale axes so that image is approximately square, for 2D plot",
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
    logger.debug(a)
    if a.interactive3d:
        from pyneuroml.plot.PlotMorphologyVispy import plot_interactive_3D

        plot_interactive_3D(
            nml_file=a.nml_file,
            min_width=a.min_width,
            verbose=a.v,
            plot_type=a.plot_type,
            theme=a.theme,
            plot_spec={"point_fraction": a.point_fraction},
        )
    else:
        plot_2D(
            a.nml_file,
            a.plane2d,
            a.min_width,
            a.v,
            a.nogui,
            a.save_to_file,
            a.square,
            a.plot_type,
            plot_spec={"point_fraction": a.point_fraction},
        )


def plot_2D(
    nml_file: typing.Union[str, NeuroMLDocument, Cell],
    plane2d: str = "xy",
    min_width: float = DEFAULTS["minWidth"],  # noqa
    verbose: bool = False,
    nogui: bool = False,
    save_to_file: typing.Optional[str] = None,
    square: bool = False,
    plot_type: str = "detailed",
    title: typing.Optional[str] = None,
    close_plot: bool = False,
    plot_spec: typing.Optional[
        typing.Dict[str, typing.Union[str, typing.List[int], float]]
    ] = None,
    highlight_spec: typing.Optional[typing.Dict[typing.Any, typing.Any]] = None,
):
    """Plot cells in a 2D plane.

    If a file with a network containing multiple cells is provided, it will
    plot all the cells. For detailed neuroml.Cell types, it will plot their
    complete morphology. For point neurons, we only plot the points (locations)
    where they are.

    This method uses matplotlib.

    .. versionadded:: 1.1.12
        The hightlight_spec parameter


    :param nml_file: path to NeuroML cell file, or a NeuroMLDocument object
    :type nml_file: str or :py:class:`neuroml.NeuroMLDocument` or
        :py:class:`neuroml.Cell`
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
    :param close_plot: call pyplot.close() to close plot after plotting
    :type close_plot: bool
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
        - marker_size: width of the marker

        E.g.:

        .. code-block:: python

            {
                "cell id1": {
                    "seg id1": {
                        "marker_color": "blue",
                        "marker_size": 10
                    }
                }
            }

    :type highlight_spec: dict
    """

    if plot_type not in ["detailed", "constant", "schematic", "point"]:
        raise ValueError(
            "plot_type must be one of 'detailed', 'constant', 'schematic', 'point'"
        )

    if highlight_spec is None:
        highlight_spec = {}

    if verbose:
        print("Plotting %s" % nml_file)

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

    if verbose:
        logger.debug(f"positions: {positions}")
        logger.debug(f"pop_id_vs_cell: {pop_id_vs_cell}")
        logger.debug(f"cell_id_vs_cell: {cell_id_vs_cell}")
        logger.debug(f"pop_id_vs_color: {pop_id_vs_color}")
        logger.debug(f"pop_id_vs_radii: {pop_id_vs_radii}")

    # not used, clear up
    del cell_id_vs_cell

    fig, ax = get_new_matplotlib_morph_plot(title, plane2d)
    axis_min_max = [float("inf"), -1 * float("inf")]

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
        pos_pop = positions[pop_id]  # type: typing.Dict[typing.Any, typing.List[float]]

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

            if cell is None:
                plot_2D_point_cells(
                    offset=pos,
                    plane2d=plane2d,
                    color=color,
                    soma_radius=radius,
                    verbose=verbose,
                    ax=ax,
                    fig=fig,
                    autoscale=False,
                    scalebar=False,
                    nogui=True,
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
                    plot_2D_point_cells(
                        offset=pos1,
                        plane2d=plane2d,
                        color=color,
                        soma_radius=radius,
                        verbose=verbose,
                        ax=ax,
                        fig=fig,
                        autoscale=False,
                        scalebar=False,
                        nogui=True,
                    )
                elif plot_type == "schematic" or cell.id in schematic_cells:
                    plot_2D_schematic(
                        offset=pos,
                        cell=cell,
                        segment_groups=None,
                        labels=False,
                        plane2d=plane2d,
                        verbose=verbose,
                        fig=fig,
                        ax=ax,
                        scalebar=False,
                        nogui=True,
                        autoscale=False,
                        square=False,
                    )
                elif (
                    plot_type == "detailed"
                    or cell.id in detailed_cells
                    or plot_type == "constant"
                    or cell.id in constant_cells
                ):
                    cell_highlight_spec = {}
                    try:
                        cell_highlight_spec = highlight_spec[cell.id]
                    except KeyError:
                        pass
                    plot_2D_cell_morphology(
                        offset=pos,
                        cell=cell,
                        plane2d=plane2d,
                        color=color,
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
                        highlight_spec=cell_highlight_spec,
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


def plot_2D_cell_morphology(
    offset: typing.List[float] = [0, 0],
    cell: Optional[Cell] = None,
    plane2d: str = "xy",
    color: typing.Optional[str] = None,
    title: str = "",
    verbose: bool = False,
    fig: Optional[matplotlib.figure.Figure] = None,
    ax: Optional[matplotlib.axes.Axes] = None,
    min_width: float = DEFAULTS["minWidth"],
    axis_min_max: typing.List = [float("inf"), -1 * float("inf")],
    scalebar: bool = False,
    nogui: bool = True,
    autoscale: bool = True,
    square: bool = False,
    plot_type: str = "detailed",
    save_to_file: typing.Optional[str] = None,
    close_plot: bool = False,
    overlay_data: typing.Optional[typing.Dict[int, float]] = None,
    overlay_data_label: typing.Optional[str] = None,
    datamin: typing.Optional[float] = None,
    datamax: typing.Optional[float] = None,
    colormap_name: str = "viridis",
    highlight_spec: typing.Optional[typing.Dict[typing.Any, typing.Any]] = None,
):
    """Plot the detailed 2D morphology of a cell in provided plane.

    The method can also overlay data onto the morphology.

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
    :param plane2d: plane to plot on
    :type plane2d: str
    :param color: color to use for all segments
    :type color: str
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
    :param overlay_data: data to overlay over the morphology
        this must be a dictionary with segment ids as keys, the single value to
        overlay as values
    :type overlay_data: dict, keys are segment ids, values are magnitudes to
        overlay on curtain plots
    :param overlay_data_label: label of data being overlaid
    :type overlay_data_label: str
    :param colormap_name: name of matplotlib colourmap to use for data overlay
        See:
        https://matplotlib.org/stable/api/matplotlib_configuration_api.html#matplotlib.colormaps
        Note: random colours are used for each segment if no data is to be overlaid
    :type colormap_name: str
    :param datamin: min limits of data (useful to compare different plots)
    :type datamin: float
    :param datamax: max limits of data (useful to compare different plots)
    :type datamax: float
    :param highlight_spec: dictionary that allows passing some
        specifications to allow highlighting of particular elements. Mostly
        only helpful for marking segments on multi-compartmental cells. In the
        main dictionary are more dictionaries, one for each segment id (as
        string or integer) which will be the key:

        - marker_color: color of the marker
        - marker_size: width of the marker

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

    if fig is None:
        fig, ax = get_new_matplotlib_morph_plot(title)

    # overlaying data
    data_max = -1 * float("inf")
    data_min = float("inf")
    acolormap = None
    norm = None
    if overlay_data:
        this_max = numpy.max(list(overlay_data.values()))
        this_min = numpy.min(list(overlay_data.values()))
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
        if data_min == data_max:
            fig.colorbar(
                matplotlib.cm.ScalarMappable(norm=norm, cmap=acolormap),
                label=overlay_data_label,
                ax=ax,
                ticks=[data_min],
            )
        else:
            fig.colorbar(
                matplotlib.cm.ScalarMappable(norm=norm, cmap=acolormap),
                label=overlay_data_label,
                ax=ax,
            )

    # random default color
    for seg in cell.morphology.segments:
        p = cell.get_actual_proximal(seg.id)
        d = seg.distal
        width = (p.diameter + d.diameter) / 2

        segment_spec = {
            "marker_size": None,
            "marker_color": None,
        }
        try:
            segment_spec.update(highlight_spec[str(seg.id)])
        # if there's no spec for this segment
        except KeyError:
            logger.debug("No segment highlight spec found for segment" + str(seg.id))
        # Also check if segment ids are provided as ints
        try:
            segment_spec.update(highlight_spec[seg.id])
        # if there's no spec for this segment
        except KeyError:
            logger.debug("No segment highlight spec found for segment" + str(seg.id))

        logger.debug("segment_spec for " + str(seg.id) + " is" + str(segment_spec))

        if width < min_width:
            width = min_width

        if plot_type == "constant":
            width = min_width

        if segment_spec["marker_size"] is not None:
            width = float(segment_spec["marker_size"])

        if overlay_data and acolormap and norm:
            try:
                seg_color: typing.Union[
                    str, typing.Tuple[float, float, float, float]
                ] = acolormap(norm(overlay_data[seg.id]))
            except KeyError:
                seg_color = "black"
        else:
            if seg.id in soma_segs:
                seg_color = "g"
            elif seg.id in axon_segs:
                seg_color = "r"
            elif seg.id in dend_segs:
                seg_color = "b"
            # default is also blue
            else:
                seg_color = "b"

        if segment_spec["marker_color"] is not None:
            seg_color = segment_spec["marker_color"]

        spherical = (
            p.x == d.x and p.y == d.y and p.z == d.z and p.diameter == d.diameter
        )

        if verbose:
            logger.info(
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


def plot_2D_point_cells(
    offset: typing.List[float] = [0, 0],
    plane2d: str = "xy",
    color: typing.Optional[str] = None,
    soma_radius: float = 10.0,
    title: str = "",
    verbose: bool = False,
    fig: Optional[matplotlib.figure.Figure] = None,
    ax: Optional[matplotlib.axes.Axes] = None,
    axis_min_max: typing.List = [float("inf"), -1 * float("inf")],
    scalebar: bool = False,
    nogui: bool = True,
    autoscale: bool = True,
    square: bool = False,
    save_to_file: typing.Optional[str] = None,
    close_plot: bool = False,
):
    """Plot point cells.

    .. versionadded:: 1.0.0

    .. seealso::

        :py:func:`plot_2D`
            general function for plotting

        :py:func:`plot_2D_schematic`
            for plotting only segmeng groups with their labels

        :py:func:`plot_2D_cell_morphology`
            for plotting cells with detailed morphologies

    :param offset: location of cell
    :type offset: [float, float]
    :param plane2d: plane to plot on
    :type plane2d: str
    :param color: color to use for cell
    :type color: str
    :param soma_radius: radius of soma
    :type soma_radius: float
    :param fig: a matplotlib.figure.Figure object to use
    :type fig: matplotlib.figure.Figure
    :param ax: a matplotlib.axes.Axes object to use
    :type ax: matplotlib.axes.Axes
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
    """
    if fig is None:
        fig, ax = get_new_matplotlib_morph_plot(title)

    cell_color = get_next_hex_color()

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
    width: float = 2.0,
    verbose: bool = False,
    square: bool = False,
    nogui: bool = False,
    save_to_file: typing.Optional[str] = None,
    scalebar: bool = True,
    autoscale: bool = True,
    fig: Optional[matplotlib.figure.Figure] = None,
    ax: Optional[matplotlib.axes.Axes] = None,
    title: str = "",
    close_plot: bool = False,
) -> None:
    """Plot a 2D schematic of the provided segment groups.

    This plots each segment group as a straight line between its first and last
    segment.

    .. versionadded:: 1.0.0

    .. seealso::

        :py:func:`plot_2D`
            general function for plotting

        :py:func:`plot_2D_point_cells`
            for plotting point cells

        :py:func:`plot_2D_cell_morphology`
            for plotting cells with detailed morphologies

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
    :param width: width for lines
    :type width: float
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
    segment_groups: typing.List[str],
    labels: bool = False,
    verbose: bool = False,
    nogui: bool = False,
    save_to_file: typing.Optional[str] = None,
    overlay_data: typing.Optional[typing.Dict[str, typing.List[typing.Any]]] = None,
    overlay_data_label: str = "",
    width: typing.Union[float, int] = 4,
    colormap_name: str = "viridis",
    title: str = "SegmentGroup",
    datamin: typing.Optional[float] = None,
    datamax: typing.Optional[float] = None,
    close_plot: bool = False,
) -> None:
    """Plot curtain plots of provided segment groups.

    .. versionadded:: 1.0.0

    :param cell: cell to plot
    :type cell: neuroml.Cell
    :param segment_groups: list of ids of unbranched segment groups to plot
    :type segment_groups: list(str)
    :param labels: toggle labelling of segment groups
    :type labels: bool
    :param verbose: show extra information (default: False)
    :type verbose: bool
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
            raise ValueError(
                f"Keys of overlay_data ({overlay_data.keys()}) and ord_segs ({ord_segs.keys()})must match."
            )
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
            ax=ax,
            label=overlay_data_label,
        )

    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.yaxis.set_ticks_position("left")
    ax.xaxis.set_ticks_position("none")
    ax.xaxis.set_ticks([])

    ax.set_xlabel(title)
    ax.set_ylabel("length (μm)")

    logger.debug(f"Generating curtain plot for {len(ord_segs)} segment groups")

    # column counter
    column = 0
    for sgid, segs in ord_segs.items():
        logger.debug(f"Processing {sgid}")
        column += 1
        length = 0

        cumulative_lengths_sg = cumulative_lengths[sgid]

        sgobj = cell.get_segment_group(sgid)
        if sgobj.neuro_lex_id != neuro_lex_ids["section"]:
            raise ValueError(
                f"{sgobj} does not have neuro_lex_id set to indicate it is an unbranched segment"
            )

        for seg_num in range(0, len(segs)):
            # seg = segs[seg_num]
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
