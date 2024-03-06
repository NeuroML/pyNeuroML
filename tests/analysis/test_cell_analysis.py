#!/usr/bin/env python3
"""
Test cell analysis module

File:

Copyright 2023 NeuroML contributors
"""


import unittest
import pathlib


import neuroml
from pyneuroml.analysis import generate_current_vs_frequency_curve


class TestCellAnalysis(unittest.TestCase):

    """Test cell analysis module"""

    def test_cell_analysis(self):
        """Test analyse_point_neuron"""
        doc = neuroml.Izhikevich2007Cell.component_factory("NeuroMLDocument", id="test")
        doc.add(
            "Izhikevich2007Cell",
            id="izh2007RS0",
            v0="-60mV",
            C="100pF",
            k="0.7nS_per_mV",
            vr="-60mV",
            vt="-40mV",
            vpeak="35mV",
            a="0.03per_ms",
            b="-2nS",
            c="-50.0mV",
            d="100pA",
        )
        neuroml.writers.NeuroMLWriter.write(
            doc, "tests/analysis/test_cell_analysis.cell.nml"
        )
        generate_current_vs_frequency_curve(
            "tests/analysis/test_cell_analysis.cell.nml",
            "izh2007RS0",
            plot_voltage_traces=True,
            plot_iv=True,
            show_plot_already=False,
            save_voltage_traces_to="tests/analysis/test_analysis_traces.png",
            save_if_figure_to="tests/analysis/test_analysis_if.png",
            save_iv_figure_to="tests/analysis/test_analysis_iv.png",
        )
        self.assertTrue(
            pathlib.Path("tests/analysis/test_analysis_traces.png").is_file()
        )
        self.assertTrue(pathlib.Path("tests/analysis/test_analysis_if.png").is_file())
        self.assertTrue(pathlib.Path("tests/analysis/test_analysis_iv.png").is_file())
