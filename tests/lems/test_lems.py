#!/usr/bin/env python3
"""
Tests related to pyneuroml.lems module

File: tests/lems/tests_lems.py

Copyright 2024 NeuroML contributors
"""

import logging
import os
import tempfile
import unittest

import pyneuroml.lems as pyl

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestLEMSModule(unittest.TestCase):
    """Test the LEMS module"""

    def test_load_sim_data_from_lems_file(self):
        """Test the load_sim_data_from_lems_file function"""
        spike_data = """\
0       0.04350000000009967
0       0.10960000000009591
0       0.1793000000001065
0       0.2487000000001223
0       0.31810000000013805
0       0.3876000000001538
0       0.45710000000016965
0       0.5265000000001689
0       0.5961000000001057
0       0.6655000000000425
0       0.7348999999999793
0       0.8042999999999163
0       0.873899999999853
0       0.9433999999997897"""

        event_data_file = tempfile.NamedTemporaryFile(mode="w", delete=False, dir=".")
        print(spike_data, file=event_data_file)
        event_data_file.flush()
        event_data_file.close()

        trace_data = """\
0.0     -0.06
1.0E-4  -0.05993
2.0E-4  -0.05986098
3.0E-4  -0.05979291
4.0E-4  -0.059725776
5.0E-4  -0.05965956
6.0E-4  -0.05959424
7.0E-4  -0.0595298
8.0E-4  -0.05946622
9.0E-4  -0.059403483
0.001   -0.05934157
0.0011  -0.059280466
0.0012  -0.059220158
0.0013  -0.05916062
0.0014  -0.05910185
0.0015  -0.05904382
0.0016  -0.05898653
0.0017  -0.05892995
0.0018  -0.058874078
0.0019  -0.058818895"""

        trace_file = tempfile.NamedTemporaryFile(mode="w", delete=False, dir=".")
        print(trace_data, file=trace_file)
        trace_file.flush()
        trace_file.close()

        lems_contents = f"""
<Lems>

    <!--

        This LEMS file has been automatically generated using PyNeuroML v1.1.13 (libNeuroML v0.5.8)

     -->

    <!-- Specify which component to run -->
    <Target component="example_izhikevich2007network_sim"/>

    <!-- Include core NeuroML2 ComponentType definitions -->
    <Include file="Cells.xml"/>
    <Include file="Networks.xml"/>
    <Include file="Simulation.xml"/>

    <Include file="izhikevich2007_network.nml"/>

    <Simulation id="example_izhikevich2007network_sim" length="1000ms" step="0.1ms" target="IzNet" seed="123">  <!-- Note seed: ensures same random numbers used every run -->
        <EventOutputFile id="pop0" fileName="{event_data_file.name}" format="ID_TIME">
            <EventSelection id="0" select="IzPop0[0]" eventPort="spike"/>
        </EventOutputFile>
        <OutputFile id="output0" fileName="{trace_file.name}">
            <OutputColumn id="IzhPop0[0]" quantity="IzhPop0[0]/v"/>
        </OutputFile>


    </Simulation>

</Lems>
        """

        f = tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            dir=".",
        )
        print(lems_contents, file=f)
        f.flush()
        f.close()

        events = pyl.load_sim_data_from_lems_file(
            f.name, base_dir=".", get_events=True, get_traces=False
        )

        traces = pyl.load_sim_data_from_lems_file(
            f.name, base_dir=".", get_events=False, get_traces=True
        )

        self.assertIsNotNone(events)
        self.assertEqual(events["IzPop0[0]"][0], 0.04350000000009967)
        self.assertEqual(events["IzPop0[0]"][-1], 0.9433999999997897)
        print(events)

        self.assertIsNotNone(traces)
        self.assertEqual(traces["t"][0], 0.0)
        self.assertEqual(traces["t"][-1], 0.0019)
        self.assertEqual(traces["IzhPop0[0]/v"][0], -0.06)
        self.assertEqual(traces["IzhPop0[0]/v"][-1], -0.058818895)
        print(traces)

        os.unlink(f.name)
        os.unlink(event_data_file.name)
        os.unlink(trace_file.name)


if __name__ == "__main__":
    unittest.main()
