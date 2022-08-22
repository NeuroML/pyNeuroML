#!/usr/bin/env python3
"""
Test neuron utils.

File: tests/neuron/test_neuron_utils.py

Copyright 2022 NeuroML contributors
"""


import unittest
import logging
import tempfile
import pathlib
import subprocess
import pytest
from _pytest.monkeypatch import MonkeyPatch


from pyneuroml.neuron import load_hoc_or_python_file, morph, get_utils_hoc
from pyneuroml.pynml import execute_command_in_dir


logger = logging.getLogger(__name__)


class TestNeuronUtils(unittest.TestCase):

    """Test Neuron Utils"""

    def test_hoc_loader(self):
        """Test hoc loader util function"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".hoc") as f:
            print(
                """
                print "Empty test hoc file"
                """, file=f, flush=True)

            self.assertTrue(load_hoc_or_python_file(f.name))

        with tempfile.NamedTemporaryFile(mode="w", suffix=".hoc") as f:
            print(
                """
                a line that should cause a syntax error
                """, file=f, flush=True)

            self.assertFalse(load_hoc_or_python_file(f.name))

        # loading python files is not yet implemented
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py") as f:
            print(
                """
                print("An empty test python file")
                """, file=f, flush=True)

            self.assertFalse(load_hoc_or_python_file(f.name))
