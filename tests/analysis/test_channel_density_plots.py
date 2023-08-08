#!/usr/bin/env python3
"""
Tests for channel density plot related methods

File: tests/analysis/test_channel_density_plots.py

Copyright 2023 NeuroML contributors
"""

import logging
import unittest

import neuroml
from pyneuroml.analysis.ChannelDensityPlot import (
    get_channel_densities,
    get_conductance_density_for_segments,
)
from pyneuroml.pynml import read_neuroml2_file

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestChannelDensityPlots(unittest.TestCase):

    """Tests for ChannelDensityPlot"""

    def test_get_channel_densities(self):
        """test get_channel_densities method."""
        cell_file = "tests/plot/L23-example/HL23PYR.cell.nml"
        cell = read_neuroml2_file(cell_file).cells[0]
        print(cell.id)
        channel_densities = get_channel_densities(cell)
        total_num = 0
        for channel, densities in channel_densities.items():
            total_num += len(densities)
        self.assertEqual(total_num, 22)

    def test_get_conductance_density_for_segments(self):
        """Test get_conductance_density_for_segments."""
        cell_file = "tests/plot/L23-example/HL23PYR.cell.nml"
        cell = read_neuroml2_file(cell_file).cells[0]  # type: neuroml.Cell
        print(cell.id)
        channel_densities = get_channel_densities(cell)

        channel_densities_Im = channel_densities["Im"]
        data = get_conductance_density_for_segments(cell, channel_densities_Im[0])
        soma_group = cell.get_all_segments_in_group("soma_group")
        self.assertEqual(data[soma_group[0]], 3.06)
        self.assertEqual(data[soma_group[-1]], 3.06)
        self.assertEqual(len(data), len(cell.morphology.segments))

        data = get_conductance_density_for_segments(cell, channel_densities_Im[1])
        axon_group = cell.get_all_segments_in_group("axon_group")
        self.assertEqual(data[axon_group[0]], 0.000000)
        self.assertEqual(len(data), len(cell.morphology.segments))
