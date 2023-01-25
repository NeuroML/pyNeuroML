#!/usr/bin/env python3
"""
Test morphology plotters

File: tests/plot/test_morphology_plot.py

Copyright 2023 NeuroML contributors
"""


import logging
import pathlib as pl

from pyneuroml.plot.PlotMorphology import plot_2D, plot_interactive_3D
from .. import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestMorphologyPlot(BaseTestCase):

    """Test Plot module"""

    def test_2d_plotter(self):
        """Test plot_2D function."""
        nml_files = ["tests/plot/Cell_497232312.cell.nml", "tests/plot/test.cell.nml"]
        for nml_file in nml_files:
            ofile = pl.Path(nml_file).name
            for plane in ["xy", "yz", "xz"]:
                filename = f"test_morphology_plot_2d_{ofile.replace('.', '_', 100)}_{plane}.png"
                # remove the file first
                try:
                    pl.Path(filename).unlink()
                except FileNotFoundError:
                    pass

                plot_2D(nml_file, nogui=True, plane2d=plane, save_to_file=filename)

                self.assertIsFile(filename)
                pl.Path(filename).unlink()

    def test_3d_plotter(self):
        """Test plot_interactive_3D function."""
        nml_files = ["tests/plot/Cell_497232312.cell.nml", "tests/plot/test.cell.nml"]
        for nml_file in nml_files:
            ofile = pl.Path(nml_file).name
            filename = f"test_morphology_plot_3d_{ofile.replace('.', '_', 100)}.png"
            # remove the file first
            try:
                pl.Path(filename).unlink()
            except FileNotFoundError:
                pass

            plot_interactive_3D(nml_file, nogui=True, save_to_file=filename)

            self.assertIsFile(filename)
            pl.Path(filename).unlink()
