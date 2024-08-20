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

    def test_plot_time_series_from_lems_file(self):
        """Test plot_time_series_from_lems_file function"""
        trace_file = tempfile.NamedTemporaryFile(mode="w", delete=False, dir=".")
        for i in range(0, 1000):
            print(
                f"{i/1000}\t{numpy.random.default_rng().random()}\t{numpy.random.default_rng().random()}\t{numpy.random.default_rng().random()}",
                file=trace_file,
            )
        trace_file.flush()
        trace_file.close()

        lems_contents = f"""
<Lems>

    <!--

        This LEMS file has been automatically generated using PyNeuroML v1.1.13 (libNeuroML v0.5.8)

     -->

    <!-- Specify which component to run -->
    <Target component="example_izhikevich2007network_sim"/>

    <!-- Include core NeuroML2 ComponentType definitions -->
    <Include file="Cells.xml"/>
    <Include file="Networks.xml"/>
    <Include file="Simulation.xml"/>

    <Include file="izhikevich2007_network.nml"/>

    <Simulation id="example_izhikevich2007network_sim" length="1000ms" step="0.1ms" target="IzNet" seed="123">  <!-- Note seed: ensures same random numbers used every run -->
        <OutputFile id="output0" fileName="{trace_file.name}">
            <OutputColumn id="IzhPop0[0]" quantity="IzhPop0[0]/v"/>
            <OutputColumn id="IzhPop0[1]" quantity="IzhPop0[1]/v"/>
            <OutputColumn id="IzhPop0[2]" quantity="IzhPop0[2]/v"/>
        </OutputFile>


    </Simulation>

</Lems>
        """

        lems_file = tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            dir=".",
        )
        print(lems_contents, file=lems_file)
        lems_file.flush()
        lems_file.close()

        pyplts.plot_time_series_from_lems_file(
            lems_file.name,
            title="",
            offset=False,
            show_plot_already=False,
            save_figure_to="time-series-test-from-lems-file.png",
        )
        self.assertIsFile("time-series-test-from-lems-file.png")

        pyplts.plot_time_series_from_lems_file(
            lems_file.name,
            title="",
            offset=True,
            show_plot_already=False,
            save_figure_to="time-series-test-from-lems-file-2.png",
        )
        self.assertIsFile("time-series-test-from-lems-file.png")

        os.unlink("time-series-test-from-lems-file.png")
        os.unlink("time-series-test-from-lems-file-2.png")
        os.unlink(trace_file.name)
        os.unlink(lems_file.name)


if __name__ == "__main__":
    unittest.main()
