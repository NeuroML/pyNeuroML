#!/usr/bin/env python3
"""
Methods to plot morphology using Plot.ly

Note: the vispy methods are more performant.

File: pyneuroml/plot/PlotMorphologyPlotly.py

Copyright 2023 NeuroML contributors
"""

import logging
import os
import typing

from neuroml import Cell, NeuroMLDocument

from pyneuroml.pynml import read_neuroml2_file

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    import plotly.graph_objects as go
except ImportError:
    logger.warning("Please install optional dependencies to use plotly features:")
    logger.warning("pip install pyneuroml[plotly]")


def plot_3D_cell_morphology_plotly(
    nml_file: typing.Union[str, Cell, NeuroMLDocument],
    min_width: float = 0.8,
    verbose: bool = False,
    nogui: bool = False,
    save_to_file: typing.Optional[str] = None,
    plot_type: str = "detailed",
):
    """Plot NeuroML2 cell morphology interactively using Plot.ly

    Please note that the interactive plot uses Plotly, which uses WebGL. So,
    you need to use a WebGL enabled browser, and performance here may be
    hardware dependent.

    https://plotly.com/python/webgl-vs-svg/
    https://en.wikipedia.org/wiki/WebGL

    :param nml_file: path to NeuroML cell file, or a
        :py:class:`neuroml.NeuroMLDocument` or :py:class:`neuroml.Cell` object
    :type nml_file: str or neuroml.NeuroMLDocument or neuroml.Cell
    :param min_width: minimum width for segments (useful for visualising very
        thin segments): default 0.8um
    :type min_width: float
    :param verbose: show extra information (default: False)
    :type verbose: bool
    :param nogui: do not show matplotlib GUI (default: false)
    :type nogui: bool
    :param save_to_file: optional filename to save generated morphology to
    :type save_to_file: str
    :param plot_type: type of plot, one of:

        - detailed: show detailed morphology taking into account each segment's
          width
        - constant: show morphology, but use constant line widths

    :type plot_type: str
    """
    if plot_type not in ["detailed", "constant"]:
        raise ValueError(
            "plot_type must be one of 'detailed', 'constant', or 'schematic'"
        )

    if isinstance(nml_file, str):
        nml_model = read_neuroml2_file(
            nml_file,
            include_includes=True,
            check_validity_pre_include=False,
            verbose=False,
            optimized=True,
        )
    elif isinstance(nml_file, Cell):
        nml_model = NeuroMLDocument(id="newdoc")
        nml_model.add(nml_file)
    elif isinstance(nml_file, NeuroMLDocument):
        nml_model = nml_file
    else:
        raise TypeError(
            "Passed model is not a NeuroML file path, nor a neuroml.Cell, nor a neuroml.NeuroMLDocument"
        )

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
            if plot_type == "constant":
                width = min_width
            fig.add_trace(
                go.Scatter3d(
                    x=[p.x, d.x],
                    y=[p.y, d.y],
                    z=[p.z, d.z],
                    name=None,
                    marker={"size": 2, "color": "blue"},
                    line={"width": width, "color": "blue"},
                    mode="lines",
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

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
                    title=dict(text="extent (um)"),
                ),
                yaxis=dict(
                    backgroundcolor="white",
                    showbackground=False,
                    showgrid=False,
                    showspikes=False,
                    title=dict(text="extent (um)"),
                ),
                zaxis=dict(
                    backgroundcolor="white",
                    showbackground=False,
                    showgrid=False,
                    showspikes=False,
                    title=dict(text="extent (um)"),
                ),
            ),
        )
        if not nogui:
            fig.show()
        if save_to_file:
            logger.info(
                "Saving image to %s of plot: %s"
                % (os.path.abspath(save_to_file), title)
            )
            fig.write_image(save_to_file, scale=2, width=1024, height=768)
            logger.info("Saved image to %s of plot: %s" % (save_to_file, title))
