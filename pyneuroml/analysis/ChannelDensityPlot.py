#!/usr/bin/env python
#
#   A script which can be used to generate graphical representation of
#   ion channel densities in NeuroML2 cells
#

import argparse
import logging
import math
import os
import pprint
import typing
from collections import OrderedDict

import matplotlib
import matplotlib.pyplot as plt
import numpy
from matplotlib.colors import LinearSegmentedColormap
from neuroml import (
    Cell,
    Cell2CaPools,
    ChannelDensity,
    ChannelDensityGHK,
    ChannelDensityGHK2,
    ChannelDensityNernst,
    ChannelDensityNernstCa2,
    ChannelDensityNonUniform,
    ChannelDensityNonUniformGHK,
    ChannelDensityNonUniformNernst,
    ChannelDensityVShift,
    VariableParameter,
)
from sympy import sympify

from pyneuroml.plot.Plot import generate_plot
from pyneuroml.plot.PlotMorphology import plot_2D_cell_morphology
from pyneuroml.pynml import get_value_in_si, read_neuroml2_file
from pyneuroml.utils import get_ion_color
from pyneuroml.utils.cli import build_namespace

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


pp = pprint.PrettyPrinter(depth=6)

height = 18
spacing = 2
width_o = 18
order = 8
width = width_o * order
start = -2
stop = start + order

substitute_ion_channel_names = {"LeakConductance": "Pas"}

CHANNEL_DENSITY_PLOTTER_CLI_DEFAULTS = {
    "nogui": False,
    "noDistancePlots": False,
}


def channel_density_plotter_process_args():
    """Parse command-line arguments.

    :returns: None
    """
    parser = argparse.ArgumentParser(
        description=(
            "A script to generate channel density plots"
            "for different ion channels on a NeuroML2"
            "cell"
        )
    )

    parser.add_argument(
        "cellFiles",
        type=str,
        nargs="+",
        metavar="<NeuroML 2 Cell file>",
        help="Name of the NeuroML 2 file(s)",
    )

    parser.add_argument(
        "-noDistancePlots",
        action="store_true",
        default=CHANNEL_DENSITY_PLOTTER_CLI_DEFAULTS["noDistancePlots"],
        help=("Do not generate distance plots"),
    )
    parser.add_argument(
        "-nogui",
        action="store_true",
        default=CHANNEL_DENSITY_PLOTTER_CLI_DEFAULTS["nogui"],
        help=("Do not show plots as they are generated"),
    )

    return parser.parse_args()


def _get_rect(ion_channel, row, max_, min_, r, g, b, extras=False):
    if max_ == 0:
        return ""

    sb = ""

    lmin = max(math.log10(min_), start)
    lmax = min(math.log10(max_), stop)
    xmin = width * (lmin - start) / order
    xmax = width * (lmax - start) / order
    offset = (height + spacing) * row

    sb += "\n<!-- %s %s: %s -> %s (%s -> %s)-->\n" % (
        row,
        ion_channel,
        min_,
        max_,
        lmin,
        lmax,
    )
    sb += (
        '<rect y="'
        + str(offset)
        + '" width="'
        + str(width)
        + '" height="'
        + str(height)
        + '" style="fill:rgb('
        + str(r)
        + ","
        + str(g)
        + ","
        + str(b)
        + ');stroke-width:0;stroke:rgb(10,10,10)"/>\n'
    )

    text = "%s: " % (
        ion_channel
        if ion_channel not in substitute_ion_channel_names
        else substitute_ion_channel_names[ion_channel]
    )

    for i in range(order):
        x = width_o * i
        sb += (
            '<line x1="'
            + str(x)
            + '" y1="'
            + str(offset)
            + '" x2="'
            + str(x)
            + '" y2="'
            + str(height + offset)
            + '" style="stroke:rgb(100,100,100);stroke-width:0.5" />\n'
        )

    if max_ == min_:
        sb += (
            '<circle cx="'
            + str(xmin)
            + '" cy="'
            + str(offset + (height / 2))
            + '" r="2" style="stroke:yellow;fill:yellow;stroke-width:2" />\n'
        )
        text += " %s S/m^2" % format_float(min_)
    else:
        sb += (
            '<line x1="'
            + str(xmin)
            + '" y1="'
            + str(offset + (height / 2))
            + '" x2="'
            + str(xmax)
            + '" y2="'
            + str(offset + (height / 2))
            + '" style="stroke:black;stroke-width:1" />\n'
        )
        sb += (
            '<circle cx="'
            + str(xmin)
            + '" cy="'
            + str(offset + (height / 2))
            + '" r="2" style="stroke:yellow;fill:yellow;stroke-width:2" />\n'
        )
        sb += (
            '<circle cx="'
            + str(xmax)
            + '" cy="'
            + str(offset + (height / 2))
            + '" r="2" style="stroke:red;fill:red;stroke-width:2" />\n'
        )
        text += " %s->%s S/m^2" % (format_float(min_), format_float(max_))

    if extras:
        sb += (
            '<text x="%s" y="%s" fill="black" font-family="Arial" font-size="12">%s</text>\n'
            % (width + 3, offset + height - 3, text)
        )

    return sb


