#!/usr/bin/env python3
"""
Test biosimulations related methods

File: tests/test_biosimulations.py

Copyright 2024 NeuroML contributors
"""


import logging
import os

from pyneuroml.biosimulations import (
    get_simulator_versions,
    submit_simulation,
    submit_simulation_archive,
)

from . import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestBiosimulations(BaseTestCase):
    """Test biosimulations module"""

    def test_get_simulator_versions(self):
        """Test get_simulators"""
        simulators = get_simulator_versions()

        print(simulators)

        for s in [
            "neuron",
            "netpyne",
            "tellurium",
            "pyneuroml",
            "pyneuroml",
            "xpp",
            "brian2",
            "copasi",
        ]:
            self.assertIn(s, simulators.keys())
            versions = simulators[s]
            self.assertGreater(len(versions), 0)

    def test_submit_simulation(self):
        """Test submit_simulation"""
        os.chdir("examples")
        response = submit_simulation(
            "LEMS_NML2_Ex5_DetCell.xml", sim_dict={}, dry_run=True
        )
        self.assertTrue(response)

    def test_submit_simulation_archive(self):
        """Test submit_simulation_archive"""
        dry_run = True
        os.chdir("examples")
        sim_dict = {
            "name": "PyNeuroML test simulation",
            "simulator": "neuron",
            "simulatorVersion": "8.0.2",
            "cpus": "1",
            "memory": "8",
            "maxTime": "20",
            "purpose": "other",
            "email": "something@something.com",
            "envVars": None,
            "projectId": None,
        }
        response = submit_simulation(
            "LEMS_NML2_Ex5_DetCell.xml", sim_dict=sim_dict, dry_run=dry_run
        )

        if dry_run:
            pass
        else:
            print(response.json())
            self.assertEqual(response.status_code, 201)
