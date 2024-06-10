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
    plot_channel_densities,
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
        cell: neuroml.Cell = read_neuroml2_file(cell_file).cells[0]
        print(cell.id)
        channel_densities = get_channel_densities(cell)

        channel_densities_Im = channel_densities["Im"]
        data_Im = get_conductance_density_for_segments(cell, channel_densities_Im[0])
        soma_group = cell.get_all_segments_in_group("soma_group")
        self.assertEqual(data_Im[soma_group[0]], 3.06)
        self.assertEqual(data_Im[soma_group[-1]], 3.06)

        data_Im = get_conductance_density_for_segments(cell, channel_densities_Im[1])
        axon_group = cell.get_all_segments_in_group("axon_group")
        self.assertEqual(data_Im[axon_group[0]], 0.000000)

        channel_densities_Ih = channel_densities["Ih"]
        for cd in channel_densities_Ih:
            if "NonUniform" in cd.__class__.__name__:
                data_Ih = get_conductance_density_for_segments(cell, cd)
                self.assertNotIn(soma_group[0], data_Ih.keys())
                self.assertEqual(
                    len(data_Ih),
                    len(cell.get_all_segments_in_group("apical_dendrite_group")),
                )

    def test_plot_channel_densities(self):
        """Test the plot_channel_densities function."""
        cell_file = "tests/plot/L23-example/HL23PYR.cell.nml"
        cell: neuroml.Cell = read_neuroml2_file(cell_file).cells[0]

        # check with channel densities
        plot_channel_densities(
            cell,
            channel_density_ids=["Ih_apical", "Ih_somatic", "Ih_basal", "Ih"],
            distance_plots=True,
            show_plots_already=False,
            target_directory="tests/analysis",
        )
        plot_channel_densities(
            cell,
            ion_channels=["Ih"],
            distance_plots=True,
            show_plots_already=False,
            target_directory="tests/analysis",
        )