def format_float(dens):
    if dens == 0:
        return 0
    if int(dens) == dens:
        return "%i" % dens
    if dens < 1e-4:
        return "%f" % dens
    ff = "%.4f" % (dens)
    if "." in ff:
        ff = ff.rstrip("0")
    return ff


def generate_channel_density_plots(
    nml2_file, text_densities=False, passives_erevs=False, target_directory=None
):
    nml_doc = read_neuroml2_file(
        nml2_file, include_includes=True, verbose=False, optimized=True
    )

    cell_elements = []
    cell_elements.extend(nml_doc.cells)
    cell_elements.extend(nml_doc.cell2_ca_poolses)
    svg_files = []
    all_info = {}

    for cell in cell_elements:
        info = {}
        all_info[cell.id] = info
        logger.info("Extracting channel density info from %s" % cell.id)
        sb = ""
        ions = {}
        maxes = {}
        mins = {}
        row = 0
        na_ions = []
        k_ions = []
        ca_ions = []
        other_ions = []

        if isinstance(cell, Cell2CaPools):
            cds = (
                cell.biophysical_properties2_ca_pools.membrane_properties2_ca_pools.channel_densities
                + cell.biophysical_properties2_ca_pools.membrane_properties2_ca_pools.channel_density_nernsts
            )
        elif isinstance(cell, Cell):
            cds = (
                cell.biophysical_properties.membrane_properties.channel_densities
                + cell.biophysical_properties.membrane_properties.channel_density_nernsts
            )

        epas = None
        ena = None
        ek = None
        eh = None
        eca = None

        for cd in cds:
            dens_si = get_value_in_si(cd.cond_density)
            logger.info(
                "cd: %s, ion_channel: %s, ion: %s, density: %s (SI: %s)"
                % (cd.id, cd.ion_channel, cd.ion, cd.cond_density, dens_si)
            )

            ions[cd.ion_channel] = cd.ion
            erev_V = get_value_in_si(cd.erev) if hasattr(cd, "erev") else None
            erev = (
                "%s mV" % format_float(erev_V * 1000) if hasattr(cd, "erev") else None
            )

            if cd.ion == "na":
                if cd.ion_channel not in na_ions:
                    na_ions.append(cd.ion_channel)
                ena = erev
                info["ena"] = erev_V
            elif cd.ion == "k":
                if cd.ion_channel not in k_ions:
                    k_ions.append(cd.ion_channel)
                ek = erev
                info["ek"] = erev_V
            elif cd.ion == "ca":
                if cd.ion_channel not in ca_ions:
                    ca_ions.append(cd.ion_channel)
                eca = erev
                info["eca"] = erev_V
            else:
                if cd.ion_channel not in other_ions:
                    other_ions.append(cd.ion_channel)
                if cd.ion == "non_specific":
                    epas = erev
                    info["epas"] = erev_V
                if cd.ion == "h":
                    eh = erev
                    info["eh"] = erev_V

            if cd.ion_channel in maxes:
                if dens_si > maxes[cd.ion_channel]:
                    maxes[cd.ion_channel] = dens_si
            else:
                maxes[cd.ion_channel] = dens_si
            if cd.ion_channel in mins:
                if dens_si < mins[cd.ion_channel]:
                    mins[cd.ion_channel] = dens_si
            else:
                mins[cd.ion_channel] = dens_si

        for ion_channel in na_ions + k_ions + ca_ions + other_ions:
            col = get_ion_color(ions[ion_channel])
            info[ion_channel] = {"max": maxes[ion_channel], "min": mins[ion_channel]}

            if maxes[ion_channel] > 0:
                sb += _get_rect(
                    ion_channel,
                    row,
                    maxes[ion_channel],
                    mins[ion_channel],
                    col[0],
                    col[1],
                    col[2],
                    text_densities,
                )
                row += 1

        if passives_erevs:
            if ena:
                sb += add_text(row, "E Na = %s " % ena)
                row += 1
            if ek:
                sb += add_text(row, "E K = %s " % ek)
                row += 1
            if eca:
                sb += add_text(row, "E Ca = %s" % eca)
                row += 1
            if eh:
                sb += add_text(row, "E H = %s" % eh)
                row += 1
            if epas:
                sb += add_text(row, "E pas = %s" % epas)
                row += 1

            for (
                sc
            ) in cell.biophysical_properties.membrane_properties.specific_capacitances:
                sb += add_text(row, "C (%s) = %s" % (sc.segment_groups, sc.value))

                info["specific_capacitance_%s" % sc.segment_groups] = get_value_in_si(
                    sc.value
                )
                row += 1

            # sb+='<text x="%s" y="%s" fill="black" font-family="Arial">%s</text>\n'%(width/3., (height+spacing)*(row+1), text)

        sb = (
            "<?xml version='1.0' encoding='UTF-8'?>\n<svg xmlns=\"http://www.w3.org/2000/svg\" width=\""
            + str(width + text_densities * 200)
            + '" height="'
            + str((height + spacing) * row)
            + '">\n'
            + sb
            + "</svg>\n"
        )

        print(sb)
        svg_file = nml2_file + "_channeldens.svg"
        if target_directory:
            svg_file = target_directory + "/" + svg_file.split("/")[-1]
        svg_files.append(svg_file)
        sf = open(svg_file, "w")
        sf.write(sb)
        sf.close()
        logger.info("Written to %s" % os.path.abspath(svg_file))

        pp.pprint(all_info)

    return svg_files, all_info


