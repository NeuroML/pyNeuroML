#!/usr/bin/env python3
"""
Test neuron utils.

File: tests/neuron/test_neuron_utils.py

Copyright 2023 NeuroML contributors
"""


import unittest
import logging
import tempfile
import pytest
import pathlib


from pyneuroml.neuron import (
    load_hoc_or_python_file,
    morphinfo,
    get_utils_hoc,
    getinfo,
    export_mod_to_neuroml2,
)

from . import load_olm_cell


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

    @pytest.mark.localonly
    def test_morphinfo(self):
        """Test the morphinfo function"""
        if not hasattr(self, "allsections"):
            self.allsections = load_olm_cell()
        self.assertGreater(len(self.allsections), 0)
        logger.debug(f"All sections are: {self.allsections}")
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

    @pytest.mark.localonly
    def test_getinfo(self):
        """Test the getinfo function"""
        # compile mods
        if not hasattr(self, "allsections"):
            self.allsections = load_olm_cell()
        self.assertGreater(len(self.allsections), 0)
        logger.debug(f"All sections are: {self.allsections}")
        allinfo = getinfo(self.allsections, doprint="json")
        logger.debug(f"Info on all sections: {allinfo}")

        soma_0_KvAolm_gmax = allinfo["mechanisms"]["KvAolm"]["parameters"][
            "gmax_KvAolm"
        ]["values"]["olm_0_.soma_0"]["values"]["*"]
        self.assertEqual(soma_0_KvAolm_gmax, 0.00495)
        soma_0_leak_gmax = allinfo["mechanisms"]["leak_chan"]["parameters"][
            "gmax_leak_chan"
        ]["values"]["olm_0_.soma_0"]["values"]["*"]
        self.assertEqual(soma_0_leak_gmax, 1e-5)

        dend_0_KvAolm_gmax = allinfo["mechanisms"]["KvAolm"]["parameters"][
            "gmax_KvAolm"
        ]["values"]["olm_0_.dend_0"]["values"]["*"]
        self.assertEqual(dend_0_KvAolm_gmax, 0.0028)
        dend_0_leak_gmax = allinfo["mechanisms"]["leak_chan"]["parameters"][
            "gmax_leak_chan"
        ]["values"]["olm_0_.dend_0"]["values"]["*"]
        self.assertEqual(dend_0_leak_gmax, 1e-5)

        axon_0_Nav_gmax = allinfo["mechanisms"]["Nav"]["parameters"]["gmax_Nav"][
            "values"
        ]["olm_0_.axon_0"]["values"]["*"]
        self.assertEqual(axon_0_Nav_gmax, 0.01712)

        axon_0_leak_gmax = allinfo["mechanisms"]["leak_chan"]["parameters"][
            "gmax_leak_chan"
        ]["values"]["olm_0_.axon_0"]["values"]["*"]
        self.assertEqual(axon_0_leak_gmax, 1e-5)

    def test_export_mod_to_neuroml2(self):
        """Test the export_mod_to_neuroml2 method."""
        thispath = pathlib.Path(__file__)
        dirname = str(
            thispath.parent / pathlib.Path("test_data") / pathlib.Path("mods")
        )

        export_mod_to_neuroml2(str(dirname) + "/leak_chan.mod")
        path = pathlib.Path("leak_chan.channel.nml")
        self.assertTrue(path.is_file())

        export_mod_to_neuroml2(str(dirname) + "/Nav.mod")
        path = pathlib.Path("Nav.channel.nml")
        self.assertTrue(path.is_file())
