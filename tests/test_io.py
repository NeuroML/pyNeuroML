#!/usr/bin/env python3
"""
Tests for io methods

File: tests/test_io.py

Copyright 2024 NeuroML contributors
"""

import logging
import os

from pyneuroml.errors import NMLFileTypeError
from pyneuroml.io import confirm_file_type

from . import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestIo(BaseTestCase):
    """Test io module"""

    def test_confirm_file_type(self):
        """Test confirm_file_type method."""

        # LEMS file with xml extension
        test_lems_file = "a_test_lems_file.xml"
        with open(test_lems_file, "w") as f:
            print("<LEMS> </LEMS>", file=f)
        confirm_file_type(test_lems_file, ["xml"])

        # lems file with non xml extension but provided tag
        test_lems_file2 = "a_test_lems_file.lems"
        with open(test_lems_file2, "w") as f:
            print("<LEMS> </LEMS>", file=f)

        confirm_file_type(test_lems_file2, ["xml"], "lems")

        # lems file with non xml and bad tag: should fail
        with self.assertRaises(NMLFileTypeError):
            test_lems_file3 = "a_bad_test_lems_file.lems"
            with open(test_lems_file3, "w") as f:
                print("<LAMS> </LAMS>", file=f)

            confirm_file_type(test_lems_file3, ["xml"], "lems")

        os.unlink(test_lems_file)
        os.unlink(test_lems_file2)
        os.unlink(test_lems_file3)
