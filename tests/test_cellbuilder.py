#!/usr/bin/env python3
"""
Unit tests for CellBuilder.py

Copyright 2022 NeuroML contributors
Author: P Gleeson
"""
import unittest
import os

from neuroml import NeuroMLDocument
from pyneuroml import pynml


from pyneuroml.morphologies.CellBuilder import create_cell, add_segment
from pyneuroml.morphologies.PlotMorphology import plot_2D


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

            self.post_process(nml_cell_file, cell)


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

            self.post_process(nml_cell_file, cell)


        def post_process(self, nml_cell_file, cell):

            from neuroml.utils import validate_neuroml2

            validate_neuroml2(nml_cell_file)

            pynml.nml2_to_png(nml_cell_file)

            img_file = '%s/%s'%(os.path.dirname(os.path.abspath(nml_cell_file)),'%s.morph.png'%cell.id)

            plot_2D(nmlFile=nml_cell_file,
                    nogui=True,
                    saveToFile=img_file,
                    v=True)


if __name__ == "__main__":
    unittest.main()
