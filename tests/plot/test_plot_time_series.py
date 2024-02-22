#!/usr/bin/env python3
"""
Tests for pyneuroml.plot.PlotTimeSeries

File: test/plot/test_plot_time_series.py

Copyright 2024 NeuroML contributors
"""


import os
import unittest

import numpy
import logging
import pyneuroml.plot.PlotTimeSeries as pyplts
import tempfile

from .. import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestPlotTimeSeries(BaseTestCase):
    """Test PlotTimeSeries module"""

    def test_plot_time_series(self):
        """Test plot_time_series function."""

        npoints = 1000
        traces_dict = {}
        traces_dict["t"] = list(numpy.arange(0, 1000, 1000 / npoints))

        labels = list(range(0, 3))

        for label in labels:
            traces_dict[str(label)] = list(
                numpy.random.default_rng().uniform(-30, 80, npoints)
            )

        pyplts.plot_time_series(
            traces_dict,
            title="",
            offset=False,
            show_plot_already=False,
            save_figure_to="time-series-test.png",
        )
        pyplts.plot_time_series(
            traces_dict,
            title="",
            offset=True,
            show_plot_already=False,
            save_figure_to="time-series-test-2.png",
        )
        self.assertIsFile("time-series-test.png")
        self.assertIsFile("time-series-test-2.png")

        os.unlink("time-series-test.png")
        os.unlink("time-series-test-2.png")

    def test_plot_time_series_from_data_file(self):
        """Test plot_time_series_from_data_file function"""
        trace_file = tempfile.NamedTemporaryFile(mode="w", delete=False, dir=".")
        for i in range(0, 1000):
            print(
                f"{i/1000}\t{numpy.random.default_rng().random()}\t{numpy.random.default_rng().random()}\t{numpy.random.default_rng().random()}",
                file=trace_file,
            )
        trace_file.flush()
        trace_file.close()

        pyplts.plot_time_series_from_data_files(
            trace_file.name,
            title="",
            offset=False,
            show_plot_already=False,
            save_figure_to="time-series-test-from-file.png",
        )
        self.assertIsFile("time-series-test-from-file.png")

        pyplts.plot_time_series_from_data_files(
            trace_file.name,
            title="",
            offset=True,
            show_plot_already=False,
            save_figure_to="time-series-test-from-file-2.png",
        )
        self.assertIsFile("time-series-test-from-file.png")

        os.unlink("time-series-test-from-file.png")
        os.unlink("time-series-test-from-file-2.png")
        os.unlink(trace_file.name)


if __name__ == "__main__":
    unittest.main()
