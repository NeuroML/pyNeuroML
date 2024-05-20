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
import pyneuroml.lems as pynmll
from pyneuroml.utils.cli import build_namespace
from matplotlib import pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar
from typing import Dict, List, Optional, Union
from typing import Tuple


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


def _process_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    :returns: An argparse.Namespace object containing the parsed arguments.
    :rtype: argparse.Namespace
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


def plot_spikes(
    spike_data: List[Dict[str, Union[List[float], List[int]]]],
    spiketime_files: List[str],
    offset: int = 0,
    show_plots_already: bool = True,
    save_spike_plot_to: Optional[str] = None,
    rates: bool = False,
    rate_window: int = 50,
    rate_bins: int = 500,
    max_image_size: Optional[Tuple[int, int]] = None,
) -> None:
    """
    Plot spike times from data.

    :param spike_data: List of dictionaries containing spike time data. Each dictionary should have the following keys:
                        - "name" (str): Name of the population or file.
                        - "times" (List[float]): List of spike times in seconds.
                        - "ids" (List[int]): List of cell IDs corresponding to each spike time.
    :type spike_data: List[Dict[str, Union[List[float], List[int]]]]
    :param show_plots_already: Whether to show the plots immediately after they are generated. Defaults to True.
    :type show_plots_already: bool
    :param save_spike_plot_to: Path to save the spike plot to. If `None`, the plot will not be saved. Defaults to `None`.
    :type save_spike_plot_to: Optional[str]
    :param rates: Whether to plot rates in addition to spike times. Defaults to False.
    :type rates: bool
    :param rate_window: Window size for rate calculation in ms. Defaults to 50.
    :type rate_window: int
    :param rate_bins: Number of bins for rate histogram. Defaults to 500.
    :type rate_bins: int
    :return: None
    :rtype: None
    """

    xs = []
    ys = []
    labels = []
    markers = []
    linestyles = []

    max_time = 0
    max_id = 0
    min_id = float("inf")
    unique_ids = []
    for data in spike_data:
        unique_ids.extend(data["ids"])
    unique_ids = list(set(unique_ids))
    times = OrderedDict()
    ids_in_file = OrderedDict()

    current_offset = offset

    for data in spike_data:
        x = [t for t in data["times"]]
        y = [id_shifted + current_offset for id_shifted in data["ids"]]

        name = data["name"]
        times[name] = data["times"]
        ids_in_file[name] = [id_shifted + current_offset for id_shifted in data["ids"]]
        max_id_here = max(ids_in_file[name])

        max_time = max(max_time, max(x))
        max_id = max(max_id, max_id_here + current_offset)
        min_id = min(min_id, min(ids_in_file[name]) + current_offset)

        labels.append("%s (%i)" % (name, max_id_here))

        xs.append(x)
        ys.append(y)
        markers.append(".")
        linestyles.append("")

    xlim = [0, max_time * 1.05]
    max_id = max([max(ids_in_file[name]) for name in ids_in_file])
    min_id = min([min(ids_in_file[name]) for name in ids_in_file])
    ylim = [min_id - 1 + offset, max_id + 1]

    markersizes = [
        3 if len(unique_ids) <= 50 else 2 if len(unique_ids) <= 200 else 1 for _ in xs
    ]
    if max_image_size is not None:
        plt.figure(figsize=(max_image_size[0] / 100, max_image_size[1] / 100))

    generate_plot(
        xs,
        ys,
        "Spike times from: %s" % ", ".join(spiketime_files),
        labels=labels,
        linestyles=linestyles,
        markers=markers,
        xaxis="Time (s)",
        yaxis="Cell index",
        xlim=xlim,
        ylim=ylim,
        markersizes=markersizes,
        grid=True,
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

            boxes = [int(rate_window)]
            for b in boxes:
                box = np.ones(b)

                hist_c = np.convolve(hist / len(box), box)

                ys = hist_c
                xs = [i / (float(len(ys))) for i in range(len(ys))]
                plt.plot(xs, ys, label=name + "_%i_c" % b)

        plt.legend()
    if show_plots_already:
        plt.show()
    else:
        plt.close()


def plot_spikes_from_data_files(
    spiketime_files: List[str],
    format: str,
    show_plots_already: bool = True,
    save_spike_plot_to: Optional[str] = None,
    rates: bool = False,
    rate_window: int = 50,
    rate_bins: int = 500,
) -> None:
    """
    Plot spike times from data files.

    :param spiketime_files: List of spike time files to be plotted.
    :type spiketime_files: List[str]
    :param format: Format of the spike time data in the files. Can be one of the following:
                   - "id_t": Each line contains a cell ID (int) followed by a spike time (float).
                   - "id_time_nest_dat": Each line contains a cell ID (int) followed by a spike time (float),
                                         with NEST-style comments allowed.
                   - "t_id": Each line contains a spike time (float) followed by a cell ID (int).
                   - "sonata": SONATA-style HDF5 file.
    :type format: str
    :param show_plots_already: Whether to show the plots immediately after they are generated. Defaults to True.
    :type show_plots_already: bool
    :param save_spike_plot_to: Path to save the spike plot to. If `None`, the plot will not be saved. Defaults to `None`.
    :type save_spike_plot_to: Optional[str]
    :param rates: Whether to plot rates in addition to spike times. Defaults to False.
    :type rates: bool
    :param rate_window: Window size for rate calculation in ms. Defaults to 50.
    :type rate_window: int
    :param rate_bins: Number of bins for rate histogram. Defaults to 500.
    :type rate_bins: int
    :return: None
    :rtype: None
    """
    spike_data = []

    if format == "sonata":
        for file_name in spiketime_files:
            ids_times_pops = read_sonata_spikes_hdf5_file(file_name)

            for pop in ids_times_pops:
                ids_times = ids_times_pops[pop]
                times = [t for id, times_list in ids_times.items() for t in times_list]
                ids = [id for id, times_list in ids_times.items() for _ in times_list]

                spike_data.append(
                    {"name": f"{pop} ({file_name})", "times": times, "ids": ids}
                )

    else:
        for file_name in spiketime_files:
            logger.info("Loading spike times from: %s" % file_name)
            spikes_file = open(file_name)
            name = os.path.basename(file_name)
            times = []
            ids = []

            for line in spikes_file:
                if not line.startswith("#") and not (
                    line.startswith("sender") and format == "id_time_nest_dat"
                ):
                    parts = line.split()
                if len(parts) != 2:
                    logger.warning("Invalid line format: %s" % line)
                    continue
                if format == "id_t" or format == "id_time_nest_dat":
                    id, t = parts
                elif format == "t_id":
                    t, id = parts
                elif format == "TIME_ID":
                    t, id = parts
                else:
                    logger.error("Unknown format: %s" % format)
                    raise ValueError("Unknown format: %s" % format)
                times.append(float(t))
                ids.append(int(id))
            spike_data.append({"name": name, "times": times, "ids": ids})

    plot_spikes(
        spike_data,
        spiketime_files,
        offset=0,
        show_plots_already=show_plots_already,
        save_spike_plot_to=save_spike_plot_to,
        rates=rates,
        rate_window=rate_window,
        rate_bins=rate_bins,
    )


def get_spike_data_files_from_lems(
    lems_file_name: str, base_dir: str
) -> Tuple[List[str], str]:
    """
    Read a LEMS simulation file and get the paths of the spike data files and their format.

    :param lems_file_name: Path to the LEMS simulation file.
    :type lems_file_name: str
    :param base_dir: Directory where the LEMS file resides.
    :type base_dir: str
    :return: A tuple containing a list of spike data file paths and the format of the spike data files.
    :rtype: Tuple[List[str], str]
    """
    # Code to read the LEMS file and extract the spike data file paths and format
    sim_data = pynmll.load_sim_data_from_lems_file(lems_file_name)

    spike_data_files = []
    spike_data_format = None
    for select, events in sim_data.items():
        file_path = os.path.join(base_dir, select + ".dat")
        spike_data_files.append(file_path)
        spike_data_format = "TIME_ID"

    return spike_data_files, spike_data_format


def plot_spikes_from_lems_file(
    lems_file_name: str,
    base_dir: str = ".",
    show_plots_already: bool = True,
    save_spike_plot_to: Optional[str] = None,
    rates: bool = False,
    rate_window: int = 50,
    rate_bins: int = 500,
) -> None:
    """
    Plot spike times from a LEMS simulation file.

    This function reads a LEMS simulation file to figure out the names of the spike data files,
    and then calls `plot_spikes_from_data_files` to load and plot the spike data.

    :param lems_file_name: Path to the LEMS simulation file.
    :type lems_file_name: str
    :param base_dir: Directory where the LEMS file resides. Defaults to the current directory.
    :type base_dir: str
    :param show_plots_already: Whether to show the plots immediately after they are generated. Defaults to True.
    :type show_plots_already: bool
    :param save_spike_plot_to: Path to save the spike plot to. If `None`, the plot will not be saved. Defaults to `None`.
    :type save_spike_plot_to: Optional[str]
    :param rates: Whether to plot rates in addition to spike times. Defaults to False.
    :type rates: bool
    :param rate_window: Window size for rate calculation in ms. Defaults to 50.
    :type rate_window: int
    :param rate_bins: Number of bins for rate histogram. Defaults to 500.
    :type rate_bins: int
    :return: None
    :rtype: None
    """
    # Code to read the LEMS simulation file and get the spike data file paths and format
    spike_data_files, spike_data_format = get_spike_data_files_from_lems(
        lems_file_name, base_dir
    )

    plot_spikes_from_data_files(
        spike_data_files,
        spike_data_format,
        show_plots_already=show_plots_already,
        save_spike_plot_to=save_spike_plot_to,
        rates=rates,
        rate_window=rate_window,
        rate_bins=rate_bins,
    )


def main(args: Optional[argparse.Namespace] = None) -> None:
    """Entry point for the script.

    :param args: Parsed command line arguments. Defaults to None.
    :type args: Optional[argparse.Namespace]
    :return: None
    :rtype: None
    """
    if args is None:
        args = _process_args()

    lems_files = [f for f in args.spiketimeFiles if f.startswith("LEMS_")]

    spike_data_files = [f for f in args.spiketimeFiles if not f.startswith("LEMS_")]

    if lems_files:
        for lems_file in lems_files:
            plot_spikes_from_lems_file(
                lems_file,
                show_plots_already=args.showPlotsAlready,
                save_spike_plot_to=args.saveSpikePlotTo,
                rates=args.rates,
                rate_window=args.rateWindow,
                rate_bins=args.rateBins,
            )
    elif spike_data_files:
        plot_spikes_from_data_files(
            args.spiketimeFiles,
            args.format,
            show_plots_already=args.showPlotsAlready,
            save_spike_plot_to=args.saveSpikePlotTo,
            rates=args.rates,
            rate_window=args.rateWindow,
            rate_bins=args.rateBins,
        )
    else:
        print("Please provide either spike data files or a LEMS simulation file.")


if __name__ == "__main__":
    main()
