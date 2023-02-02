#!/usr/bin/env python3
"""
Enter one line description here.

File:

Copyright 2023 Ankur Sinha
Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com>
"""

import unittest
import logging
import pathlib as pl
from pyneuroml.utils.recording import (record_exposure_from_segments)
from pyneuroml.lems import LEMSSimulation
import neuroml
from neuroml.utils import component_factory
from neuroml.loaders import read_neuroml2_file

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestRecordingUtils(unittest.TestCase):

    """Tests for utils/recording.py"""

    def test_record_exposure_from_segments(self):
        """Test record_exposure_from_segments"""
        sim_id = "test_sim"
        segs = ["0", "1", "2", "3", "20", "30"]
        test_path = "pop0/0/dummy_cell"
        sim = LEMSSimulation(sim_id=sim_id, duration=100, dt=0.01)
        sim.include_neuroml2_file("dummy_file_path.nml")
        sim.create_output_file(id="test_output", file_name="dummy_output.xml")
        record_exposure_from_segments(test_path, sim, "test_output",
                                      segs, ["v"])

        of = None
        for o in sim.lems_info["output_files"]:
            if o["id"] == "test_output":
                of = o

        columns = of["columns"]
        for s in segs:
            self.assertIn(f"{test_path.replace('/', '_')}_v", columns.keys())
            self.assertIn(f"{test_path}/v", columns.values())


if __name__ == "__main__":
    unittest.main()
