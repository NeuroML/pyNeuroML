#!/usr/bin/env python3
"""
Test biosimulations related methods

File: tests/test_biosimulations.py

Copyright 2024 NeuroML contributors
"""


import logging

from pyneuroml.biosimulations import get_simulator_versions

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
