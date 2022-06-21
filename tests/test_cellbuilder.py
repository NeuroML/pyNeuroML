#!/usr/bin/env python3
"""
Unit tests for CellBuilder.py

Copyright 2022 NeuroML contributors
Author: P Gleeson
"""
import unittest

from neuroml import NeuroMLDocument
from pyneuroml import pynml


from pyneuroml.morphologies.CellBuilder import create_cell, add_segment


class TestCellBuilder(unittest.TestCase):

        def test_simple_cell(self):

            nml_cell_doc = NeuroMLDocument(id="simple_built_cell")
            cell = create_cell("simple_cell")
            cell.notes = "NeuroML cell created by CellBuilder"
            nml_cell_file = 'examples/test_data/' + cell.id + ".cell.nml"

            # Add soma segment
            diam = 10.0
            soma_0 = add_segment(cell,
                                 prox=[0.0, 0.0, 0.0, diam],
                                 dist=[0.0, 10., 0.0, diam],
                                 name="Seg0_soma_0",
                                 group="soma_0")

            nml_cell_doc.cells.append(cell)
            pynml.write_neuroml2_file(nml_cell_doc, nml_cell_file, True, True)

            from neuroml.utils import validate_neuroml2

            validate_neuroml2(nml_cell_file)

            pynml.nml2_to_png(nml_cell_file)


        def test_complex_cell(self):

            nml_cell_doc = NeuroMLDocument(id="complex_built_cell")
            cell = create_cell("complex_cell")
            cell.notes = "NeuroML cell created by CellBuilder"
            nml_cell_file = 'examples/test_data/' + cell.id + ".cell.nml"

            # Add soma segment
            diam = 30.0
            soma_0 = add_segment(cell,
                                 prox=[0.0, 0.0, 0.0, diam],
                                 dist=[0.0, 20., 0.0, diam],
                                 name="Seg0_soma_0",
                                 group="soma_0")

            dend_0 = add_segment(cell,
                                  prox=[soma_0.distal.x, soma_0.distal.y, soma_0.distal.z, 5],
                                  dist=[soma_0.distal.x, soma_0.distal.y+50, soma_0.distal.z, 2],
                                  name="dend_0",
                                  group="dend_0",
                                  parent=soma_0)

            nml_cell_doc.cells.append(cell)
            pynml.write_neuroml2_file(nml_cell_doc, nml_cell_file, True, True)

            from neuroml.utils import validate_neuroml2

            validate_neuroml2(nml_cell_file)

            pynml.nml2_to_png(nml_cell_file)


if __name__ == "__main__":
    unittest.main()
