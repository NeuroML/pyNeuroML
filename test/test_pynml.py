#!/usr/bin/env python3
"""
Unit tests for pynml.py

File: test/test_pynml.py

Copyright 2021 NeuroML contributors
Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com>
"""

import unittest
import os

from pyneuroml.pynml import extract_lems_definition_files


class TestJarUtils(unittest.TestCase):

    """Test jNeuroML jar related functions"""

    def test_lems_def_files_extraction(self):
        """Test extraction of NeuroML2 LEMS files from jar."""
        filelist = ["Cells.xml",
                    "Channels.xml",
                    "Inputs.xml",
                    "Networks.xml",
                    "NeuroML2CoreTypes.xml",
                    "NeuroMLCoreCompTypes.xml",
                    "NeuroMLCoreDimensions.xml",
                    "PyNN.xml",
                    "Simulation.xml",
                    "Synapses.xml"]

        extraction_dir = extract_lems_definition_files()
        newfilelist = os.listdir(extraction_dir.name + "/NeuroML2CoreTypes/")
        assert(sorted(filelist) == sorted(newfilelist))
        extraction_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
