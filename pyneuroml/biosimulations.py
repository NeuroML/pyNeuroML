#!/usr/bin/env python3
"""
Functions related to Biosimulations.org

File: pyneuroml/biosimulations.py

Copyright 2024 NeuroML contributors
"""


import logging
import typing

import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

biosimulators_api_url = "https://api.biosimulators.org"
biosimulations_api_url = "https://api.biosimulations.org"


def get_simulator_versions(
    simulators: typing.Union[str, typing.List[str]] = [
        "neuron",
        "netpyne",
        "tellurium",
        "pyneuroml",
        "pyneuroml",
        "xpp",
        "brian2",
        "copasi",
    ]
):
    """Get simulator list from biosimulators.

    :param simulators: a simulator or list of simulators to get versions for
    :type simulators: str or list(str)
    :returns: json response from API
    :rtype: str
    """
    if type(simulators) is str:
        simulators = [simulators]
    all_siminfo = {}  # type: typing.Dict[str, typing.List[str]]
    for sim in simulators:
        resp = requests.get(f"{biosimulators_api_url}/simulators/{sim}")
        siminfo = resp.json()
        for s in siminfo:
            try:
                all_siminfo[s["id"]].append(s["version"])
            except KeyError:
                all_siminfo[s["id"]] = [s["version"]]

    return all_siminfo
