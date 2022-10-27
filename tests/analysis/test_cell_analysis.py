#!/usr/bin/env python3
"""
Test cell analysis module

File:

Copyright 2022 NeuroML contributors
"""


import unittest
import neuroml
from pyneuroml.analysis.NML2CellAnalysis import analyse_point_neuron


class TestCellAnalysis(unittest.TestCase):

    """Test CellAnalysis module"""

    def test_analyse_point_neuron(self):
        """Test analyse_point_neuron

        :param arg1: TODO
        :returns: TODO

        """
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
