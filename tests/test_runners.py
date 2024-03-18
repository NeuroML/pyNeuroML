#!/usr/bin/env python3
"""
Tests for runner methods

File: tests/test_runners.py

Copyright 2024 NeuroML contributors
"""

import logging
import pathlib as pl

from pyneuroml.runners import generate_sim_scripts_in_folder, run_multiple_lems_with

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

    def test_run_multiple_lems_with(self):
        """Test the run_multiple_lems_with function."""
        spec = {
            "LEMS_NML2_Ex9_FN.xml": {
                "engine": "jneuroml_neuron",
                "args": (),
                "kwargs": {"exec_in_dir": "examples", "nogui": True},
            },
            "LEMS_NML2_Ex5_DetCell.xml": {
                "engine": "jneuroml_neuron",
                "args": (),
                "kwargs": {"exec_in_dir": "examples", "nogui": True},
            },
        }

        results = run_multiple_lems_with(2, sims_spec=spec)
        for sim, res in results.items():
            self.assertTrue(res())
