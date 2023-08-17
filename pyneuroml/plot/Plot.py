#!/usr/bin/env python3
"""
Plotting helper functions.

File: pyneuroml/plot/Plot.py

Copyright 2023 NeuroML contributors
"""

import os
import logging
import typing
import matplotlib
import matplotlib.axes

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def generate_plot(
    xvalues: typing.List[typing.List[float]],
    yvalues: typing.List[typing.List[float]],
    title: str,
    labels: typing.Optional[typing.List[str]] = None,
    colors: typing.Optional[typing.List[str]] = None,
    linestyles: typing.Optional[typing.List[str]] = None,
    linewidths: typing.Optional[typing.List[str]] = None,
    markers: typing.Optional[typing.List[str]] = None,
    markersizes: typing.Optional[typing.List[str]] = None,
    xaxis: str = None,
    yaxis: str = None,
    xlim: typing.List[float] = None,
    ylim: typing.List[float] = None,
    show_xticklabels: bool = True,
    show_yticklabels: bool = True,
    grid: bool = False,
    logx: bool = False,
    logy: bool = False,
    font_size: int = 12,
    bottom_left_spines_only: bool = False,
    cols_in_legend_box: int = 3,
    legend_position: typing.Optional[str] = "best",
    show_plot_already: bool = True,
    save_figure_to: typing.Optional[str] = None,
    title_above_plot: bool = False,
    verbose: bool = False,
    close_plot: bool = False,
) -> typing.Optional[matplotlib.axes.Axes]:
    """Utility function to generate plots using the Matplotlib library.

    This function can be used to generate graphs with multiple plot lines.
    For example, to plot two metrics you can use:

    ::

        generate_plot(xvalues=[[ax1, ax2, ax3], [bx1, bx2, bx3]], yvalues=[[ay1, ay2, ay3], [by1, by2, by3]], labels=["metric 1", "metric 2"])

    Please note that while plotting multiple plots, you should take care to
    ensure that the number of x values and y values for each metric correspond.
    These lists are passed directly to Matplotlib for plotting without
    additional sanity checks.

    Please see the Matplotlib documentation for the complete list of available
    styles and colours:
    - https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.plot.html
    - https://matplotlib.org/stable/gallery/index.html

    :param xvalues: X values
    :type xvalues: list of lists
    :param yvalues: Y values
    :type yvalues: lists of lists
    :param title: title of plot
    :type title: str
    :param labels: labels for each plot (default: None)
    :type labels: list of strings
    :param colors: colours for each plot (default: None)
    :type colors: list of strings
    :param linestyles: list of line styles (default: None)
    :type linestyles: list strings
    :param linewidths: list of line widths (default: None)
    :type linewidths: list of floats
    :param markers: list of markers (default: None)
    :type markers: list strings
    :param markersizes: list of marker sizes (default: None)
    :type markersizes: list of floats
    :param xaxis: label of X axis (default: None)
    :type xaxis: str
    :param yaxis: label of Y axis (default: None)
    :type yaxis: str
    :param xlim: left and right extents of x axis (default: None)
    :type xlim: tuple of (float, float) or individual arguments: (left=float), (right=float)
                See https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.xlim.html
    :param ylim: top and bottom extents of y axis (default: None)
    :type ylim: tuple of (float, float) or individual arguments: (top=float), (bottom=float)
                See https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.ylim.html
    :param show_xticklabels: whether labels should be shown on xtics (default: True)
    :type show_xticklabels: boolean
    :param show_yticklabels: whether labels should be shown on ytics (default: True)
    :type show_yticklabels: boolean
    :param grid: enable/disable grid (default: False)
    :type grid: boolean
    :param logx: should the x axis be in log scale (default: False)
    :type logx: boolean
    :param logy: should the y ayis be in log scale (default: False)
    :type logy: boolean
    :param font_size: font size (default: 12)
    :type font_size: float
    :param bottom_left_spines_only: enable/disable spines on right and top (default: False)
                (a spine is the line noting the data area boundary)
    :type bottom_left_spines_only: boolean
    :param cols_in_legend_box: number of columns to use in legend box (default: 3)
    :type cols_in_legend_box: float
    :param legend_position: position of legend:
                See: https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.legend.html
                Extra options:

                - "outer right" places the legend on the right, but outside the axes box
                - "bottom center" places the legend on the bottom, below the
                  figure

    :type legend_position: str
    :param show_plot_already: if plot should be shown when created (default: True)
    :type show_plot_already: boolean
    :param save_figure_to: location to save generated figure to (default: None)
    :type save_figure_to: str
    :param title_above_plot: enable/disable title above the plot (default: False)
    :type title_above_plot: boolean
    :param verbose: enable/disable verbose logging (default: False)
    :type verbose: boolean
    :param close_plot: call pyplot.close() to close plot after plotting
    :type close_plot: bool
    :returns: matplotlib.axes.Axes object if plot is not closed, else None
    """

    logger.info("Generating plot: %s" % (title))

    from matplotlib import pyplot as plt
    from matplotlib import rcParams

    rcParams.update({"font.size": font_size})

    fig = plt.figure()
    ax = fig.add_subplot(111)

    plt.get_current_fig_manager().set_window_title(title)
    if title_above_plot:
        plt.title(title)

    if xaxis:
        plt.xlabel(xaxis)
    if yaxis:
        plt.ylabel(yaxis)

    if grid:
        plt.grid("on")

    if logx:
        ax.set_xscale("log")
    if logy:
        ax.set_yscale("log")

    if bottom_left_spines_only:
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        ax.yaxis.set_ticks_position("left")
        ax.xaxis.set_ticks_position("bottom")

    if not show_xticklabels:
        ax.set_xticklabels([])
    if not show_yticklabels:
        ax.set_yticklabels([])

    for i in range(len(xvalues)):

        linestyle = "-" if not linestyles else linestyles[i]
        label = "" if not labels else labels[i]
        marker = None if not markers else markers[i]
        linewidth = 1 if not linewidths else linewidths[i]
        markersize = None if not markersizes else markersizes[i]

        if colors:
            plt.plot(
                xvalues[i],
                yvalues[i],
                marker=marker,
                color=colors[i],
                markersize=markersize,
                linestyle=linestyle,
                linewidth=linewidth,
                label=label,
            )
        else:
            plt.plot(
                xvalues[i],
                yvalues[i],
                marker=marker,
                markersize=markersize,
                linestyle=linestyle,
                linewidth=linewidth,
                label=label,
            )

    if labels:
        if legend_position == "outer right":
            box = ax.get_position()
            ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
            # Put a legend to the right of the current axis
            ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))

        elif legend_position == "bottom center":
            plt.legend(
                loc="upper center",
                # to ensure it does not cover the lower axis label
                bbox_to_anchor=(0.5, -0.15),
                fancybox=True,
                shadow=True,
                ncol=cols_in_legend_box,
            )
        else:
            plt.legend(
                loc=legend_position,
                fancybox=True,
                shadow=True,
                ncol=cols_in_legend_box,
            )

    if xlim:
        plt.xlim(xlim)
    if ylim:
        plt.ylim(ylim)

    if save_figure_to:
        logger.info(
            "Saving image to %s of plot: %s" % (os.path.abspath(save_figure_to), title)
        )
        plt.savefig(save_figure_to, bbox_inches="tight")
        logger.info("Saved image to %s of plot: %s" % (save_figure_to, title))

    if show_plot_already:
        plt.show()

    if close_plot:
        logger.info("Closing plot")
        plt.close()
    else:
        return ax

    return None


