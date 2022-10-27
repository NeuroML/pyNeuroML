#!/usr/bin/env python3
"""
Test cell analysis module

File:

Copyright 2022 NeuroML contributors
"""


import unittest
import pathlib


import neuroml
from pyneuroml.analysis.NML2CellAnalysis import (analyse_point_neuron,
                                                 compare_point_neurons,
                                                 analyse_multi_compartmental_neuron)


class TestCellAnalysis(unittest.TestCase):

    """Test CellAnalysis module"""

    def test_analyse_point_neuron(self):
        """Test analyse_point_neuron """
        new_izh_cell = neuroml.Izhikevich2007Cell.component_factory(
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
        )  # type: neuroml.Izhikevich2007Cell
        analyse_point_neuron(new_izh_cell, num_amplitudes=5, max_amplitude=0.1)
        self.assertTrue(pathlib.Path("izh2007RS0-fi.png").is_file())
        self.assertTrue(pathlib.Path("izh2007RS0-v.png").is_file())

    def test_compare_point_neurons(self):
        """Test compare_point_neurons """
        new_izh_cell = neuroml.Izhikevich2007Cell.component_factory(
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
        )  # type: neuroml.Izhikevich2007Cell
        new_izh_cell1 = neuroml.Izhikevich2007Cell.component_factory(
            "Izhikevich2007Cell",
            id="izh2007RS1",
            v0="-60mV",
            C="100pF",
            k="0.7nS_per_mV",
            vr="-57mV",
            vt="-40mV",
            vpeak="35mV",
            a="0.03per_ms",
            b="-2nS",
            c="-50.0mV",
            d="100pA",
        )  # type: neuroml.Izhikevich2007Cell
        compare_point_neurons([new_izh_cell, new_izh_cell1], num_amplitudes=5)
        self.assertTrue(pathlib.Path("comparison-fi.png").is_file())

    def test_analyse_multi_compartmental_neuron(self):
        """Test analyse_multi_compartmental_neuron."""
        thispath = pathlib.Path(__file__)
        dirname = str(thispath.parent)
        cell_doc = neuroml.loaders.read_neuroml2_file(dirname + "/../plot/test.cell.nml", include_includes=True)

        cell = cell_doc.cells[0]
        # add includes for ion channel definitions
        includes = []
        for x in ["leak_chan", "HCNolm", "Kdrfast", "KvAolm", "Nav"]:
            includes.append(cell_doc.component_factory("IncludeType", href=f"tests/plot/olm-example/{x}.channel.nml"))

        analyse_multi_compartmental_neuron(cell, output_segment_ids=["0", "3"],
                                           includes=includes,
                                           min_amplitude=0.01,
                                           max_amplitude=0.20,
                                           num_amplitudes=5, duration=1000,
                                           pulse_duration=500.,
                                           pulse_delay=200)

        self.assertTrue(pathlib.Path("olm-0-v.png").is_file())
        self.assertTrue(pathlib.Path("olm-3-v.png").is_file())
        self.assertTrue(pathlib.Path("olm-fi.png").is_file())
