#!/usr/bin/env python3
"""
Test the LEMSSimulation class

File: tests/lems/test_lemssimulation.py

Copyright 2023 NeuroML contributors
Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com>
"""

import logging
import pathlib as pl
import unittest

import pytest
from pyneuroml.lems import LEMSSimulation

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestLEMSSimulation(unittest.TestCase):

    """Test the LEMSSimulation class"""

    def test_lemssimulation_meta(self):
        """Test the LEMSSimulation class."""
        # Create a simulation instance of the model
        simulation_id = "tests-sim"
        simulation = LEMSSimulation(
            sim_id=simulation_id,
            duration=1000,
            dt=0.1,
            simulation_seed=123,
            meta={
                "for": "neuron",
                "method": "cvode",
                "abs_tolerance": "0.0001",
                "rel_tolerance": "0.0004",
            },
        )
        simulation.assign_simulation_target("some_network")
        # Save the simulation to a file
        lems_simulation_file = simulation.save_to_file()

        expected_string = '<Meta for="neuron" method="cvode" abs_tolerance="0.0001" rel_tolerance="0.0004"/>'

        with open(lems_simulation_file, "r") as f:
            self.assertIn(expected_string, f.read())

        pl.Path(lems_simulation_file).unlink()

    @pytest.mark.xfail
    def test_lemssimulation_meta_should_fail(self):
        """Test without meta to ensure it's not always added"""
        # Create a simulation instance of the model
        simulation_id = "tests-sim-failure"
        simulation = LEMSSimulation(
            sim_id=simulation_id,
            duration=1000,
            dt=0.1,
            simulation_seed=123,
        )
        simulation.assign_simulation_target("some_network")
        # Save the simulation to a file
        lems_simulation_file = simulation.save_to_file()

        expected_string = '<Meta for="neuron" method="cvode" abs_tolerance="0.0001" rel_tolerance="0.0004"/>'

        with open(lems_simulation_file, "r") as f:
            self.assertIn(expected_string, f.read())

        pl.Path(lems_simulation_file).unlink()
