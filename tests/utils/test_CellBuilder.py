#!/usr/bin/env python3
"""
Test the cell builder utilities

File: test_CellBuilder.py

Copyright 2021 NeuroML contributors
"""


import unittest
import tempfile
import neuroml
from neuroml import IonChannel
import pyneuroml as pynml
from pyneuroml.utils.CellBuilder import *
from neuroml import NeuroMLDocument


class CellBuilderTestCase(unittest.TestCase):

    """Test the CellBuilder module"""

    def test_simple_cell(self):
        "Test a simple cell."

        nml_doc = NeuroMLDocument(id="simple_built_cell")
        cell = create_cell("simple_cell")
        cell.notes = "NeuroML cell created by CellBuilder"

        # Add soma segment
        diam = 10.0
        soma_0 = add_segment(cell,
                             prox=[0.0, 0.0, 0.0, diam],
                             dist=[0.0, 10., 0.0, diam],
                             name="Seg0_soma_0",
                             group="soma_0")

        self.assertIsInstance(soma_0, neuroml.Segment)

        nml_doc.add(cell)

        with tempfile.NamedTemporaryFile() as test_file:
            self.assertTrue(pynml.pynml.write_neuroml2_file(nml_doc, test_file.name,
                                                            validate=True))

    def test_complex_cell(self):
        """Test a complex cell."""
        nml_doc = NeuroMLDocument(id="complex_built_cell")
        cell = create_cell("complex_cell")
        cell.notes = "NeuroML cell created by CellBuilder"

        # Add soma segment
        diam = 30.0
        soma_0 = add_segment(cell,
                             prox=[0.0, 0.0, 0.0, diam],
                             dist=[0.0, 20., 0.0, diam],
                             name="Seg0_soma_0",
                             group="soma_0")
        self.assertIsInstance(soma_0, neuroml.Segment)

        dend_0 = add_segment(cell,
                             prox=[soma_0.distal.x, soma_0.distal.y, soma_0.distal.z, 5],
                             dist=[soma_0.distal.x, soma_0.distal.y + 50, soma_0.distal.z, 2],
                             name="dend_0",
                             group="dend_0",
                             parent=soma_0)
        self.assertIsInstance(dend_0, neuroml.Segment)

        nml_doc.add(cell)

        with tempfile.NamedTemporaryFile() as test_file:
            self.assertTrue(pynml.pynml.write_neuroml2_file(nml_doc, test_file.name,
                                                            validate=True))

    def test_create_cell(self):
        """Test cell creation"""
        new_cell = create_cell(cell_id="test_cell")
        self.assertIsInstance(new_cell, neuroml.Cell)

        nml_doc = NeuroMLDocument(id="test_cell_doc")
        nml_doc.cells.append(new_cell)
        with tempfile.NamedTemporaryFile() as test_file:
            # cell does not have segments: is invalid NeuroML
            self.assertFalse(pynml.pynml.write_neuroml2_file(nml_doc, test_file.name,
                                                             validate=True))

    def test_add_segment(self):
        """Test adding a segment."""
        new_cell = create_cell(cell_id="test_cell")
        segment = add_segment(new_cell, (0, 0, 0, 20), (20, 0, 0, 20), name='soma', group='soma_group')
        self.assertIsInstance(segment, neuroml.Segment)
        self.assertEqual(segment.proximal.diameter, 20.)
        self.assertEqual(segment.proximal.x, 0.)
        self.assertEqual(segment.distal.diameter, 20.)
        self.assertEqual(segment.distal.x, 20.)

        nml_doc = NeuroMLDocument(id="test_cell_with_segment_doc")
        nml_doc.cells.append(new_cell)
        with tempfile.NamedTemporaryFile() as test_file:
            # it is now valid because the cell has a segment
            self.assertTrue(pynml.pynml.write_neuroml2_file(nml_doc, test_file.name,
                                                            validate=True))

    def test_setting_init_memb_potential(self):
        """Test adding initial membrane potential."""
        new_cell = create_cell(cell_id="test_cell")
        add_segment(new_cell, (0, 0, 0, 20), (20, 0, 0, 20), name='soma', group='soma_group')
        set_init_memb_potential(new_cell, "-65mV")

        nml_doc = NeuroMLDocument(id="test_cell_with_init_memb_pot_doc")
        nml_doc.cells.append(new_cell)
        with tempfile.NamedTemporaryFile() as test_file:
            # it is now valid because the cell has a segment
            self.assertTrue(pynml.pynml.write_neuroml2_file(nml_doc, test_file.name,
                                                            validate=True))

    @unittest.expectedFailure
    def test_setting_init_memb_potential_should_fail(self):
        """Units of membrane potential are wrong: should fail."""
        new_cell = create_cell(cell_id="test_cell")
        add_segment(new_cell, (0, 0, 0, 20), (20, 0, 0, 20), name='soma', group='soma_group')
        # Make it invalid: wrong dimensions for membrane potential
        set_init_memb_potential(new_cell, "-65 cm")

        nml_doc = NeuroMLDocument(id="test_cell_with_init_memb_pot_wrong_doc")
        nml_doc.cells.append(new_cell)
        with tempfile.NamedTemporaryFile() as test_file:
            self.assertTrue(pynml.pynml.write_neuroml2_file(nml_doc,
                                                            test_file.name,
                                                            validate=True))

    def test_setting_resistivity(self):
        """Test setting the resistivity."""
        new_cell = create_cell(cell_id="test_cell")
        add_segment(new_cell, (0, 0, 0, 20), (20, 0, 0, 20), name='soma', group='soma_group')
        set_resistivity(new_cell, "2000 ohm_cm")
        nml_doc = NeuroMLDocument(id="test_cell_with_resistivity_doc")
        nml_doc.cells.append(new_cell)
        with tempfile.NamedTemporaryFile() as test_file:
            self.assertTrue(pynml.pynml.write_neuroml2_file(nml_doc, test_file.name,
                                                            validate=True))

    @unittest.expectedFailure
    def test_setting_resistivity_should_fail(self):
        """Test setting the resistivity."""
        new_cell = create_cell(cell_id="test_cell")
        add_segment(new_cell, (0, 0, 0, 20), (20, 0, 0, 20), name='soma', group='soma_group')
        set_resistivity(new_cell, "2000 kilO")
        nml_doc = NeuroMLDocument(id="test_cell_with_resistivity_doc")
        nml_doc.cells.append(new_cell)
        with tempfile.NamedTemporaryFile() as test_file:
            self.assertTrue(pynml.pynml.write_neuroml2_file(nml_doc, test_file.name,
                                                            validate=True))

    def test_setting_specific_capacitance(self):
        """Test setting the specific_capacitance."""
        new_cell = create_cell(cell_id="test_cell")
        add_segment(new_cell, (0, 0, 0, 20), (20, 0, 0, 20), name='soma', group='soma_group')
        set_specific_capacitance(new_cell, "1.0 uF_per_cm2")
        nml_doc = NeuroMLDocument(id="test_cell_with_specific_capacitance_doc")
        nml_doc.cells.append(new_cell)
        with tempfile.NamedTemporaryFile() as test_file:
            self.assertTrue(pynml.pynml.write_neuroml2_file(nml_doc, test_file.name,
                                                            validate=True))

    @unittest.expectedFailure
    def test_setting_specific_capacitance_should_fail(self):
        """Test setting the specific_capacitance."""
        new_cell = create_cell(cell_id="test_cell")
        add_segment(new_cell, (0, 0, 0, 20), (20, 0, 0, 20), name='soma', group='soma_group')
        set_specific_capacitance(new_cell, "kilo")
        nml_doc = NeuroMLDocument(id="test_cell_with_specific_capacitance_doc")
        nml_doc.cells.append(new_cell)
        with tempfile.NamedTemporaryFile() as test_file:
            self.assertTrue(pynml.pynml.write_neuroml2_file(nml_doc, test_file.name,
                                                            validate=True))

    def test_setting_channel_density(self):
        """Test setting the channel_density."""
        new_cell = create_cell(cell_id="test_cell")
        add_segment(new_cell, (0, 0, 0, 20), (20, 0, 0, 20), name='soma', group='soma_group')
        nml_doc = NeuroMLDocument(id="test_cell_with_channel_density_doc")
        nml_doc.cells.append(new_cell)

        ion_chan = IonChannel(id="pas", conductance="10 pS",
                              type="ionChannelPassive")
        nml_doc.ion_channel.append(ion_chan)

        add_channel_density(new_cell, nml_doc, "pas_chan", "0.021 mS_per_cm2",
                            "pas", "", "-70.0 mV", "non_specific", group="all")
        with tempfile.NamedTemporaryFile(dir=".") as test_file:
            self.assertTrue(pynml.pynml.write_neuroml2_file(nml_doc,
                                                            test_file.name,
                                                            validate=True))

    @unittest.expectedFailure
    def test_setting_channel_density_should_fail(self):
        """Test setting the channel_density."""
        new_cell = create_cell(cell_id="test_cell")
        add_segment(new_cell, (0, 0, 0, 20), (20, 0, 0, 20), name='soma', group='soma_group')
        nml_doc = NeuroMLDocument(id="test_cell_with_channel_density_doc")
        nml_doc.cells.append(new_cell)

        ion_chan = IonChannel(id="pas", conductance="10 pS",
                              type="ionChannelPassive")
        nml_doc.ion_channel.append(ion_chan)

        add_channel_density(new_cell, nml_doc, "pas_chan", "NOT A NUMBER",
                            "pas", "", "-70.0 mV", "non_specific", group="all")
        with tempfile.NamedTemporaryFile(dir=".") as test_file:
            self.assertTrue(pynml.pynml.write_neuroml2_file(nml_doc,
                                                            test_file.name,
                                                            validate=True))
