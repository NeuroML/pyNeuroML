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


from pyneuroml.neuron import load_hoc_or_python_file, morphinfo, get_utils_hoc
from pyneuroml.pynml import execute_command_in_dir


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestNeuronUtils(unittest.TestCase):

    """Test Neuron Utils"""

    def test_hoc_loader(self):
        """Test hoc loader util function"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".hoc") as f:
            print(
                """
                print "Empty test hoc file"
                """,
                file=f,
                flush=True,
            )

            self.assertTrue(load_hoc_or_python_file(f.name))

        with tempfile.NamedTemporaryFile(mode="w", suffix=".hoc") as f:
            print(
                """
                a line that should cause a syntax error
                """,
                file=f,
                flush=True,
            )

            self.assertFalse(load_hoc_or_python_file(f.name))

        # loading python files is not yet implemented
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py") as f:
            print(
                """
                print("An empty test python file")
                """,
                file=f,
                flush=True,
            )

            self.assertFalse(load_hoc_or_python_file(f.name))

    def test_get_utils_hoc(self):
        """Test the get_utils_hoc function"""
        a = get_utils_hoc()
        self.assertTrue(a.is_file())

    def test_morphinfo(self):
        """Test the morphinfo function"""
        # compile mods
        thispath = pathlib.Path(__file__)
        dirname = str(thispath.parent / pathlib.Path("test_data"))
        subprocess.run(["nrnivmodl", dirname + "/mods"])
        # must be done after mod files have been compiled
        from neuron import h

        retval = load_hoc_or_python_file(f"{dirname}/olm.hoc")
        self.assertTrue(retval)
        h("objectvar acell")
        h("acell = new olm()")
        allsections = list(h.allsec())
        logger.debug(f"All sections are: {allsections}")
        # default section is soma_0
        soma_morph = morphinfo(doprint="json")
        self.assertEqual(soma_morph["nsegs"], 1)
        self.assertEqual(soma_morph["n3d"], 3)
        self.assertEqual(soma_morph["3d points"][0]["diam"], 10.0)
        self.assertEqual(soma_morph["3d points"][1]["diam"], 10.0)
        self.assertEqual(soma_morph["3d points"][2]["diam"], 10.0)

        axon_morph = morphinfo("olm[0].axon_0", doprint="json")
        self.assertEqual(axon_morph["nsegs"], 1)
        self.assertEqual(axon_morph["n3d"], 3)
        self.assertEqual(axon_morph["3d points"][0]["diam"], 1.5)
        self.assertEqual(axon_morph["3d points"][1]["y"], -75.0)
        self.assertEqual(axon_morph["3d points"][2]["y"], -150.0)

        dend_morph = morphinfo("olm[0].dend_0", doprint="json")
        self.assertEqual(dend_morph["nsegs"], 1)
        self.assertEqual(dend_morph["n3d"], 3)
        self.assertEqual(dend_morph["3d points"][0]["diam"], 3.0)
        self.assertEqual(dend_morph["3d points"][1]["y"], 120.0)
        self.assertEqual(dend_morph["3d points"][2]["y"], 197.0)
