#!/usr/bin/env python3
"""
Test pynml.plot.Plot module

File: tests/plot/test_plot.py

Copyright 2023 NeuroML contributors
"""

import random
import pytest
import unittest
import logging
import pathlib as pl

from pyneuroml.plot import generate_plot, generate_interactive_plot
from .. import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestPlot(BaseTestCase):
    """Test Plot module"""

    @pytest.mark.localonly
    def test_generate_plot_animated(self):
        """Test generate_plot function."""
        filename = "tests/plot/test_generate_plot.gif"

        # remove the file first
        try:
            pl.Path(filename).unlink()
        except FileNotFoundError:
            pass

        numpoints = 100
        xs = list(range(0, numpoints))
        ys = random.choices(list(range(0, 1000)), k=numpoints)
        ys2 = random.choices(list(range(0, 1500)), k=numpoints)

        generate_plot(
            [xs, xs],
            [ys, ys2],
            "Test plot animated",
            xaxis="x",
            yaxis="y",
            grid=False,
            show_plot_already=True,
            animate=True,
            legend_position="right",
            save_figure_to=filename,
            close_plot=True,
        )
        self.assertIsFile(filename)
        pl.Path(filename).unlink()

    @pytest.mark.localonly
    def test_generate_plot_animated_specify_writer(self):
        """Test generate_plot function with specific writer."""
        filename = "tests/plot/test_generate_plot_writer.gif"

        # remove the file first
        try:
            pl.Path(filename).unlink()
        except FileNotFoundError:
            pass

        numpoints = 100
        xs = list(range(0, numpoints))
        ys = random.choices(list(range(0, 1000)), k=numpoints)
        ys2 = random.choices(list(range(0, 1500)), k=numpoints)

        generate_plot(
            [xs, xs],
            [ys, ys2],
            "Test plot animated writer",
            xaxis="x",
            yaxis="y",
            grid=False,
            show_plot_already=True,
            animate=True,
            legend_position="right",
            save_figure_to=filename,
            animate_writer=("ffmpeg", []),
            close_plot=True,
        )
        self.assertIsFile(filename)
        pl.Path(filename).unlink()

    @pytest.mark.localonly
    def test_generate_plot_animated_should_default_pillow_when_writer_invalid(self):
        """Test generate_plot function does not fail when writer is invalid."""
        filename1 = "tests/plot/test_generate_plot_writer1.gif"
        filename2 = "tests/plot/test_generate_plot_writer2.gif"

        # remove the file first
        try:
            pl.Path(filename1).unlink()
            pl.Path(filename2).unlink()
        except FileNotFoundError:
            pass

        numpoints = 100
        xs = list(range(0, numpoints))
        ys = random.choices(list(range(0, 1000)), k=numpoints)
        ys2 = random.choices(list(range(0, 1500)), k=numpoints)

        generate_plot(
            [xs, xs],
            [ys, ys2],
            "Test plot animated writer",
            xaxis="x",
            yaxis="y",
            grid=False,
            show_plot_already=True,
            animate=True,
            legend_position="right",
            save_figure_to=filename1,
            # imagemagick is not a requirement in pyNeuroML
            animate_writer=("imagemagick", ["-quality", "100"]),
            close_plot=True,  # without this, all plots not closed will also be plotted
        )

        generate_plot(
            [xs, xs],
            [ys, ys2],
            "Test plot animated writer",
            xaxis="x",
            yaxis="y",
            grid=False,
            show_plot_already=True,
            animate=True,
            legend_position="right",
            save_figure_to=filename2,
            # tests will use pillow by default
            animate_writer=("imaginary_writer", [""]),
            close_plot=True,  # without this, all plots not closed will also be plotted
        )

        self.assertIsFile(filename1)
        self.assertIsFile(filename2)
        pl.Path(filename1).unlink()
        pl.Path(filename2).unlink()

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
            close_plot=True,
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