def add_text(row, text):
    return (
        '<text x="%s" y="%s" fill="black" font-family="Arial" font-size="12">%s</text>\n'
        % (width / 3.0, (height + spacing) * (row + 0.5), text)
    )


def get_channel_densities(
    nml_cell: Cell,
) -> typing.Dict[
    str,
    typing.List[
        typing.Union[
            ChannelDensity,
            ChannelDensityGHK,
            ChannelDensityGHK2,
            ChannelDensityVShift,
            ChannelDensityNernst,
            ChannelDensityNernstCa2,
            ChannelDensityNonUniform,
            ChannelDensityNonUniformGHK,
            ChannelDensityNonUniformNernst,
        ]
    ],
]:
    """Get channel densities from a NeuroML Cell.

    :param nml_cell: a NeuroML cell object
    :type nml_cell: neuroml.Cell
    :returns: ordered dictionary of channel densities on cell with the ion
        channel id as the key, and list of channel density objects as the value
    """
    # order matters because if two channel densities apply conductances to same
    # segments, only the latest value is applied
    channel_densities = OrderedDict()  # type: typing.Dict[str, typing.List[typing.Any]]
    dens = nml_cell.biophysical_properties.membrane_properties.info(
        show_contents=True, return_format="dict"
    )
    for name, obj in dens.items():
        logger.debug(f"Name: {name}")
        # channel_densities; channel_density_nernsts, etc
        if name.startswith("channel_densit"):
            for m in obj["members"]:
                try:
                    channel_densities[m.ion_channel].append(m)
                except KeyError:
                    channel_densities[m.ion_channel] = []
                    channel_densities[m.ion_channel].append(m)

    logger.debug(f"Found channel densities: {channel_densities}")
    return channel_densities


