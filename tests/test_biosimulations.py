#!/usr/bin/env python3
"""
Test biosimulations related methods

File: tests/test_biosimulations.py

Copyright 2024 NeuroML contributors
"""

import logging
import os
import pathlib

from pyneuroml.biosimulations import (
    get_simulator_versions,
    submit_simulation,
)

from . import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestBiosimulations(BaseTestCase):
    """Test biosimulations module"""

    def test_get_simulator_versions(self):
        """Test get_simulators"""
        simulators = get_simulator_versions()

        logging.info(simulators)

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
        # TODO: we don't want to use the prod instance for testing, so currently
        # disabled. We'll point it at a dev instance for testingo
        # Manually set to False to test.
        dry_run = True
        thispath = pathlib.Path(__file__)
        dirname = str(thispath.parent.parent)
        cwd = os.getcwd()
        os.chdir(dirname + "/examples")
        sim_dict = {
            "name": "PyNeuroML test simulation",
            "simulator": "neuron",
            "simulatorVersion": "latest",
            "maxTime": "20",
        }

        response = submit_simulation(
            "LEMS_NML2_Ex5_DetCell.xml", sim_dict=sim_dict, dry_run=dry_run
        )
        os.chdir(cwd)

        if dry_run:
            pass
        else:
            logger.debug(response.json())
            self.assertEqual(response.status_code, 201)
