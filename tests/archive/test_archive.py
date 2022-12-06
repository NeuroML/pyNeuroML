#!/usr/bin/env python3
"""
Tests for pyneuroml.archive module

File: test_archive.py

Copyright 2022 NeuroML contributors
"""


import unittest
import logging
import pathlib

from pyneuroml.archive import get_model_file_list, create_combine_archive


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestArchiveModule(unittest.TestCase):

    """Test the pyneuroml.archive module."""

    def test_get_model_file_list(self):
        """Test get_model_file_list."""
        # a NeuroML file in the tests directory
        thispath = pathlib.Path(__file__)
        dirname = str(thispath.parent.parent)
        filelist = []
        get_model_file_list("HH_example_cell.nml", filelist, dirname)
        self.assertEqual(4, len(filelist))

        # a LEMS file in the examples directory
        dirname = str(thispath.parent.parent.parent)
        filelist = []
        get_model_file_list(
            "LEMS_NML2_Ex5_DetCell.xml", filelist, dirname + "/examples"
        )
        self.assertEqual(5, len(filelist))
        print(filelist)

        # NeuroML file in examples directory
        dirname = str(thispath.parent.parent.parent)
        filelist = []
        get_model_file_list(
            "NML2_SingleCompHHCell.nml", filelist, dirname + "/examples"
        )
        self.assertEqual(4, len(filelist))

    def test_create_combine_archive(self):
        """Test create_combine_archive."""

        thispath = pathlib.Path(__file__)
        dirname = str(thispath.parent.parent)
        create_combine_archive("HH_example", "HH_example_cell.nml", dirname)

        dirname = str(thispath.parent.parent.parent)
        create_combine_archive(
            "LEMS_NML2_Ex5_DetCell", "LEMS_NML2_Ex5_DetCell.xml", dirname + "/examples"
        )

        dirname = str(thispath.parent.parent.parent)
        create_combine_archive(
            "NML2_SingleCompHHCell", "NML2_SingleCompHHCell.nml", dirname + "/examples"
        )