def get_conductance_density_for_segments(
    cell: Cell,
    channel_density: typing.Union[
        ChannelDensity,
        ChannelDensityGHK,
        ChannelDensityGHK2,
        ChannelDensityVShift,
        ChannelDensityNernst,
        ChannelDensityNernstCa2,
        ChannelDensityNonUniform,
        ChannelDensityNonUniformGHK,
        ChannelDensityNonUniformNernst,
    ],
    seg_ids: typing.Optional[typing.Union[str, typing.List[str]]] = None,
) -> typing.Dict[int, float]:
    """Get conductance density for provided segments to be able to generate a
    morphology plot.

    If no segment ids are provided, provide values for all segments that the
    channel density is present on.

    For uniform channel densities, the value is reported in SI units, but for
    non-uniform channel densities, for example ChannelDensityNonUniform, where
    the conductance density can be a function of an arbitrary variable, like
    distance from soma, the conductance density can be provided by an arbitrary
    function. In this case, the units of the conductance are not reported since
    the arbitrary function only provides a magnitude.

    For non-uniform channel densities, we evaluate the provided expression
    using sympy.sympify.

    :param cell: a NeuroML Cell
    :type cell: Cell
    :param seg_ids: segment id or list of segment ids to report, if None,
        report on all segments that channel density is present
    :type seg_ids: None or str or list(str)
    :param channel_density: a channel density object
    :type channel_density: ChannelDensityGHK or ChannelDensityGHK2 or ChannelDensityVShift or ChannelDensityNernst or ChannelDensityNernstCa2 or ChannelDensityNonUniform or ChannelDensityNonUniformGHK or ChannelDensityNonUniformNernst,
    :returns: dictionary with keys as segment ids and the conductance density
        for that segment as the value

    .. versionadded:: 1.0.10

    """
    data = {}
    segments = []

    # for uniform
    try:
        seg_group_name = channel_density.segment_groups
    # for NonUniform
    except AttributeError:
        seg_group_name = channel_density.variable_parameters[0].segment_groups
    seg_group = cell.get_segment_group(seg_group_name)
    segments = cell.get_all_segments_in_group(seg_group)

    # add any segments explicitly listed
    try:
        segments.extend(channel_density.segments)
    except TypeError:
        pass
    # non uniform channel densities do not have a segments child element
    except AttributeError:
        pass

    # filter to seg_ids
    if seg_ids is not None:
        if isinstance(seg_ids, str):
            segments = [seg_ids]
        else:
            segments = list(set(seg_ids) & set(segments))

    if "NonUniform" not in channel_density.__class__.__name__:
        logger.debug(f"Got a uniform channel density: {channel_density.id}")

        for seg in cell.morphology.segments:
            if seg.id in segments:
                value = get_value_in_si(channel_density.cond_density)
                if value is not None:
                    data[seg.id] = value
    else:
        # get the inhomogeneous param/value from the channel density
        param: VariableParameter = channel_density.variable_parameters[0]
        inhom_val = param.inhomogeneous_value.value
        # H(x) -> Heaviside(x, 0)
        if "H" in inhom_val:
            newstr = inhom_val.replace("H", "Heaviside")
            """
            # not needed, we use the same H as in sympy
            for arg in preorder_traversal(inhom_expr):
                if isinstance(arg, Function) and str(arg.func) == "H":
                    newstr = newstr.replace(str(arg.args[0]), f"{arg.args[0]}, 0")
            newstr = newstr.replace("H(", "Heaviside(")
            """
            inhom_expr = sympify(newstr)
        else:
            inhom_expr = sympify(inhom_val)
        inhom_param_id = param.inhomogeneous_value.inhomogeneous_parameters
        logger.debug(f"Inhom value: {inhom_val}, Inhom param id: {inhom_param_id}")

        inhom_params = seg_group.inhomogeneous_parameters
        req_inhom_param = None
        for p in inhom_params:
            if p.id == inhom_param_id:
                req_inhom_param = p
                break
        if req_inhom_param is None:
            raise ValueError(
                f"Could not find InhomogeneousValue definition for id: {inhom_param_id}"
            )
        logger.debug(f"InhomogeneousParameter found: {req_inhom_param.id}")
        expr_variable = req_inhom_param.variable

        # TODO: can probably speed this up using lambdify:
        # https://docs.sympy.org/latest/tutorials/intro-tutorial/basic_operations.html#lambdify
        # code currently not slow, so leaving this for the future
        for seg in cell.morphology.segments:
            if seg.id in segments:
                distance_to_seg = cell.get_distance(seg.id)
                data[seg.id] = float(inhom_expr.subs(expr_variable, distance_to_seg))

    return data


