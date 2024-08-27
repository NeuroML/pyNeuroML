#!/usr/bin/env python3
"""
Test morphology plotters

File: tests/plot/test_morphology_plot.py

Copyright 2023 NeuroML contributors
"""

import logging
import os
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
    make_cell_upright,
    plot_3D_cell_morphology,
    plot_3D_schematic,
    plot_interactive_3D,
)
from pyneuroml.pynml import read_neuroml2_file

from .. import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@pytest.fixture(scope="class", autouse=True)
def change_test_dir(request):
    # Store the current working directory
    original_dir = os.getcwd()

    # Change to the desired directory
    os.chdir("./tests/plot/")

    # After the test class completes, revert to the original directory
    def teardown():
        os.chdir(original_dir)

    request.addfinalizer(teardown)


class TestMorphologyPlot(BaseTestCase):
    """Test Plot module"""

    def test_2d_point_plotter(self):
        """Test plot_2D_point_cells function."""
        nml_files = ["Izh2007Cells.net.nml"]
        for nml_file in nml_files:
            ofile = pl.Path(nml_file).name
            for plane in ["xy"]:
                filename = f"test_morphology_plot_2d_point_{ofile.replace('.', '_', 100)}_{plane}.png"
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
        nml_files = ["Izh2007Cells.net.nml"]
        for nml_file in nml_files:
            plot_interactive_3D(nml_file, theme="dark", nogui=True)

    def test_2d_plotter(self):
        """Test plot_2D function."""
        nml_files = ["Cell_497232312.cell.nml", "test.cell.nml"]
        for nml_file in nml_files:
            ofile = pl.Path(nml_file).name
            for plane in ["yz"]:
                filename = f"test_morphology_plot_2d_{ofile.replace('.', '_', 100)}_{plane}.png"
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
        nml_files = ["Cell_497232312.cell.nml"]
        for nml_file in nml_files:
            nml_doc = read_neuroml2_file(nml_file)
            cell: neuroml.Cell = nml_doc.cells[0]
            ofile = pl.Path(nml_file).name
            plane = "xy"
            filename = f"test_morphology_plot_2d_{ofile.replace('.', '_', 100)}_{plane}_with_data.png"
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
        os.chdir("L23-example/")
        nml_file = "TestNetwork.net.nml"
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
        os.chdir("../")

    def test_2d_plotter_network_with_detailed_spec(self):
        os.chdir("L23-example/")
        nml_file = "TestNetwork.net.nml"
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
        os.chdir("../")

    def test_2d_plotter_network(self):
        """Test plot_2D function with a network of a few cells."""
        os.chdir("L23-example/")
        nml_file = "TestNetwork.net.nml"
        ofile = pl.Path(nml_file).name
        for plane in ["yz"]:
            filename = (
                f"test_morphology_plot_2d_{ofile.replace('.', '_', 100)}_{plane}.png"
            )
            # remove the file first
            try:
                pl.Path(filename).unlink()
            except FileNotFoundError:
                pass

            plot_2D(nml_file, nogui=True, plane2d=plane, save_to_file=filename)

            self.assertIsFile(filename)
            pl.Path(filename).unlink()
        os.chdir("../")

    def test_2d_constant_plotter_network(self):
        """Test plot_2D_schematic function with a network of a few cells."""
        os.chdir("L23-example/")
        nml_file = "TestNetwork.net.nml"
        ofile = pl.Path(nml_file).name
        for plane in ["xz"]:
            filename = f"test_morphology_plot_2d_{ofile.replace('.', '_', 100)}_{plane}_constant.png"
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
        os.chdir("../")

    def test_2d_schematic_plotter_network(self):
        """Test plot_2D_schematic function with a network of a few cells."""
        os.chdir("L23-example/")
        nml_file = "TestNetwork.net.nml"
        ofile = pl.Path(nml_file).name
        for plane in ["xy"]:
            filename = f"test_morphology_plot_2d_{ofile.replace('.', '_', 100)}_{plane}_schematic.png"
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
        os.chdir("../")

    @pytest.mark.localonly
    def test_3d_schematic_plotter(self):
        """Test plot_3D_schematic plotter function."""
        os.chdir("L23-example/")
        nml_file = "HL23PYR.cell.nml"
        nml_doc = read_neuroml2_file(nml_file)
        cell: neuroml.Cell = nml_doc.cells[0]
        plot_3D_schematic(
            cell,
            segment_groups=None,
            nogui=True,
        )
        os.chdir("../")

    @pytest.mark.localonly
    def test_3d_morphology_plotter_vispy_network(self):
        """Test plot_3D_cell_morphology_vispy function."""
        os.chdir("L23-example/")
        nml_file = "TestNetwork.net.nml"
        plot_interactive_3D(nml_file, min_width=1, nogui=True, theme="dark")
        os.chdir("../")

    @pytest.mark.localonly
    def test_3d_morphology_plotter_vispy_network_with_spec(self):
        """Test plot_3D_cell_morphology_vispy function."""
        os.chdir("L23-example/")
        nml_file = "TestNetwork.net.nml"
        plot_interactive_3D(
            nml_file,
            min_width=1,
            nogui=True,
            theme="dark",
            plot_spec={"point_fraction": 0.5},
        )
        os.chdir("../")

    @pytest.mark.localonly
    def test_3d_morphology_plotter_vispy_network_with_spec2(self):
        """Test plot_3D_cell_morphology_vispy function."""
        os.chdir("L23-example/")
        nml_file = "TestNetwork.net.nml"
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
        os.chdir("../")

    @pytest.mark.localonly
    def test_3d_plotter_vispy_morph_only(self):
        """Test plot_interactive_3D function with morphology only NeuroML document."""
        os.chdir("L23-example/")
        nml_file = "HL23VIP.morph.cell.nml"
        plot_interactive_3D(nml_file)
        os.chdir("../")

    @pytest.mark.localonly
    def test_3d_plotter_vispy(self):
        """Test plot_3D_cell_morphology_vispy function."""
        os.chdir("L23-example/")
        nml_file = "HL23PYR.cell.nml"
        nml_doc = read_neuroml2_file(nml_file)
        cell: neuroml.Cell = nml_doc.cells[0]
        plot_3D_cell_morphology(
            cell=cell, nogui=True, color="Groups", verbose=True, plot_type="constant"
        )
        os.chdir("../")

        # test a circular soma
        nml_file = "test-spherical-soma.cell.nml"
        nml_doc = read_neuroml2_file(nml_file)
        cell: neuroml.Cell = nml_doc.cells[0]
        plot_3D_cell_morphology(
            cell=cell, nogui=True, color="Groups", verbose=True, plot_type="constant"
        )

    def test_3d_plotter_plotly(self):
        """Test plot_3D_cell_morphology_plotly function."""
        nml_files = ["Cell_497232312.cell.nml", "test.cell.nml"]
        for nml_file in nml_files:
            ofile = pl.Path(nml_file).name
            filename = f"test_morphology_plot_3d_{ofile.replace('.', '_', 100)}.png"
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
        nml_file = "Cell_497232312.cell.nml"
        olm_file = "test.cell.nml"

        nml_doc = read_neuroml2_file(nml_file)
        cell: neuroml.Cell = nml_doc.cells[0]
        ofile = pl.Path(nml_file).name

        olm_doc = read_neuroml2_file(olm_file)
        olm_cell: neuroml.Cell = olm_doc.cells[0]
        olm_ofile = pl.Path(olm_file).name

        for plane in ["xy", "yz", "xz"]:
            # olm cell
            filename = (
                f"test_schematic_plot_2d_{olm_ofile.replace('.', '_', 100)}_{plane}.png"
            )
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
            filename = (
                f"test_schematic_plot_2d_{ofile.replace('.', '_', 100)}_{plane}.png"
            )
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
        nml_file = "Cell_497232312.cell.nml"

        nml_doc = read_neuroml2_file(nml_file)
        cell: neuroml.Cell = nml_doc.cells[0]
        ofile = pl.Path(nml_file).name

        # more complex cell
        filename = f"test_curtain_plot_2d_{ofile.replace('.', '_', 100)}.png"
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
        nml_file = "Cell_497232312.cell.nml"

        nml_doc = read_neuroml2_file(nml_file)
        cell: neuroml.Cell = nml_doc.cells[0]
        ofile = pl.Path(nml_file).name

        # more complex cell
        filename = f"test_curtain_plot_2d_{ofile.replace('.', '_', 100)}_withdata.png"
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

    def test_PCA_transformation(self):
        """Test principle component axis rotation after PCA cell transformation"""

        acell = neuroml.utils.component_factory("Cell", id="test_cell", validate=False)  # type: neuroml.Cell
        acell.set_spike_thresh("10mV")
        soma = acell.add_segment(
            prox=[0, 0, 0, 15],
            dist=[10, 0, 0, 15],
            seg_id=0,
            use_convention=False,
            reorder_segment_groups=False,
            optimise_segment_groups=False,
        )

        acell.add_segment(
            prox=[10, 0, 0, 12],
            dist=[110, 0, 0, 12],
            seg_id=1,
            use_convention=False,
            reorder_segment_groups=False,
            optimise_segment_groups=False,
            parent=soma,
        )

        acell.add_segment(
            prox=[110, 0, 0, 7],
            dist=[250, 0, 0, 7],
            seg_id=2,
            use_convention=False,
            reorder_segment_groups=False,
            optimise_segment_groups=False,
            parent=soma,
        )

        acell.add_segment(
            prox=[250, 0, 0, 4],
            dist=[320, 0, 0, 4],
            seg_id=3,
            use_convention=False,
            reorder_segment_groups=False,
            optimise_segment_groups=False,
            parent=soma,
        )

        print(f"cell before: {acell}")

        transformed_cell = make_cell_upright(acell)
        transformed_cell.id = "test_transformed_cell"
        print(f"cell after transformation: {transformed_cell}")

        # Get all segments' distal points
        segment_points = []
        segments_all = transformed_cell.morphology.segments
        for segment in segments_all:
            segment_points.append(
                [segment.distal.x, segment.distal.y, segment.distal.z]
            )

        coords = numpy.array(segment_points)
        from sklearn.decomposition import PCA

        # Get the PCA components
        pca = PCA()
        pca.fit(coords)
        # Get the principal component axes
        first_pca = pca.components_
        pca_goal = numpy.array([0, first_pca[0][1], 0])
        # Test if PCA of transformed cell is on y axis
        print(f"type first pca {first_pca} and type pca_goal {pca_goal}")
        numpy.testing.assert_almost_equal(pca_goal, first_pca[0], 3)
