#!/usr/bin/env python3
"""
Test pynml.plot.Plot module

File: tests/plot/test_plot.py

Copyright 2023 NeuroML contributors
"""

import unittest
import logging
import pathlib as pl

from pyneuroml.plot import generate_plot, generate_interactive_plot
from .. import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestPlot(BaseTestCase):

    """Test Plot module"""

    def test_generate_plot(self):
        """Test generate_plot function."""
        filename = "tests/plot/test_generate_plot.png"

        # remove the file first
        try:
            pl.Path(filename).unlink()
        except FileNotFoundError:
            pass

        xs = range(0, 10)
        ys = range(0, 10)
        generate_plot(
            [xs],
            [ys],
            "Test plot",
            labels=["test"],
            linestyles=["-"],
            markers=["."],
            xaxis="x",
            yaxis="y",
            xlim="10",
            ylim="10",
            markersizes=["1"],
            grid=False,
            show_plot_already=False,
            save_figure_to=filename,
            legend_position="right",
        )
        self.assertIsFile(filename)
        pl.Path(filename).unlink()

    def test_generate_interactive_plot(self):
        """Test generate_interactive_plot function."""
        filename = "tests/plot/test_generate_interactive_plot.png"

        # remove the file first
        try:
            pl.Path(filename).unlink()
        except FileNotFoundError:
            pass

        xs = [*range(5, 15000)]
        ys = [*range(5, 15000)]
        xs1 = [*range(5, 15000)]
        ys1 = [*range(14999, 4, -1)]
        labels = ["up", "down"]
        generate_interactive_plot(
            xvalues=[xs, xs1],
            yvalues=[ys, ys1],
            labels=labels,
            modes=["lines+markers", "markers"],
            title=f"test interactive plot with {len(xs) * 2} points",
            plot_bgcolor="white",
            xaxis="x axis",
            yaxis="y axis",
            show_interactive=False,
            xaxis_spikelines=True,
            yaxis_spikelines=False,
            save_figure_to=filename,
        )
        self.assertIsFile(filename)
        pl.Path(filename).unlink()


if __name__ == "__main__":
    unittest.main()
