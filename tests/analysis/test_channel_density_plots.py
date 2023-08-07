#!/usr/bin/env python3
"""
Tests for channel density plot related methods

File: tests/analysis/test_channel_density_plots.py

Copyright 2023 NeuroML contributors
"""

import logging
import unittest

from pyneuroml.analysis.ChannelDensityPlot import get_channel_densities
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
