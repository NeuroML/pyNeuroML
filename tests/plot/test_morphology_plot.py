#!/usr/bin/env python3
"""
Test morphology plotters

File: tests/plot/test_morphology_plot.py

Copyright 2023 NeuroML contributors
"""

import logging
import pathlib as pl

import neuroml
import numpy
import pytest

from pyneuroml.plot.PlotMorphology import (
    plot_2D,
    plot_2D_cell_morphology,
    plot_2D_schematic,
    plot_segment_groups_curtain_plots,
)
from pyneuroml.plot.PlotMorphologyPlotly import (
    plot_3D_cell_morphology_plotly,
)
from pyneuroml.plot.PlotMorphologyVispy import (
    create_cylindrical_mesh,
    plot_3D_cell_morphology,
    plot_3D_schematic,
    plot_interactive_3D,
)
from pyneuroml.pynml import read_neuroml2_file

from .. import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestMorphologyPlot(BaseTestCase):
    """Test Plot module"""

    def test_2d_point_plotter(self):
        """Test plot_2D_point_cells function."""
        nml_files = ["tests/plot/Izh2007Cells.net.nml"]
        for nml_file in nml_files:
            ofile = pl.Path(nml_file).name
            for plane in ["xy"]:
                filename = f"tests/plot/test_morphology_plot_2d_point_{ofile.replace('.', '_', 100)}_{plane}.png"
                # remove the file first
                try:
                    pl.Path(filename).unlink()
                except FileNotFoundError:
                    pass

                plot_2D(nml_file, nogui=True, plane2d=plane, save_to_file=filename)

                self.assertIsFile(filename)
                pl.Path(filename).unlink()

    @pytest.mark.localonly
    def test_3d_point_plotter(self):
        """Test plot_2D_point_cells function."""
        nml_files = ["tests/plot/Izh2007Cells.net.nml"]
        for nml_file in nml_files:
            plot_interactive_3D(nml_file, theme="dark", nogui=True)

    def test_2d_plotter(self):
        """Test plot_2D function."""
        nml_files = ["tests/plot/Cell_497232312.cell.nml", "tests/plot/test.cell.nml"]
        for nml_file in nml_files:
            ofile = pl.Path(nml_file).name
            for plane in ["yz"]:
                filename = f"tests/plot/test_morphology_plot_2d_{ofile.replace('.', '_', 100)}_{plane}.png"
                # remove the file first
                try:
                    pl.Path(filename).unlink()
                except FileNotFoundError:
                    pass

                plot_2D(nml_file, nogui=True, plane2d=plane, save_to_file=filename)

                self.assertIsFile(filename)
                pl.Path(filename).unlink()

    def test_2d_morphology_plotter_data_overlay(self):
        """Test plot_2D_cell_morphology method with data."""
        nml_files = ["tests/plot/Cell_497232312.cell.nml"]
        for nml_file in nml_files:
            nml_doc = read_neuroml2_file(nml_file)
            cell: neuroml.Cell = nml_doc.cells[0]
            ofile = pl.Path(nml_file).name
            plane = "xy"
            filename = f"tests/plot/test_morphology_plot_2d_{ofile.replace('.', '_', 100)}_{plane}_with_data.png"
            # remove the file first
            try:
                pl.Path(filename).unlink()
            except FileNotFoundError:
                pass

            segs = cell.get_all_segments_in_group("all")
            values = list(numpy.random.randint(50, 101, 1800)) + list(
                numpy.random.randint(0, 51, len(segs) - 1800)
            )
            data_dict = dict(zip(segs, values))

            plot_2D_cell_morphology(
                cell=cell,
                nogui=True,
                plane2d=plane,
                save_to_file=filename,
                overlay_data=data_dict,
                overlay_data_label="Test",
            )

            self.assertIsFile(filename)
            pl.Path(filename).unlink()

    def test_2d_plotter_network_with_spec(self):
        """Test plot_2D function with a network of a few cells with specs."""
        nml_file = "tests/plot/L23-example/TestNetwork.net.nml"
        ofile = pl.Path(nml_file).name
        # percentage
        for plane in ["zx"]:
            filename = f"test_morphology_plot_2d_spec_{ofile.replace('.', '_', 100)}_{plane}.png"
            # remove the file first
            try:
                pl.Path(filename).unlink()
            except FileNotFoundError:
                pass

            plot_2D(
                nml_file,
                nogui=True,
                plane2d=plane,
                save_to_file=filename,
                plot_spec={"point_fraction": 0.5},
            )

            self.assertIsFile(filename)
            pl.Path(filename).unlink()

    def test_2d_plotter_network_with_detailed_spec(self):
        nml_file = "tests/plot/L23-example/TestNetwork.net.nml"
        ofile = pl.Path(nml_file).name
        # more detailed plot_spec
        for plane in ["xy"]:
            filename = f"test_morphology_plot_2d_spec_{ofile.replace('.', '_', 100)}_{plane}.png"
            # remove the file first
            try:
                pl.Path(filename).unlink()
            except FileNotFoundError:
                pass

            plot_2D(
                nml_file,
                nogui=True,
                plane2d=plane,
                save_to_file=filename,
                plot_spec={
                    "point_cells": ["HL23VIP"],
                    "detailed_cells": ["HL23PYR"],
                    "schematic_cells": ["HL23PV"],
                    "constant_cells": ["HL23SST"],
                },
            )
            self.assertIsFile(filename)
            pl.Path(filename).unlink()

    def test_2d_plotter_network(self):
        """Test plot_2D function with a network of a few cells."""
        nml_file = "tests/plot/L23-example/TestNetwork.net.nml"
        ofile = pl.Path(nml_file).name
        for plane in ["yz"]:
            filename = f"tests/plot/test_morphology_plot_2d_{ofile.replace('.', '_', 100)}_{plane}.png"
            # remove the file first
            try:
                pl.Path(filename).unlink()
            except FileNotFoundError:
                pass

            plot_2D(nml_file, nogui=True, plane2d=plane, save_to_file=filename)

            self.assertIsFile(filename)
            # pl.Path(filename).unlink()

    def test_2d_constant_plotter_network(self):
        """Test plot_2D_schematic function with a network of a few cells."""
        nml_file = "tests/plot/L23-example/TestNetwork.net.nml"
        ofile = pl.Path(nml_file).name
        for plane in ["xz"]:
            filename = f"tests/plot/test_morphology_plot_2d_{ofile.replace('.', '_', 100)}_{plane}_constant.png"
            # remove the file first
            try:
                pl.Path(filename).unlink()
            except FileNotFoundError:
                pass

            plot_2D(
                nml_file,
                nogui=True,
                plane2d=plane,
                save_to_file=filename,
                plot_type="constant",
            )

            self.assertIsFile(filename)
            pl.Path(filename).unlink()

    def test_2d_schematic_plotter_network(self):
        """Test plot_2D_schematic function with a network of a few cells."""
        nml_file = "tests/plot/L23-example/TestNetwork.net.nml"
        ofile = pl.Path(nml_file).name
        for plane in ["xy"]:
            filename = f"tests/plot/test_morphology_plot_2d_{ofile.replace('.', '_', 100)}_{plane}_schematic.png"
            # remove the file first
            try:
                pl.Path(filename).unlink()
            except FileNotFoundError:
                pass

            plot_2D(
                nml_file,
                nogui=True,
                plane2d=plane,
                save_to_file=filename,
                plot_type="schematic",
            )

            self.assertIsFile(filename)
            pl.Path(filename).unlink()

    @pytest.mark.localonly
    def test_3d_schematic_plotter(self):
        """Test plot_3D_schematic plotter function."""
        nml_file = "tests/plot/L23-example/HL23PYR.cell.nml"
        nml_doc = read_neuroml2_file(nml_file)
        cell: neuroml.Cell = nml_doc.cells[0]
        plot_3D_schematic(
            cell,
            segment_groups=None,
            nogui=True,
        )

    @pytest.mark.localonly
    def test_3d_morphology_plotter_vispy_network(self):
        """Test plot_3D_cell_morphology_vispy function."""
        nml_file = "tests/plot/L23-example/TestNetwork.net.nml"
        plot_interactive_3D(nml_file, min_width=1, nogui=True, theme="dark")

    @pytest.mark.localonly
    def test_3d_morphology_plotter_vispy_network_with_spec(self):
        """Test plot_3D_cell_morphology_vispy function."""
        nml_file = "tests/plot/L23-example/TestNetwork.net.nml"
        plot_interactive_3D(
            nml_file,
            min_width=1,
            nogui=True,
            theme="dark",
            plot_spec={"point_fraction": 0.5},
        )

    @pytest.mark.localonly
    def test_3d_morphology_plotter_vispy_network_with_spec2(self):
        """Test plot_3D_cell_morphology_vispy function."""
        nml_file = "tests/plot/L23-example/TestNetwork.net.nml"
        plot_interactive_3D(
            nml_file,
            min_width=1,
            nogui=True,
            theme="dark",
            plot_spec={
                "point_cells": ["HL23VIP"],
                "detailed_cells": ["HL23PYR"],
                "schematic_cells": ["HL23PV"],
                "constant_cells": ["HL23SST"],
            },
        )

    @pytest.mark.localonly
    def test_3d_plotter_vispy(self):
        """Test plot_3D_cell_morphology_vispy function."""
        nml_file = "tests/plot/L23-example/HL23PYR.cell.nml"
        nml_doc = read_neuroml2_file(nml_file)
        cell: neuroml.Cell = nml_doc.cells[0]
        plot_3D_cell_morphology(
            cell=cell, nogui=True, color="Groups", verbose=True, plot_type="constant"
        )

        # test a circular soma
        nml_file = "tests/plot/test-spherical-soma.cell.nml"
        nml_doc = read_neuroml2_file(nml_file)
        cell: neuroml.Cell = nml_doc.cells[0]
        plot_3D_cell_morphology(
            cell=cell, nogui=True, color="Groups", verbose=True, plot_type="constant"
        )

    def test_3d_plotter_plotly(self):
        """Test plot_3D_cell_morphology_plotly function."""
        nml_files = ["tests/plot/Cell_497232312.cell.nml", "tests/plot/test.cell.nml"]
        for nml_file in nml_files:
            ofile = pl.Path(nml_file).name
            filename = (
                f"tests/plot/test_morphology_plot_3d_{ofile.replace('.', '_', 100)}.png"
            )
            # remove the file first
            try:
                pl.Path(filename).unlink()
            except FileNotFoundError:
                pass

            plot_3D_cell_morphology_plotly(nml_file, nogui=True, save_to_file=filename)

            self.assertIsFile(filename)
            pl.Path(filename).unlink()

    def test_2d_schematic_plotter(self):
        """Test plot_2D_schematic function."""
        nml_file = "tests/plot/Cell_497232312.cell.nml"
        olm_file = "tests/plot/test.cell.nml"

        nml_doc = read_neuroml2_file(nml_file)
        cell: neuroml.Cell = nml_doc.cells[0]
        ofile = pl.Path(nml_file).name

        olm_doc = read_neuroml2_file(olm_file)
        olm_cell: neuroml.Cell = olm_doc.cells[0]
        olm_ofile = pl.Path(olm_file).name

        for plane in ["xy", "yz", "xz"]:
            # olm cell
            filename = f"tests/plot/test_schematic_plot_2d_{olm_ofile.replace('.', '_', 100)}_{plane}.png"
            try:
                pl.Path(filename).unlink()
            except FileNotFoundError:
                pass

            plot_2D_schematic(
                olm_cell,
                segment_groups=["soma_0", "dendrite_0", "axon_0"],
                nogui=True,
                plane2d=plane,
                save_to_file=filename,
            )

            # more complex cell
            filename = f"tests/plot/test_schematic_plot_2d_{ofile.replace('.', '_', 100)}_{plane}.png"
            # remove the file first
            try:
                pl.Path(filename).unlink()
            except FileNotFoundError:
                pass

            plot_2D_schematic(
                cell,
                segment_groups=None,
                nogui=True,
                plane2d=plane,
                save_to_file=filename,
                labels=True,
            )

            self.assertIsFile(filename)
            pl.Path(filename).unlink()

    def test_plot_segment_groups_curtain_plots(self):
        """Test plot_segment_groups_curtain_plots function."""
        nml_file = "tests/plot/Cell_497232312.cell.nml"

        nml_doc = read_neuroml2_file(nml_file)
        cell: neuroml.Cell = nml_doc.cells[0]
        ofile = pl.Path(nml_file).name

        # more complex cell
        filename = f"tests/plot/test_curtain_plot_2d_{ofile.replace('.', '_', 100)}.png"
        # remove the file first
        try:
            pl.Path(filename).unlink()
        except FileNotFoundError:
            pass

        sgs = cell.get_segment_groups_by_substring("apic_")
        # sgs_1 = cell.get_segment_groups_by_substring("dend_")
        sgs_ids = list(sgs.keys())  # + list(sgs_1.keys())
        plot_segment_groups_curtain_plots(
            cell,
            segment_groups=sgs_ids[0:50],
            nogui=True,
            save_to_file=filename,
            labels=True,
        )

        self.assertIsFile(filename)
        pl.Path(filename).unlink()

    def test_plot_segment_groups_curtain_plots_with_data(self):
        """Test plot_segment_groups_curtain_plots function with data overlay."""
        nml_file = "tests/plot/Cell_497232312.cell.nml"

        nml_doc = read_neuroml2_file(nml_file)
        cell: neuroml.Cell = nml_doc.cells[0]
        ofile = pl.Path(nml_file).name

        # more complex cell
        filename = f"tests/plot/test_curtain_plot_2d_{ofile.replace('.', '_', 100)}_withdata.png"
        # remove the file first
        try:
            pl.Path(filename).unlink()
        except FileNotFoundError:
            pass

        sgs = cell.get_segment_groups_by_substring("apic_")
        sgs_1 = cell.get_segment_groups_by_substring("dend_")
        sgs_ids = list(sgs.keys()) + list(sgs_1.keys())
        data_dict = {}

        nsgs = 50

        for sg_id in sgs_ids[0:nsgs]:
            lensgs = len(cell.get_all_segments_in_group(sg_id))
            data_dict[sg_id] = numpy.random.randint(0, 101, lensgs)

        plot_segment_groups_curtain_plots(
            cell,
            segment_groups=sgs_ids[0:nsgs],
            nogui=True,
            save_to_file=filename,
            labels=True,
            overlay_data=data_dict,
            overlay_data_label="Random values (0, 100)",
            width=4,
        )

        self.assertIsFile(filename)
        pl.Path(filename).unlink()

    def test_cylindrical_mesh_generator(self):
        """Test the create_cylindrical_mesh function"""
        mesh = create_cylindrical_mesh(5, 10, 1.0, 1, closed=False)
        mesh2 = create_cylindrical_mesh(5, 10, 1.0, 1, closed=True)

        self.assertEqual(mesh.n_vertices + 2, mesh2.n_vertices)
