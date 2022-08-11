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
    plot_2D, plot_interactive_3D,
    get_sphere_surface,
    get_cylinder_surface
)
from .. import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestMorphologyPlot(BaseTestCase):

    """Test Plot module"""

    def test_2d_plotter(self):
        """Test plot_2D function."""
        nml_files = ["tests/plot/Cell_497232312.cell.nml",
                     "tests/plot/test.cell.nml"]
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
        nml_files = ["tests/plot/Cell_497232312.cell.nml",
                     "tests/plot/test.cell.nml"]
        nml_files = ["tests/plot/test.cell.nml"]
        for nml_file in nml_files:
            ofile = pl.Path(nml_file).name
            filename = f"test_morphology_plot_3d_{ofile.replace('.', '_', 100)}.png"
            # remove the file first
            try:
                pl.Path(filename).unlink()
            except FileNotFoundError:
                pass

            plot_interactive_3D(nml_file, min_width=2., nogui=False, save_to_file=filename)

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

    def test_cylinder(self):
        """Test plot_interactive_3D function."""
        X, Y, Z = get_cylinder_surface(x1=0, y1=0, z1=0, radius1=10, x2=0,
                                       y2=0, z2=10, radius2=None)
        # print("x")
        # print(X)
        # print("y")
        # print(Y)
        # print("z")
        # print(Z)
        fig = go.Figure()
        fig.add_trace(go.Surface(x=X, y=Y, z=Z,
                                 surfacecolor=(len(X) * len(Y) * ["blue"])))
        fig.show()

        """

        # Test some points we know should be in there
        self.assertAlmostEqual(-5., np.min(X), delta=0.2)
        self.assertAlmostEqual(5., np.max(X), delta=0.2)
        self.assertAlmostEqual(-5., np.min(Y), delta=0.2)
        self.assertAlmostEqual(5., np.max(Y), delta=0.2)
        self.assertAlmostEqual(-5., np.min(Z), delta=0.2)
        self.assertAlmostEqual(5., np.max(Z), delta=0.2)
        """
