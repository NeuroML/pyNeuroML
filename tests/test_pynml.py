#!/usr/bin/env python3
"""
Unit tests for pynml.py

File: test/test_pynml.py

Copyright 2021 NeuroML contributors
Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com>
"""

import unittest
import os
import shutil
import logging

from pyneuroml.pynml import (extract_lems_definition_files, list_exposures,
                             list_recording_paths_for_exposures)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
        newfilelist = os.listdir(extraction_dir)
        shutil.rmtree(extraction_dir[:-1 * len("NeuroML2CoreTypes/")])
        assert(sorted(filelist) == sorted(newfilelist))


class TestHelperUtils(unittest.TestCase):

    """Test helper utilities."""

    def test_exposure_listing(self):
        """Test listing of exposures in NeuroML documents."""
        exps = list_exposures("tests/izhikevich_test_file.nml", "iz")
        ctypes = {}
        for key, val in exps.items():
            ctypes[key.type] = val

        self.assertTrue("izhikevich2007Cell" in ctypes.keys())
        expnames = []
        for exp in ctypes["izhikevich2007Cell"]:
            expnames.append(exp.name)
        # https://docs.neuroml.org/Userdocs/Schemas/Cells.html#schema-izhikevich2007cell
        self.assertTrue("u" in expnames)
        self.assertTrue("v" in expnames)
        self.assertTrue("iMemb" in expnames)
        self.assertTrue("iSyn" in expnames)

    def test_exposure_listing_2(self):
        """Test listing of exposures in NeuroML documents."""
        os.chdir("tests/")
        exps = list_exposures("HH_example_net.nml")
        print(exps)
        os.chdir("../")

    def test_recording_path_listing(self):
        """Test listing of recording paths in NeuroML documents."""
        paths = list_recording_paths_for_exposures("tests/izhikevich_test_file.nml",
                                                   "", "IzhNet")
        print("\n".join(paths))
        # self.assertTrue("izh2007RS0/u" in paths)
        # self.assertTrue("izh2007RS0/v" in paths)

    def test_recording_path_listing_2(self):
        """Test listing of recording paths in NeuroML documents."""
        os.chdir("tests/")
        paths = list_recording_paths_for_exposures("HH_example_net.nml",
                                                   "hh_cell", "single_hh_cell_network")
        print("\n".join(paths))
        os.chdir("../")


if __name__ == "__main__":
    unittest.main()
