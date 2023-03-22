#!/usr/bin/env python3
"""
Test pynml.channelml

File: tests/channelml/test_channelml.py

Copyright 2023 NeuroML contributors
"""

import unittest
import logging
import pathlib as pl

from pyneuroml.channelml import channelml2nml
from pyneuroml.pynml import validate_neuroml2
from .. import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestChannelML(BaseTestCase):

    """Test ChannelML module"""

    def test_channelml2nml(self):
        """Test channelml2nml function."""
        cwd = pl.Path(__file__).parent
        # CaPool: does not validate: missing an NmlId, which needs to be added
        # manually
        # NaChannel_HH: uses general gateHH which needs to be update to use a
        # particular type of gateHH
        # NMDA: not quite sure
        for file in ["DoubExpSyn", "SingleExpSyn"]:
            inputfile = str(cwd / pl.Path(f"{file}.xml"))
            outfile = f"{file}.channel.nml"
            retval = channelml2nml(inputfile)
            print(retval)
            with open(outfile, "w") as f:
                print(retval, file=f, flush=True)
            self.assertTrue(validate_neuroml2(outfile))
            pl.Path(outfile).unlink()


if __name__ == "__main__":
    unittest.main()