def plot_channel_densities(
    cell: Cell,
    channel_density_ids: typing.Optional[typing.Union[str, typing.List[str]]] = None,
    ion_channels: typing.Optional[typing.Union[str, typing.List[str]]] = None,
    ymin: typing.Optional[float] = None,
    ymax: typing.Optional[float] = None,
    colormap_name: str = "autumn_r",
    plane2d: str = "xy",
    distance_plots: bool = False,
    show_plots_already: bool = True,
    morph_plot_type: str = "constant",
    morph_min_width: float = 2.0,
    target_directory=None,
):
    """Plot channel densities on a Cell on morphology plots.

    You can either provide a list of channel densities where it'll generate one
    plot per channel density. Or, you can provide a list of ions, and it'll
    generate one plot per ion---adding up the conductance densities of the
    different channel densities for that ion. If neither are provided, plots
    for all ion channels on the cell are generated.

    .. versionadded:: 1.0.10

    :param cell: a NeuroML cell object
    :type cell: neuroml.Cell
    :param channel_density_ids: a channel density id or list of ids
    :type channel_density_ids: str or list(str)
    :param ion_channels: an ion channel or list of ions channels
    :type ion_channels: str or list(str)
    :param ymin: min y value for plots, if None, automatically calculated
    :type ymin: float or None
    :param ymax: max y value for plots, if None, automatically calculated
    :type ymax: float or None
    :param plane2d: plane to plot morphology plot in, passed on to the
        :py:function::`plot_2D_cell_morphology` function
    :type plane2d: str "xy" or "yz" or "zx"
    :param morph_plot_type: plot type for morphology plot passed on to
        plot_2D_cell_morphology
    :type morph_plot_type: str
    :param morph_min_width: min width for morphology plot passed on to
        plot_2D_cell_morphology
    :type morph_min_width: float
    :param distance_plots: also generate plots showing conductance densities at
        distances from the soma
    :type distance_plots: bool
    :param colormap_name: name of matplotlib colormap to use for morph plot.
        Note that if there's only one overlay value, the colormap is modified
        to only show the max value of the colormap to indicate this.

        See: https://matplotlib.org/stable/users/explain/colors/colormaps.html
    :type colormap_name: str
    :returns: None
    """
    tgt_dir = target_directory + "/" if target_directory else "./"

    if channel_density_ids is not None and ion_channels is not None:
        raise ValueError(
            "Only one of channel_density_ids or ions channels may be provided"
        )

    channel_densities = get_channel_densities(cell)
    logger.debug(f"Got channel densities {channel_densities}")
    # if neither are provided, generate plots for all ion channels on the cell
    if channel_density_ids is None and ion_channels is None:
        ion_channels = list(channel_densities.keys())

    # calculate distances of segments from soma for later use
    if distance_plots:
        distances = {}
        for seg in cell.morphology.segments:
            distances[seg.id] = cell.get_distance(seg.id)

        # sorted by distances
        sorted_distances = {
            k: v for k, v in sorted(distances.items(), key=lambda item: item[1])
        }

    if channel_density_ids is not None:
        if isinstance(channel_density_ids, str):
            channel_density_ids_list = []
            channel_density_ids_list.append(channel_density_ids)
            channel_density_ids = channel_density_ids_list

        logger.info(f"Plotting channel density plots for {channel_density_ids}")

        for ion_channel, cds in channel_densities.items():
            logger.debug(f"Looking at {ion_channel}: {cds}")
            for cd in cds:
                if cd.id in channel_density_ids:
                    print(f"Generating plots for {cd.id}")
                    data = get_conductance_density_for_segments(cell, cd)
                    logger.debug(f"Got data for {cd.id}")

                    # default colormap: what user passed
                    colormap_name_to_pass = colormap_name

                    # define a new colormap with a single color if there's
                    # only one value
                    this_max = numpy.max(list(data.values()))
                    this_min = numpy.min(list(data.values()))
                    if this_max == this_min:
                        logger.debug(
                            "Only one data value found, creating custom colormap"
                        )
                        selected_colormap = matplotlib.colormaps[colormap_name]
                        maxcolor = selected_colormap(1.0)
                        cdict = {
                            "red": (
                                (0.0, maxcolor[0], maxcolor[0]),
                                (1.0, maxcolor[0], maxcolor[0]),
                            ),
                            "green": (
                                (0.0, maxcolor[1], maxcolor[1]),
                                (1.0, maxcolor[1], maxcolor[1]),
                            ),
                            "blue": (
                                (0.0, maxcolor[2], maxcolor[2]),
                                (1.0, maxcolor[2], maxcolor[2]),
                            ),
                            "alpha": (
                                (0.0, maxcolor[3], maxcolor[3]),
                                (1.0, maxcolor[3], maxcolor[3]),
                            ),
                        }
                        colormap_name_to_pass = "new_pyneuroml_morph_color_map"
                        newcolormap = LinearSegmentedColormap(
                            colormap_name_to_pass, cdict
                        )
                        matplotlib.colormaps.register(newcolormap, force=True)

                    plot_2D_cell_morphology(
                        cell=cell,
                        title=f"{cd.id}",
                        plot_type=morph_plot_type,
                        min_width=morph_min_width,
                        overlay_data=data,
                        overlay_data_label="(S/m2)",
                        save_to_file=f"{tgt_dir}{cell.id}_{cd.id}.cd.png",
                        datamin=ymin,
                        plane2d=plane2d,
                        nogui=not show_plots_already,
                        colormap_name=colormap_name_to_pass,
                    )
                    if distance_plots:
                        xvals = []
                        yvals = []
                        for segid, distance in sorted_distances.items():
                            # if segid is not in data, it'll just skip and
                            # continue
                            try:
                                yvals.append(data[segid])
                                xvals.append(distance)
                            except KeyError:
                                pass

                        generate_plot(
                            xvalues=[xvals],
                            yvalues=[yvals],
                            title=f"{cd.id}",
                            title_above_plot=True,
                            xaxis="Distance from soma (um)",
                            yaxis="g density (S/m2)",
                            save_figure_to=f"{tgt_dir}{cell.id}_{cd.id}_cd_vs_dist.png",
                            show_plot_already=show_plots_already,
                            linestyles=[" "],
                            linewidths=["0"],
                            markers=["."],
                        )
            if show_plots_already is False:
                plt.close()

    elif ion_channels is not None:
        if isinstance(ion_channels, str):
            ion_channel_list = []
            ion_channel_list.append(ion_channels)
            ion_channels = ion_channel_list
        logger.info(f"Plotting channel density plots for ion channels: {ion_channels}")

        for ion_channel, cds in channel_densities.items():
            if ion_channel in ion_channels:
                logger.debug(f"Looking at {ion_channel}: {cds}")
                print(f"Generating plots for {ion_channel}")
                data = {}
                for cd in cds:
                    data_for_cd = get_conductance_density_for_segments(cell, cd)
                    logger.debug(f"Got data for {cd.id}")
                    for seg, val in data_for_cd.items():
                        try:
                            data[seg] += val
                        except KeyError:
                            data[seg] = val

                # plot per ion channel
                # note: plotting code is almost identical to code above with
                # changes to use ion channel instead of cd
                # so, when updating, remember to update both
                # can probably be split out into a private helper method

                # default colormap: what user passed
                colormap_name_to_pass = colormap_name

                # define a new colormap with a single color if there's
                # only one value
                this_max = numpy.max(list(data.values()))
                this_min = numpy.min(list(data.values()))
                if this_max == this_min:
                    logger.debug("Only one data value found, creating custom colormap")
                    selected_colormap = matplotlib.colormaps[colormap_name]
                    maxcolor = selected_colormap(1.0)
                    cdict = {
                        "red": (
                            (0.0, maxcolor[0], maxcolor[0]),
                            (1.0, maxcolor[0], maxcolor[0]),
                        ),
                        "green": (
                            (0.0, maxcolor[1], maxcolor[1]),
                            (1.0, maxcolor[1], maxcolor[1]),
                        ),
                        "blue": (
                            (0.0, maxcolor[2], maxcolor[2]),
                            (1.0, maxcolor[2], maxcolor[2]),
                        ),
                        "alpha": (
                            (0.0, maxcolor[3], maxcolor[3]),
                            (1.0, maxcolor[3], maxcolor[3]),
                        ),
                    }
                    colormap_name_to_pass = "new_pyneuroml_morph_color_map"
                    newcolormap = LinearSegmentedColormap(colormap_name_to_pass, cdict)
                    matplotlib.colormaps.register(newcolormap, force=True)

                plot_2D_cell_morphology(
                    cell=cell,
                    title=f"{ion_channel}",
                    plot_type=morph_plot_type,
                    min_width=morph_min_width,
                    overlay_data=data,
                    overlay_data_label="(S/m2)",
                    save_to_file=f"{tgt_dir}{cell.id}_{ion_channel}.ion.png",
                    datamin=ymin,
                    plane2d=plane2d,
                    nogui=not show_plots_already,
                    colormap_name=colormap_name_to_pass,
                )
                if distance_plots:
                    xvals = []
                    yvals = []
                    for segid, distance in sorted_distances.items():
                        # if segid is not in data, it'll just skip and
                        # continue
                        try:
                            yvals.append(data[segid])
                            xvals.append(distance)
                        except KeyError:
                            pass

                    generate_plot(
                        xvalues=[xvals],
                        yvalues=[yvals],
                        title=f"{ion_channel}",
                        title_above_plot=True,
                        xaxis="Distance from soma (um)",
                        yaxis="g density (S/m2)",
                        save_figure_to=f"{tgt_dir}{cell.id}_{ion_channel}_ion_vs_dist.png",
                        show_plot_already=show_plots_already,
                        linestyles=[" "],
                        linewidths=["0"],
                        markers=["."],
                    )
            if show_plots_already is False:
                plt.close()
    # will never reach here


def channel_density_plotter_cli(args=None):
    if args is None:
        args = channel_density_plotter_process_args()
    channel_density_plotter_runner(a=args)


def channel_density_plotter_runner(a=None, **kwargs):
    a = build_namespace(CHANNEL_DENSITY_PLOTTER_CLI_DEFAULTS, a, **kwargs)

    if len(a.cell_files) > 0:
        for cell_file in a.cell_files:
            nml_doc = read_neuroml2_file(
                cell_file, include_includes=True, verbose=False, optimized=True
            )
            # show all plots at end
            plot_channel_densities(
                nml_doc.cells[0],
                show_plots_already=not a.nogui,
                distance_plots=not a.no_distance_plots,
            )


if __name__ == "__main__":
    generate_channel_density_plots(
        "../../examples/test_data/HHCellNetwork.net.nml", True, True
    )

    generate_channel_density_plots(
        "../../../neuroConstruct/osb/showcase/BlueBrainProjectShowcase/NMC/NeuroML2/cADpyr229_L23_PC_5ecbf9b163_0_0.cell.nml",
        True,
        True,
    )
