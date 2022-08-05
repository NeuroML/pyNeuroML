#!/usr/bin/env python3
"""
Test pynml.plot.Plot module

File: tests/plot/test_plot.py

Copyright 2022 NeuroML contributors
"""

import unittest
import os
import shutil
import logging
import pathlib as pl

from pyneuroml.plot import (generate_plot, generate_interactive_plot)
from .. import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestPlot(BaseTestCase):

    """Test Plot module"""

    def test_generate_plot(self):
        """Test generate_plot function."""
        filename = "test_generate_plot.png"

        # remove the file first
        pl.Path(filename).unlink(missing_ok=True)

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
        xs = [*range(5, 15)]
        ys = [*range(5, 15)]
        xs1 = [*range(5, 15)]
        ys1 = [*range(14, 4, -1)]
        labels = ["up", "down"]
        generate_interactive_plot(
            [xs, xs1],
            [ys, ys1],
            "test interactive plot",
            labels,
            xaxis="x axis",
            yaxis="y axis"
        )


if __name__ == "__main__":
    unittest.main()

if __name__ == "__main__":
    unittest.main()
