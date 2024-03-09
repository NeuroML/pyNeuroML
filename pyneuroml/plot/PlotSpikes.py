#!/usr/bin/env python3
"""
Spike plotting helper functions.

File: pyneuroml/plot/PlotSpikes.py

Copyright 2023 NeuroML contributors
"""
import argparse
import logging
import os
import sys
from collections import OrderedDict

import matplotlib.pyplot as plt
import numpy as np
from pyneuroml.plot import generate_plot
from pyneuroml.utils.cli import build_namespace

logger = logging.getLogger(__name__)

FORMAT_ID_T = "id_t"
FORMAT_ID_TIME_NEST_DAT = "id_t_nest_dat"
FORMAT_T_ID = "t_id"

DEFAULTS = {
    "format": FORMAT_ID_T,
    "rates": False,
    "save_spike_plot_to": None,
    "rate_window": 50,
    "rate_bins": 500,
    "show_plots_already": True,
}

POP_NAME_SPIKEFILE_WITH_GIDS = "Spiketimes for GIDs"


def process_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="A script for plotting files containing spike time data"
    )

    parser.add_argument(
        "spiketimeFiles",
        type=str,
        metavar="<spiketime file>",
        help="List of text file containing spike times",
        nargs="+",
    )

    parser.add_argument(
        "-format",
        type=str,
        metavar="<format>",
        default=DEFAULTS["format"],
        help="How the spiketimes are represented on each line of file: \n"
        + "%s: id of cell, space(s) / tab(s), time of spike (default);\n" % FORMAT_ID_T
        + "%s: id of cell, space(s) / tab(s), time of spike, allowing NEST dat file comments/metadata;\n"
        % FORMAT_ID_TIME_NEST_DAT
        + "%s: time of spike, space(s) / tab(s), id of cell;\n" % FORMAT_T_ID
        + "sonata: SONATA format HDF5 file containing spike times",
    )

    parser.add_argument(
        "-rates",
        action="store_true",
        default=DEFAULTS["rates"],
        help="Show a plot of rates",
    )

    parser.add_argument(
        "-showPlotsAlready",
        action="store_true",
        default=DEFAULTS["show_plots_already"],
        help="Show plots once generated",
    )

    parser.add_argument(
        "-saveSpikePlotTo",
        type=str,
        metavar="<spiketime plot filename>",
        default=DEFAULTS["save_spike_plot_to"],
        help="Name of file in which to save spiketime plot",
    )

    parser.add_argument(
        "-rateWindow",
        type=int,
        metavar="<rate window>",
        default=DEFAULTS["rate_window"],
        help="Window for rate calculation in ms",
    )

    parser.add_argument(
        "-rateBins",
        type=int,
        metavar="<rate bins>",
        default=DEFAULTS["rate_bins"],
        help="Number of bins for rate histogram",
    )

    return parser.parse_args()


def read_sonata_spikes_hdf5_file(file_name: str) -> dict:
    """Read spike times from a SONATA format HDF5 file.

    :param file_name: The name of the HDF5 file.
    :type file_name: str
    :return: A dictionary where the keys are population names and the values are dictionaries of spike times for each ID in the population.
    :rtype: dict
    """
    full_path = os.path.abspath(file_name)
    logger.info("Loading SONATA spike times from: %s (%s)" % (file_name, full_path))

    import tables  # pytables for HDF5 support

    h5file = tables.open_file(file_name, mode="r")

    sorting = (
        h5file.root.spikes._v_attrs.sorting
        if hasattr(h5file.root.spikes._v_attrs, "sorting")
        else "???"
    )
    logger.info("Opened HDF5 file: %s; sorting=%s" % (h5file.filename, sorting))

    ids_times_pops = {}
    if hasattr(h5file.root.spikes, "gids"):
        gids = h5file.root.spikes.gids
        timestamps = h5file.root.spikes.timestamps
        ids_times = {}
        count = 0
        max_t = -1 * sys.float_info.max
        min_t = sys.float_info.max
        for i in range(len(gids)):
            id = gids[i]
            t = timestamps[i]
            max_t = max(max_t, t)
            min_t = min(min_t, t)
            if id not in ids_times:
                ids_times[id] = []
            ids_times[id].append(t)
            count += 1

        ids = ids_times.keys()
        logger.info(
            "Loaded %s spiketimes, ids (%s -> %s) times (%s -> %s)"
            % (count, min(ids), max(ids), min_t, max_t)
        )

        ids_times_pops[POP_NAME_SPIKEFILE_WITH_GIDS] = ids_times
    else:
        for group in h5file.root.spikes:
            node_ids = group.node_ids
            timestamps = group.timestamps
            ids_times = {}
            count = 0
            max_t = -1 * sys.float_info.max
            min_t = sys.float_info.max
            for i in range(len(node_ids)):
                id = node_ids[i]
                t = timestamps[i]
                max_t = max(max_t, t)
                min_t = min(min_t, t)
                if id not in ids_times:
                    ids_times[id] = []
                ids_times[id].append(t)
                count += 1

            ids = ids_times.keys()
            logger.info(
                "Loaded %s spiketimes for %s, ids (%s -> %s) times (%s -> %s)"
                % (count, group._v_name, min(ids), max(ids), min_t, max_t)
            )
            ids_times_pops[group._v_name] = ids_times

    h5file.close()

    return ids_times_pops


