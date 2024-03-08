#!/usr/bin/env python3
"""
Unit tests for pynml.py

File: test/test_pynml.py

Copyright 2023 NeuroML contributors
Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com>
"""

import logging
import os
import shutil
import unittest

from pyneuroml.pynml import (
    execute_command_in_dir,
    execute_command_in_dir_with_realtime_output,
    extract_lems_definition_files,
    list_exposures,
    list_recording_paths_for_exposures,
    run_jneuroml,
    validate_neuroml2,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestJarUtils(unittest.TestCase):

    """Test jNeuroML jar related functions"""

    def test_lems_def_files_extraction(self):
        """Test extraction of NeuroML2 LEMS files from jar."""
        filelist = [
            "Cells.xml",
            "Channels.xml",
            "Inputs.xml",
            "Networks.xml",
            "NeuroML2CoreTypes.xml",
            "NeuroMLCoreCompTypes.xml",
            "NeuroMLCoreDimensions.xml",
            "PyNN.xml",
            "Simulation.xml",
            "Synapses.xml",
        ]

        extraction_dir = extract_lems_definition_files()
        newfilelist = os.listdir(extraction_dir)
        shutil.rmtree(extraction_dir[: -1 * len("NeuroML2CoreTypes/")])
        assert sorted(filelist) == sorted(newfilelist)


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
        paths = list_recording_paths_for_exposures(
            "tests/izhikevich_test_file.nml", "", "IzhNet"
        )
        print("\n".join(paths))
        # self.assertTrue("izh2007RS0/u" in paths)
        # self.assertTrue("izh2007RS0/v" in paths)

    def test_recording_path_listing_2(self):
        """Test listing of recording paths in NeuroML documents."""
        os.chdir("tests/")
        paths = list_recording_paths_for_exposures(
            "HH_example_net.nml", "hh_cell", "single_hh_cell_network"
        )
        print("\n".join(paths))
        os.chdir("../")

    def test_execute_command_in_dir(self):
        """Test execute_command_in_dir function."""
        command = "ls"
        exec_in_dir = "."
        verbose = True
        output = None
        retcode = None

        retcode, output = execute_command_in_dir(
            command, exec_in_dir, verbose=verbose, prefix=" jNeuroML >>  "
        )

        self.assertEqual(retcode, 0)
        self.assertIsNotNone(output)

        command_bad = "ls non_existent_file"
        output = None
        retcode = None
        retcode, output = execute_command_in_dir(
            command_bad, exec_in_dir, verbose=verbose, prefix=" jNeuroML >>  "
        )
        self.assertNotEqual(retcode, 0)
        self.assertIsNotNone(output)

    def test_execute_command_in_dir_with_realtime_output(self):
        """Test execute_command_in_dir_with_realtime_output function."""
        command = "ls"
        exec_in_dir = "."
        verbose = True
        success = False

        success = execute_command_in_dir_with_realtime_output(
            command, exec_in_dir, verbose=verbose, prefix=" jNeuroML >>  "
        )
        self.assertTrue(success)

        command_bad = "ls non_existent_file"
        success = True

        success = execute_command_in_dir_with_realtime_output(
            command_bad, exec_in_dir, verbose=verbose, prefix=" jNeuroML >>  "
        )
        self.assertFalse(success)

    def test_run_jneuroml(self):
        """Test run_jneuroml"""
        retstat = None
        retstat = run_jneuroml("-v", None, None)
        self.assertTrue(retstat)

        retstat = None
        retstat = run_jneuroml("-randomflag", "", "")
        self.assertFalse(retstat)

    def test_validate_neuroml2(self):
        """Test validate_neuroml2"""
        os.chdir("tests/")
        retval = None
        retval = validate_neuroml2("HH_example_k_channel.nml")
        self.assertTrue(retval)

        retval = None
        retstring = None
        retval, retstring = validate_neuroml2(
            "HH_example_k_channel.nml", return_string=True
        )
        self.assertTrue(retval)
        self.assertIn("Valid against schema and all tests", retstring)
        os.chdir("../")

        retval = None
        retstring = None
        retval, retstring = validate_neuroml2("setup.cfg", return_string=True)
        self.assertFalse(retval)
        self.assertIn("1 failed", retstring)

    # TODO: add similar validation for NeuroMLv1


if __name__ == "__main__":
    unittest.main()
