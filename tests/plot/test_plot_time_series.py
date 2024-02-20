#!/usr/bin/env python3
"""
Tests for pyneuroml.plot.PlotTimeSeries

File: test/plot/test_plot_time_series.py

Copyright 2024 NeuroML contributors
"""


import numpy
import unittest
from pyneuroml.plot.PlotTimeSeries import *
from .. import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestPlotTimeSeries(BaseTestCase):

    """Test PlotTimeSeries module"""

    def test_plot_time_series(self):
        """Test plot_time_series function."""

        npoints = 10000
        traces_dict = {}
        traces_dict["t"] = list(numpy.arange(0, 1000, 1000 / npoints))

        labels = list(range(0, 3))

        for label in labels:
            traces_dict[str(label)] = list(
                numpy.random.default_rng().uniform(-30, 80, npoints)
            )

        plot_time_series(traces_dict, title="", offset=False, show_plot_already=True)
        plot_time_series(traces_dict, title="", offset=True, show_plot_already=True)


if __name__ == "__main__":
    unittest.main()