from typing import Dict, List, Optional, Union


def plot_spikes(
    spiketime_files: Optional[List[str]] = None,
    spike_data: Optional[List[Dict[str, Union[List[float], List[int]]]]] = None,
    format: str = FORMAT_ID_T,
    rates: bool = False,
    save_spike_plot_to: Optional[str] = None,
    rate_window: int = 50,
    rate_bins: int = 500,
    show_plots_already: bool = True,
) -> None:
    """
    Plot spike times from files or data.

    :param spiketime_files: List of spike time files to be plotted. If provided, `spike_data` should be `None`. Defaults to `None`.
    :type spiketime_files: Optional[List[str]]
    :param spike_data: List of dictionaries containing spike time data. Each dictionary should have the following keys:
                        - "name" (str): Name of the population or file.
                        - "times" (List[float]): List of spike times in seconds.
                        - "ids" (List[int]): List of cell IDs corresponding to each spike time.
                        If provided, `spiketime_files` should be `None`. Defaults to `None`.
    :type spike_data: Optional[List[Dict[str, Union[List[float], List[int]]]]]
    :param format: Format of the spike time data in the files. Can be one of the following:
                   - "id_t": Each line contains a cell ID (int) followed by a spike time (float).
                   - "id_time_nest_dat": Each line contains a cell ID (int) followed by a spike time (float),
                                         with NEST-style comments allowed.
                   - "t_id": Each line contains a spike time (float) followed by a cell ID (int).
                   - "sonata": SONATA-style HDF5 file.
                   Defaults to "id_t".
    :type format: str
    :param rates: Whether to plot rates in addition to spike times. Defaults to False.
    :type rates: bool
    :param save_spike_plot_to: Path to save the spike plot to. If `None`, the plot will not be saved. Defaults to `None`.
    :type save_spike_plot_to: Optional[str]
    :param rate_window: Window size for rate calculation in ms. Defaults to 50.
    :type rate_window: int
    :param rate_bins: Number of bins for rate histogram. Defaults to 500.
    :type rate_bins: int
    :param show_plots_already: Whether to show the plots immediately after they are generated. Defaults to True.
    :type show_plots_already: bool
    :raises ValueError: If neither `spiketime_files` nor `spike_data` is provided.
    :return: None
    :rtype: None
    """
    if spiketime_files is None and spike_data is None:
        raise ValueError("Either spiketime_files or spike_data must be provided.")

    xs = []
    ys = []
    labels = []
    markers = []
    linestyles = []

    offset_id = 0

    max_time = 0
    max_id = 0
    unique_ids = []
    times = OrderedDict()
    ids_in_file = OrderedDict()

    if spiketime_files is not None:
        if format == "sonata" or format == "s":
            for file_name in spiketime_files:
                ids_times_pops = read_sonata_spikes_hdf5_file(file_name)

                for pop in ids_times_pops:
                    ids_times = ids_times_pops[pop]

                    x = []
                    y = []
                    max_id_here = 0

                    name = file_name.split(" / ")[-1]
                    if name.endswith("_spikes.h5"):
                        name = name[:-10]
                    elif name.endswith(".h5"):
                        name = name[:-3]
                    times[name] = []
                    ids_in_file[name] = []

                    for id in ids_times:
                        for t in ids_times[id]:
                            id_shifted = offset_id + int(float(id))
                            max_id = max(max_id, id_shifted)

                            if id_shifted not in ids_in_file[name]:
                                ids_in_file[name].append(id_shifted)
                            times[name].append(t)
                            max_id_here = max(max_id_here, id_shifted)
                            max_time = max(t, max_time)
                            if id_shifted not in unique_ids:
                                unique_ids.append(id_shifted)
                            x.append(t)
                            y.append(id_shifted)

                    labels.append("%s, %s (%i)" % (name, pop, max_id_here - offset_id))
                    offset_id = max_id_here + 1
                    xs.append(x)
                    ys.append(y)
                    markers.append(".")
                    linestyles.append("")

        else:
            for file_name in spiketime_files:
                logger.info("Loading spike times from: %s" % file_name)
                spikes_file = open(file_name)
                x = []
                y = []
                max_id_here = 0

                name = spikes_file.name
                if name.endswith(".spikes"):
                    name = name[:-7]
                if name.endswith(".spike"):
                    name = name[:-6]
                times[name] = []
                ids_in_file[name] = []

                for line in spikes_file:
                    if not line.startswith("#") and not (
                        line.startswith("sender") and format == FORMAT_ID_TIME_NEST_DAT
                    ):
                        if format == FORMAT_ID_T or format == FORMAT_ID_TIME_NEST_DAT:
                            [id, t] = line.split()
                        elif format == FORMAT_T_ID:
                            [t, id] = line.split()
                        id_shifted = offset_id + int(float(id))
                        max_id = max(max_id, id_shifted)
                        t = float(t)
                        if id_shifted not in ids_in_file[name]:
                            ids_in_file[name].append(id_shifted)
                        times[name].append(t)
                        max_id_here = max(max_id_here, id_shifted)
                        max_time = max(t, max_time)
                        if id_shifted not in unique_ids:
                            unique_ids.append(id_shifted)
                        x.append(t)
                        y.append(id_shifted)

                labels.append("%s (%i)" % (name, max_id_here - offset_id))
                offset_id = max_id_here + 1
                xs.append(x)
                ys.append(y)
                markers.append(".")
                linestyles.append("")

    elif spike_data is not None:
        for data in spike_data:
            x = [t for t in data["times"]]
            y = [id_shifted for id_shifted in data["ids"]]

            name = data["name"]
            times[name] = data["times"]
            ids_in_file[name] = data["ids"]
            max_id_here = max(data["ids"])

            labels.append("%s (%i)" % (name, max_id_here - offset_id))
            offset_id = max_id_here + 1
            xs.append(x)
            ys.append(y)
            markers.append(".")
            linestyles.append("")

    xlim = [max_time / -20.0, max_time * 1.05]
    ylim = [max_id / -20.0, max_id * 1.05] if max_id > 0 else [-1, 1]
    markersizes = []
    for xx in xs:
        if len(unique_ids) > 50:
            markersizes.append(2)
        elif len(unique_ids) > 200:
            markersizes.append(1)
        else:
            markersizes.append(4)

    generate_plot(
        xs,
        ys,
        "Spike times from: %s" % spiketime_files,
        labels=labels,
        linestyles=linestyles,
        markers=markers,
        xaxis="Time (s)",
        yaxis="Cell index",
        xlim=xlim,
        ylim=ylim,
        markersizes=markersizes,
        grid=False,
        show_plot_already=False,
        save_figure_to=save_spike_plot_to,
        legend_position="right",
    )

    if rates:
        plt.figure()
        bins = rate_bins
        for name in times:
            tt = times[name]
            ids_here = len(ids_in_file[name])

            plt.hist(
                tt,
                bins=bins,
                histtype="step",
                weights=[bins * max(tt) / (float(ids_here))] * len(tt),
                label=name + "_h",
            )
            hist, bin_edges = np.histogram(
                tt, bins=bins, weights=[bins * max(tt) / (float(ids_here))] * len(tt)
            )

        plt.figure()

        for name in times:
            tt = times[name]
            ids_here = len(ids_in_file[name])

            hist, bin_edges = np.histogram(
                tt, bins=bins, weights=[bins * max(tt) / (float(ids_here))] * len(tt)
            )

            width = bin_edges[1] - bin_edges[0]
            mids = [i + width / 2 for i in bin_edges[:-1]]

            boxes = [5, 10, 20, 50]
            boxes = [20, 50]
            boxes = [int(rate_window)]
            for b in boxes:
                box = np.ones(b)

                hist_c = np.convolve(hist / len(box), box)

                ys = hist_c
                xs = [i / (float(len(ys))) for i in range(len(ys))]
                plt.plot(xs, ys, label=name + "_%i_c" % b)

    if show_plots_already:
        plt.show()
    else:
        plt.close()


def main(args: Optional[argparse.Namespace] = None) -> None:
    """Entry point for the script.

    :param args: Parsed command line arguments. Defaults to None.
    :type args: Optional[argparse.Namespace]
    :return: None
    :rtype: None
    """
    if args is None:
        args = process_args()
    plot_spikes(**vars(args))


if __name__ == "__main__":
    main()
