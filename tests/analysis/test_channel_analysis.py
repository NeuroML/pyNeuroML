#!/usr/bin/env python3
"""
Test NML2ChannelAnalysis

File: tests/analysis/test_channel_analysis.py

Copyright 2024 NeuroML contributors
"""

import textwrap
import unittest

import neuroml.loaders as loaders

from pyneuroml.analysis.NML2ChannelAnalysis import get_ks_channel_states


class TestChannelAnalysis(unittest.TestCase):
    """Test NML2ChannelAnalysis module"""

    def test_get_ks_channel_states(self):
        """Test get_ks_channel_states method"""
        ionchannel_nml_string = textwrap.dedent("""\
        <neuroml xmlns="http://www.neuroml.org/schema/neuroml2"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xsi:schemaLocation="http://www.neuroml.org/schema/neuroml2 https://raw.github.com/NeuroML/NeuroML2/development/Schemas/NeuroML2/NeuroML_v2.3.xsd"
                 id="NaRSG">

            <ionChannelKS id="k_vh" conductance="8pS">
                <gateKS id="n" instances="1">
                    <closedState id="c1"/>
                    <openState id="o1"/>
                    <vHalfTransition from="c1" to="o1" vHalf = "0mV" z="1.5" gamma="0.75" tau="3.2ms" tauMin="0.3ms"/>
                </gateKS>
            </ionChannelKS>

            <!-- This channel is not fully tested yet! -->
            <ionChannelKS id="k_fr"  conductance="1pS">
                <gateKS id="n" instances="1">
                    <closedState id="c1"/>
                    <openState id="o1"/>

                    <forwardTransition id="ft" from="c1" to="o1" >
                        <rate type="HHExpLinearRate" rate="0.1per_ms" midpoint="-55mV" scale="10mV"/>
                    </forwardTransition>

                    <reverseTransition id="rt" from="c1" to="o1" >
                        <rate type="HHExpRate" rate="0.125per_ms" midpoint="-65mV" scale="-80mV"/>
                    </reverseTransition>
                </gateKS>
            </ionChannelKS>
        </neuroml>

        """)

        result_dict = {"k_vh": {"n": ["c1", "o1"]}, "k_fr": {"n": ["c1", "o1"]}}
        nml_doc = loaders.read_neuroml2_string(ionchannel_nml_string)
        for ion_channel_ks in nml_doc.ion_channel_kses:
            info = get_ks_channel_states(ion_channel_ks)
            self.assertIn("n", list(info.keys()))
            self.assertGreater(len(info["n"]), 0)
            self.assertDictEqual(info, result_dict[ion_channel_ks.id])