def generate_interactive_plot(
    xvalues: typing.List[float],
    yvalues: typing.List[float],
    title: str,
    labels: typing.Optional[typing.List[str]] = None,
    linestyles: typing.Optional[typing.List[str]] = None,
    linewidths: typing.Optional[
        typing.Union[typing.List[int], typing.List[float]]
    ] = None,
    markers: typing.Optional[typing.Union[typing.List[str], typing.List[int]]] = None,
    markersizes: typing.Optional[
        typing.Union[typing.List[float], typing.List[int]]
    ] = None,
    plot_bgcolor: typing.Optional[str] = None,
    modes: typing.Optional[typing.List[str]] = None,
    xaxis: str = None,
    yaxis: str = None,
    legend_title: str = None,
    xaxis_color: str = "#fff",
    yaxis_color: str = "#fff",
    xaxis_width: typing.Union[float, int] = 1,
    yaxis_width: typing.Union[float, int] = 1,
    xaxis_mirror: typing.Union[str, bool] = False,
    yaxis_mirror: typing.Union[str, bool] = False,
    xaxis_spikelines: bool = False,
    yaxis_spikelines: bool = False,
    grid: bool = True,
    logx: bool = False,
    logy: bool = False,
    layout: typing.Optional[dict] = None,
    show_interactive: bool = True,
    save_figure_to: typing.Optional[str] = None,
) -> None:
    """Utility function to generate interactive plots using Plotly.

    This function can be used to generate graphs with multiple plot lines.
    For example, to plot two metrics you can use:

    ::

        generate_interactive_plot(xvalues=[[ax1, ax2, ax3], [bx1, bx2, bx3]], yvalues=[[ay1, ay2, ay3], [by1, by2, by3]], labels=["metric 1", "metric 2"])

    Please note that while plotting multiple plots, you should take care to
    ensure that the number of x values and y values for each metric correspond.
    These lists are passed directly to Plotly for plotting without additional
    sanity checks.

    A number of options are provided for convenience to allow plotting of
    multiple traces in the same plot and modification of common layout options.
    A layout dict can also be passed instead, which will overwrite any
    individually set options. If you need more customisation, please look at
    the source code of this method to write your own.

    See the plotly documentation for more information:
    https://plotly.com/python-api-reference/generated/plotly.graph_objects.scatter.html

    :param xvalues: X values
    :type xvalues: list of lists
    :param yvalues: Y values
    :type yvalues: lists of lists
    :param title: title of plot
    :type title: str
    :param labels: labels for each plot (default: None)
    :type labels: list of strings
    :param modes: modes of individual plots: "markers", "lines",
        "lines+markers": default "lines+markers"
    :type modes: str
    :param linestyles: list of line styles (default: None)
    :type linestyles: list strings
    :param linewidths: list of line widths (default: None)
    :type linewidths: list of floats/int
    :param markers: list of markers (default: None)
    :type markers: list of plotly marker values. See:
        https://plotly.com/python-api-reference/generated/plotly.graph_objects.scatter.html#plotly.graph_objects.scatter.Marker.symbol
    :param markersizes: list of marker sizes (default: None)
    :type markersizes: list of ints/floats
    :param plot_bgcolor: background color of plotting area b/w axes
        See https://plotly.com/python-api-reference/generated/plotly.graph_objects.Figure.html#plotly.graph_objects.Figure
    :type plot_bgcolor: str
    :param xaxis: label of X axis (default: None)
    :type xaxis: str
    :param yaxis: label of Y axis (default: None)
    :type yaxis: str
    :param legend_title: title of legend
    :type legend_title: str
    :param xaxis_color: color of xaxis
    :type xaxis_color: str
    :param yaxis_color: color of yaxis
    :type yaxis_color: str
    :param xaxis_width: width of xaxis
    :type xaxis_width: int/float
    :param yaxis_width: width of yaxis
    :type yaxis_width: int/float
    :param xaxis_mirror: xaxis mirror options:
        https://plotly.com/python/reference/layout/xaxis/#layout-xaxis-mirror
    :type xaxis_mirror: bool/str
    :param yaxis_mirror: yaxis mirror options
        https://plotly.com/python/reference/layout/xaxis/#layout-xaxis-mirror
    :type yaxis_mirror: bool/str
    :param xaxis_spikelines: toggle spike lines on x axis
        https://plotly.com/python/hover-text-and-formatting/#spike-lines
    :type xaxis_spikelines: bool/str
    :param yaxis_spikelines: toggle spike lines on x axis
        https://plotly.com/python/hover-text-and-formatting/#spike-lines
    :type yaxis_spikelines: bool/str
    :param grid: enable/disable grid (default: True)
    :type grid: boolean
    :param logx: should the x axis be in log scale (default: False)
    :type logx: boolean
    :param logy: should the y ayis be in log scale (default: False)
    :type logy: boolean
    :param layout: plot layout properties: these will overwrite all other
        layout options specified
        See:
        https://plotly.com/python-api-reference/generated/plotly.graph_objects.Figure.html#plotly.graph_objects.Figure.update_layout
    :type layout: dict
    :param show_interactive: toggle whether interactive plot should be opened (default: True)
    :type show_interactive: bool
    :param save_figure_to: location to save generated figure to (default: None)
        Requires the kaleido package to be installed.
        See for supported formats:
        https://plotly.com/python-api-reference/generated/plotly.graph_objects.Figure.html#plotly.graph_objects.Figure.write_image
        Note: you can also save the file from the interactive web page.
    :type save_figure_to: str
    """
    import plotly.graph_objects as go
    fig = go.Figure()

    if len(xvalues) != len(yvalues):
        raise ValueError("length of x values does not match length of y values")

    if not labels or len(labels) != len(xvalues):
        raise ValueError("labels not provided correctly")

    if not markersizes:
        markersizes = len(xvalues) * [6]
    if not markers:
        markers = len(xvalues) * [0]
    if not linestyles:
        linestyles = len(xvalues) * ["solid"]
    if not linewidths:
        linewidths = len(xvalues) * [2.0]
    if not modes:
        modes = len(xvalues) * ["lines+markers"]

    for i in range(len(xvalues)):
        fig.add_trace(
            go.Scattergl(
                x=xvalues[i],
                y=yvalues[i],
                name=labels[i],
                marker={"size": markersizes[i], "symbol": markers[i]},
                line={"dash": linestyles[i], "width": linewidths[i]},
                mode=modes[i],
            ),
        )

    fig.update_layout(
        title={"text": title, "xanchor": "auto"},
        xaxis_title=xaxis,
        yaxis_title=yaxis,
        legend_title=legend_title,
        plot_bgcolor=plot_bgcolor,
        hovermode="closest",
    )

    if logx:
        fig.update_xaxes(type="log")
    else:
        fig.update_xaxes(type="linear")
    if logy:
        fig.update_yaxes(type="log")
    else:
        fig.update_yaxes(type="linear")
    fig.update_xaxes(
        showgrid=grid,
        linecolor=xaxis_color,
        linewidth=xaxis_width,
        mirror=xaxis_mirror,
        showspikes=xaxis_spikelines,
    )
    fig.update_yaxes(
        showgrid=grid,
        linecolor=yaxis_color,
        linewidth=yaxis_width,
        mirror=yaxis_mirror,
        showspikes=yaxis_spikelines,
    )

    if layout:
        fig.update_layout(layout, overwrite=True)

    if show_interactive:
        fig.show()

    if save_figure_to:
        logger.info(
            "Saving image to %s of plot: %s" % (os.path.abspath(save_figure_to), title)
        )
        fig.write_image(save_figure_to, scale=2, width=1024, height=768)
        logger.info("Saved image to %s of plot: %s" % (save_figure_to, title))
