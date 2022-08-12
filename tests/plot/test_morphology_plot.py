#!/usr/bin/env python3
"""
Test morphology plotters

File: tests/plot/test_morphology_plot.py

Copyright 2022 NeuroML contributors
"""


import logging
import pathlib as pl

import numpy as np
import plotly.graph_objects as go

from pyneuroml.plot.PlotMorphology import (
    plot_2D, plot_interactive_3D_web,
    plot_interactive_3D_web_naive,
    plot_interactive_3D_matplotlib,
    plot_interactive_3D_matplotlib_naive,
    plot_interactive_3D,
    get_sphere_surface,
    get_frustrum_surface,
)
from .. import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestMorphologyPlot(BaseTestCase):

    """Test Plot module"""

    def test_2d_plotter(self):
        """Test plot_2D function."""
        nml_files = ["tests/plot/olm.cell.nml",
                     "tests/plot/L23_PC_simplified.cell.nml",
                     "tests/plot/Cell_497232312.cell.nml"]
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
        nml_files = ["tests/plot/olm.cell.nml",
                     "tests/plot/L23_PC_simplified.cell.nml",
                     "tests/plot/Cell_497232312.cell.nml"]
        for nml_file in nml_files:
            ofile = pl.Path(nml_file).name

            for engine in ["matplotlib", "matplotlib_surface", "plotly"]:
                filename = f"test_morphology_plot_3d_{engine}_{ofile.replace('.', '_', 100)}.png"
            # remove the file first
            try:
                pl.Path(filename).unlink()
            except FileNotFoundError:
                pass

            plot_interactive_3D(nml_file, nogui=True,
                                save_to_file=filename, verbose=False,
                                engine=engine)

            self.assertIsFile(filename)
            pl.Path(filename).unlink()

        # only a simple morphology for plotly surface
        nml_files = ["tests/plot/olm.cell.nml"]
        for nml_file in nml_files:
            ofile = pl.Path(nml_file).name
            filename = f"test_morphology_plot_3d_plotly_surface{ofile.replace('.', '_', 100)}.png"
            # remove the file first
            try:
                pl.Path(filename).unlink()
            except FileNotFoundError:
                pass

            plot_interactive_3D(nml_file, nogui=True,
                                save_to_file=filename, verbose=False,
                                engine="plotly_surface")

            self.assertIsFile(filename)
            pl.Path(filename).unlink()

    def test_sphere(self):
        """Test plot_interactive_3D function."""
        X, Y, Z = get_sphere_surface(0, 0, 0, 5, 100)

        # Test some points we know should be in there
        self.assertAlmostEqual(-5., np.min(X), delta=0.2)
        self.assertAlmostEqual(5., np.max(X), delta=0.2)
        self.assertAlmostEqual(-5., np.min(Y), delta=0.2)
        self.assertAlmostEqual(5., np.max(Y), delta=0.2)
        self.assertAlmostEqual(-5., np.min(Z), delta=0.2)
        self.assertAlmostEqual(5., np.max(Z), delta=0.2)

    def test_frustrum(self):
        """Test plot_interactive_3D function."""
        X, Y, Z, X_cap, Y_cap, Z_cap = get_frustrum_surface(
            x1=0, y1=0, z1=0, radius1=5, x2=0, y2=0, z2=5, radius2=5,
            capped=True, resolution=40, angular_resolution=50)
        # Test some points we know should be in there
        self.assertAlmostEqual(-5., np.min(X), delta=0.2)
        self.assertAlmostEqual(5., np.max(X), delta=0.2)
        self.assertAlmostEqual(-5., np.min(Y), delta=0.2)
        self.assertAlmostEqual(5., np.max(Y), delta=0.2)
        self.assertAlmostEqual(0., np.min(Z), delta=0.2)
        self.assertAlmostEqual(5., np.max(Z), delta=0.2)
