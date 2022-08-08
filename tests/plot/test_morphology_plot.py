#!/usr/bin/env python3
"""
Test morphology plotters

File: tests/plot/test_morphology_plot.py

Copyright 2022 NeuroML contributors
"""


import unittest
import logging
import pathlib as pl

from pyneuroml.plot.PlotMorphology import plot_2D
from .. import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestPlot(BaseTestCase):

    """Test Plot module"""

    def test_generate_plot(self):
        """Test generate_plot function."""
        filename = "test_generate_plot.png"

        # remove the file first
