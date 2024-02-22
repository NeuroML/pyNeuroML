#!/usr/bin/env python3
"""
Miscellaneous utils

File: pyneuroml/utils/misc.py

Copyright 2024 NeuroML contributors
"""


import os

from pyneuroml import JNEUROML_VERSION


def get_path_to_jnml_jar() -> str:
    """Get the path to the jNeuroML jar included with PyNeuroML.

    :returns: path of jar file
    """
    script_dir = os.path.dirname(os.path.realpath(__file__))
    jar_path = os.path.join(
        script_dir,
        "./../lib",
        "jNeuroML-%s-jar-with-dependencies.jar" % JNEUROML_VERSION,
    )
    return jar_path
