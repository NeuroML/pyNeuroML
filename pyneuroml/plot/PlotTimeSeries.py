#!/usr/bin/env python3
"""
Functions related to plotting of time series

File: pyneuroml/plot/PlotTimeSeries.py

Copyright 2024 NeuroML contributors
"""


import logging
import math
import typing

import numpy
from pyneuroml.plot.Plot import generate_plot
from matplotlib import pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def plot_time_series(
    trace_data: typing.Dict[typing.Any, typing.Any],
    title: str,
    offset: bool = True,
    show_plot_already: bool = True,
    **kwargs: typing.Any,
) -> None:
    """Plot time series data from a dictionary of data

    .. versionadded:: 1.2.2

    .. seealso::

        :py:func:`pyneuroml.plot.Plot.generate_plot`
            general plotting function

    :param trace_data: a dictionary of trace data
        the keys are used as labels in the legend.
        A 't' key must exist, which holds the time axis data.
    :type trace_data: dictionary with keys as labels, and values as the time
        series data
    :param title: plot title, use "" to leave it blank
    :type title: str
    :param offset: whether the time series should be offset from each other
        along the y axis for clarity.
        This is often useful when plotting voltage traces for a population of
        cells where overlapping traces would make it hard to see individual
        values
    :type offset: bool
    :param kwargs: other key word arguments that are passed to the
        `pyneuroml.plot.Plot.generate_plot` function
    :returns: None
    :raises ValueError: if a 't' (time) key is not found in the traces data

    """
    if "t" not in trace_data.keys():
        raise ValueError("A 't' (time) key must be provided in the trace data")

    xs = [trace_data["t"]] * (len(trace_data.keys()) - 1)
    ys = []
    labels = []

    if offset is False:
        show_plot = True
        for key, trace in trace_data.items():
            if key == "t":
                continue
            ys.append(trace)
            labels.append(key)
    else:
        show_plot = False
        miny = float(math.inf)
        maxy = float(-math.inf)

        for key, trace in trace_data.items():
            if key == "t":
                continue

            max_trace = max(trace)
            min_trace = min(trace)
            if max_trace > maxy:
                maxy = max_trace
            if min_trace < miny:
                miny = min_trace

        trace_width = abs(miny) + abs(maxy)

        # logger.debug(f"trace max, min, width are: {maxy}, {miny}, {trace_width}")
        print(f"trace max, min, width are: {maxy}, {miny}, {trace_width}")

        ctr = 0
        for key, trace in trace_data.items():
            if key == "t":
                continue
            offset_trace = numpy.array(trace) + (ctr * trace_width)
            ys.append(offset_trace)
            labels.append(key)
            ctr += 1

    ax = generate_plot(
        xvalues=xs,
        yvalues=ys,
        title=title,
        labels=labels,
        show_plot_already=show_plot,
        **kwargs,
    )

    # clear ytics
    if offset is True:
        ax.set_yticks([])

        scalebar_ = ScaleBar(dx=10, units="", length_fraction=0.25)
        ax.add_artist(scalebar_)

    if show_plot_already is True:
        plt.show()
