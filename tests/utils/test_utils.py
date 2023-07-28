#!/usr/bin/env python3
"""
Test utils

File: tests/utils/test_utils.py

Copyright 2023 NeuroML contributors
"""


import logging
import pathlib as pl

from pyneuroml.pynml import read_neuroml2_file
from pyneuroml.utils import extract_position_info, get_files_generated_after

from .. import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestUtils(BaseTestCase):

    """Test utils module"""

    def test_extract_position_info(self):
        """Test extract_position_info"""
        nml_files = ["tests/plot/L23-example/TestNetwork.net.nml"]
        for nml_file in nml_files:
            nml_model = read_neuroml2_file(
                nml_file,
                include_includes=True,
                check_validity_pre_include=False,
                verbose=True,
                optimized=True,
            )

            (
                cell_id_vs_cell,
                pop_id_vs_cell,
                positions,
                pop_id_vs_color,
                pop_id_vs_radii,
            ) = extract_position_info(nml_model)

            for c in ["HL23PV", "HL23PYR", "HL23VIP", "HL23SST"]:
                self.assertIn(c, cell_id_vs_cell.keys())

    def test_get_files_generated_after(self):
        """test get_files_generated_after method."""
        # compare to epoch, should just list all files
        files = get_files_generated_after(timestamp=0, include_suffixes=[".sh", ".ini"])
        logger.debug(files)
        current_files = list(pl.Path(".").glob("*.sh"))
        current_files.extend(list(pl.Path(".").glob("*.ini")))
        current_files = [f for f in current_files if f.is_file()]
        self.assertEqual(len(files), len(current_files))

        files = get_files_generated_after(
            timestamp=0, include_suffixes=[".sh", ".ini"], ignore_suffixes=[".sh"]
        )
        logger.debug(files)
        current_files = list(pl.Path(".").glob("*.ini"))
        current_files = [f for f in current_files if f.is_file()]
        self.assertEqual(len(files), len(current_files))
