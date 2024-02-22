#!/usr/bin/env python3
"""
Tests for runner methods

File: tests/test_runners.py

Copyright 2024 NeuroML contributors
"""

import logging
import pathlib as pl

from pyneuroml.runners import generate_sim_scripts_in_folder

from . import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestRunners(BaseTestCase):
    """Test runners module"""

    def test_generate_sim_scripts_in_folder(self):
        """test generate_sim_scripts_in_folder method"""
        thispath = pl.Path(__file__)
        dirname = str(thispath.parent.parent)
        dirname = generate_sim_scripts_in_folder(
            engine="jneuroml_neuron",
            lems_file_name="LEMS_NML2_Ex5_DetCell.xml",
            root_dir=dirname + "/examples/",
            run_dir=str(thispath.parent),
        )
        self.assertTrue(pl.Path(dirname).exists())
        self.assertTrue(
            pl.Path(dirname + "/" + pl.Path(dirname).name + "_generated").exists()
        )
