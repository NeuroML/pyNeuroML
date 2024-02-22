#!/usr/bin/env python3
"""
Test NSGR related methods

File: tests/utils/test_nsgr.py

Copyright 2024 NeuroML contributors
"""


import logging
import pathlib as pl

from pyneuroml.nsgr import run_on_nsg

from . import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestNSGR(BaseTestCase):
    """Test utils module"""

    def test_run_on_nsg(self):
        """test run_on_nsg method"""
        thispath = pl.Path(__file__)
        dirname = str(thispath.parent.parent)
        lems_file_name = "LEMS_NML2_Ex5_DetCell.xml"
        dirname = run_on_nsg(
            engine="jneuroml_neuron",
            lems_file_name=lems_file_name,
            root_dir=dirname + "/examples/",
            run_dir=str(thispath.parent),
            dry_run=True,
        )
        self.assertTrue(pl.Path(dirname).exists())
        self.assertTrue(
            pl.Path(f"{dirname}/" + lems_file_name.replace(".xml", "_NSG")).exists()
        )
