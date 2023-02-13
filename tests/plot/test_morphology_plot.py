#!/usr/bin/env python3
"""
Test morphology plotters

File: tests/plot/test_morphology_plot.py

Copyright 2023 NeuroML contributors
"""


import logging
import pathlib as pl

import neuroml
from pyneuroml.plot.PlotMorphology import (plot_2D, plot_interactive_3D,
                                           plot_2D_schematic)
from pyneuroml.pynml import read_neuroml2_file
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

    def test_2d_plotter_network(self):
        """Test plot_2D function with a network of a few cells."""
        nml_file = "tests/plot/L23-example/TestNetwork.net.nml"
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

    def test_2d_schematic_plotter(self):
        """Test plot_2D_schematic function."""
        nml_file = "tests/plot/Cell_497232312.cell.nml"
        olm_file = "tests/plot/test.cell.nml"

        nml_doc = read_neuroml2_file(nml_file)
        cell = nml_doc.cells[0]  # type: neuroml.Cell
        ofile = pl.Path(nml_file).name

        olm_doc = read_neuroml2_file(olm_file)
        olm_cell = olm_doc.cells[0]  # type: neuroml.Cell
        olm_ofile = pl.Path(olm_file).name

        for plane in ["xy", "yz", "xz"]:
            # olm cell
            filename = f"test_schematic_plot_2d_{olm_ofile.replace('.', '_', 100)}_{plane}.png"
            try:
                pl.Path(filename).unlink()
            except FileNotFoundError:
                pass

            plot_2D_schematic(
                olm_cell, segment_groups=["soma_0", "dendrite_0", "axon_0"],
                nogui=False, plane2d=plane, save_to_file=filename
            )

            # more complex cell
            filename = f"test_schematic_plot_2d_{ofile.replace('.', '_', 100)}_{plane}.png"
            # remove the file first
            try:
                pl.Path(filename).unlink()
            except FileNotFoundError:
                pass

            sgs = cell.get_segment_groups_by_substring("apic_")
            sgs_1 = cell.get_segment_groups_by_substring("dend_")
            sgs_ids = list(sgs.keys()) + list(sgs_1.keys())
            plot_2D_schematic(
                cell, segment_groups=sgs_ids,
                nogui=False, plane2d=plane, save_to_file=filename
            )

            self.assertIsFile(filename)
            pl.Path(filename).unlink()
