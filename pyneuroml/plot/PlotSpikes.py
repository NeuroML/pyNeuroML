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
import textwrap
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np

import pyneuroml.lems as pynmll
from pyneuroml.plot import generate_plot
from pyneuroml.utils.cli import build_namespace

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

try:
    import tables  # pytables for HDF5 support
except ImportError:
    logger.warning("Please install optional dependencies to use hdf5 features:")
    logger.warning("pip install pyneuroml[hdf5]")

FORMAT_ID_T = "id_t"
FORMAT_ID_TIME_NEST_DAT = "id_t_nest_dat"
FORMAT_T_ID = "t_id"

SPIKE_PLOTTER_DEFAULTS = {
    "format": FORMAT_ID_T,
    "rates": False,
    "save_spike_plot_to": None,
    "rate_window": 50,
    "rate_bins": 500,
    "show_plots_already": True,
    "offset": True,
}

POP_NAME_SPIKEFILE_WITH_GIDS = "Spiketimes for GIDs"


def _process_spike_plotter_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    :returns: An argparse.Namespace object containing the parsed arguments.
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description="A script for plotting files containing spike time data",
        formatter_class=argparse.RawTextHelpFormatter,
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
        default=SPIKE_PLOTTER_DEFAULTS["format"],
        help=textwrap.dedent(f"""\
        How the spiketimes are represented on each line of file:

        - {FORMAT_ID_T}: id of cell, space(s) / tab(s), time of spike (default);
        - {FORMAT_ID_TIME_NEST_DAT}: id of cell, space(s) / tab(s), time of spike, allowing NEST dat file comments/metadata
        - {FORMAT_T_ID}: time of spike, space(s) / tab(s), id of cell
        - sonata: SONATA format HDF5 file containing spike times

        """),
    )

    parser.add_argument(
        "-offset",
        action="store_true",
        default=SPIKE_PLOTTER_DEFAULTS["offset"],
        help=("Toggle whether plots are overlaid or offset"),
    )

    parser.add_argument(
        "-rates",
        action="store_true",
        default=SPIKE_PLOTTER_DEFAULTS["rates"],
        help="Show a plot of rates",
    )

    parser.add_argument(
        "-showPlotsAlready",
        action="store_true",
        default=SPIKE_PLOTTER_DEFAULTS["show_plots_already"],
        help="Show plots once generated",
    )

    parser.add_argument(
        "-saveSpikePlotTo",
        type=str,
        metavar="<spiketime plot filename>",
        default=SPIKE_PLOTTER_DEFAULTS["save_spike_plot_to"],
        help="Name of file in which to save spiketime plot",
    )

    parser.add_argument(
        "-rateWindow",
        type=int,
        metavar="<rate window>",
        default=SPIKE_PLOTTER_DEFAULTS["rate_window"],
        help="Window for rate calculation in ms",
    )

    parser.add_argument(
        "-rateBins",
        type=int,
        metavar="<rate bins>",
        default=SPIKE_PLOTTER_DEFAULTS["rate_bins"],
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
    title: str = "",
    offset: bool = True,
    show_plots_already: bool = True,
    save_spike_plot_to: Optional[str] = None,
    rates: bool = False,
    rate_window: int = 50,
    rate_bins: int = 500,
    max_image_size: Optional[Tuple[int, int]] = None,
) -> None:
    """Plot spike times from data.

    :param spike_data: List of dictionaries containing spike time data. Each dictionary should have the following keys:
                        - "name" (str): Name of the population or file.
                        - "times" (List[float]): List of spike times in seconds.
                        - "ids" (List[int]): List of cell IDs corresponding to each spike time.
    :type spike_data: list of dictionaries
    :param title: Title of the plot. Defaults to an empty string.
    :type title: str
    :param offset: toggle whether different spike_data items should be offset
        along the y axis for clarity
    :type offset: bool
    :param show_plots_already: Whether to show the plots immediately after they are generated. Defaults to True.
    :type show_plots_already: bool
    :param save_spike_plot_to: Path to save the spike plot to. If `None`, the plot will not be saved. Defaults to `None`.
    :type save_spike_plot_to: str
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

    max_time = 0.0
    max_id = 0
    min_id = float("inf")
    unique_ids = []  # type: List[int]
    for data in spike_data:
        unique_ids.extend(data["ids"])
    unique_ids = list(set(unique_ids))

    times = OrderedDict()
    ids_in_file = OrderedDict()

    current_offset = 0

    for data in spike_data:
        name = data["name"]  # type: str
        x = data["times"]
        y = [int(id_ + current_offset) for id_ in data["ids"]]

        times[name] = x

        # create a copy otherwise the sort action below sorts y also!
        ids_in_file[name] = y.copy()
        max_id_here = max(y)

        max_time = max(max_time, max(x))
        max_id = max(max_id, max_id_here)
        min_id = min(min_id, min(y))

        # only show population name: since we cannot ascertain the number of
        # cells in the population simply from the data
        labels.append(name)

        xs.append(x)
        ys.append(y)
        markers.append(".")
        linestyles.append("")

        if offset is True:
            current_offset = max_id + 1
            logger.debug(f"offset is now {current_offset}")
        ids_in_file[name].sort()

    xlim = [0, max_time * 1.05]
    ylim = [min_id - 1, max_id + 1]

    markersizes = [
        "3" if len(unique_ids) <= 50 else "2" if len(unique_ids) <= 200 else "1"
        for _ in xs
    ]
    if max_image_size is not None:
        plt.figure(figsize=(max_image_size[0] / 100, max_image_size[1] / 100))

    # do not show plot here, generate all plots and show at end
    generate_plot(
        xs,
        ys,
        title=title,
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
        legend_position="bottom center",
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

            # width = bin_edges[1] - bin_edges[0]
            # mids = [i + width / 2 for i in bin_edges[:-1]]

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
    format_: str,
    show_plots_already: bool = True,
    save_spike_plot_to: Optional[str] = None,
    rates: bool = False,
    rate_window: int = 50,
    rate_bins: int = 500,
    title: str = "",
) -> None:
    """
    Plot spike times from data files.

    :param spiketime_files: List of spike time files to be plotted.
    :type spiketime_files: List[str]
    :param title: optional title for plot, empty string disables it
    :type title: str
    :param format_: Format of the spike time data in the files.

        Can be one of the following:

        - :code:`id_t`: Each line contains a cell ID (int) followed by a spike time (float).
        - :code:`id_time_nest_dat`: Each line contains a cell ID (int) followed by a spike time (float),
          with NEST-style comments allowed.
        - :code:`t_id`: Each line contains a spike time (float) followed by a cell ID (int).
        - :code:`sonata`: SONATA-style HDF5 file.

    :type format_: str
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

    if format_ == "sonata":
        for file_name in spiketime_files:
            ids_times_pops = read_sonata_spikes_hdf5_file(file_name)

            for pop in ids_times_pops:
                ids_times = ids_times_pops[pop]
                times = [t for id_, times_list in ids_times.items() for t in times_list]
                ids = [id_ for id_, times_list in ids_times.items() for _ in times_list]

                spike_data.append(
                    {"name": f"{pop} ({file_name})", "times": times, "ids": ids}
                )

    else:
        for file_name in spiketime_files:
            logger.info("Loading spike times from: %s" % file_name)
            logger.debug(f"format is: {format_}")

            name = os.path.basename(file_name)
            try:
                spike_data_array = np.loadtxt(file_name, comments="#", unpack=True)
                logger.debug(f"Dimensions of spike array are {spike_data_array.shape}")

            except ValueError:
                logger.warning(f"Invalid line format in file: {file_name}")
                continue
            if format_ == "id_t" or format_ == "id_time_nest_dat":
                ids, times = spike_data_array
            elif format_ == "t_id" or format_ == "TIME_ID":
                times, ids = spike_data_array
            else:
                logger.error("Unknown format: %s" % format_)
                raise ValueError("Unknown format: %s" % format_)
            spike_data.append(
                {"name": name, "times": times.tolist(), "ids": ids.tolist()}
            )

    plot_spikes(
        title=title,
        spike_data=spike_data,
        show_plots_already=show_plots_already,
        save_spike_plot_to=save_spike_plot_to,
        rates=rates,
        rate_window=rate_window,
        rate_bins=rate_bins,
        offset=True,
    )


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
    event_data = pynmll.load_sim_data_from_lems_file(
        lems_file_name, get_events=True, get_traces=False
    )

    spike_data = []  # type: List[Dict]
    for select, times in event_data.items():
        new_dict = {"name": select}
        new_dict["times"] = times
        # the plot_spikes function will add an offset for each data entry, so
        # we set the ids to 0 here
        new_dict["ids"] = [0] * len(times)

        spike_data.append(new_dict)

    logger.debug("Spike data is:")
    logger.debug(spike_data)

    plot_spikes(
        spike_data,
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
        args = _process_spike_plotter_args()

    a = build_namespace(SPIKE_PLOTTER_DEFAULTS, a=args)
    logger.debug(a)

    if len(a.spiketime_files) == 1 and a.spiketime_files[0].startswith("LEMS_"):
        plot_spikes_from_lems_file(
            a.spiketime_files[0],
            show_plots_already=a.show_plots_already,
            save_spike_plot_to=a.save_spike_plot_to,
            rates=a.rates,
            rate_window=a.rate_window,
            rate_bins=a.rate_bins,
        )
    else:
        title = ""
        if len(a.spiketime_files) == 1:
            title = a.spiketime_files[0]

        plot_spikes_from_data_files(
            spiketime_files=a.spiketime_files,
            format_=a.format,
            show_plots_already=a.show_plots_already,
            save_spike_plot_to=a.save_spike_plot_to,
            rates=a.rates,
            rate_window=a.rate_window,
            rate_bins=a.rate_bins,
            title=title,
        )


if __name__ == "__main__":
    main()
