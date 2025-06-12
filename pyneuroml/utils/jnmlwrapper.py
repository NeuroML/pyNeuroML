#!/usr/bin/env python3
"""
Simple wrapper around jNeuroML to allow users to use jnml using the version
bundled in PyNeuroML

File: pyneuroml/utils/jnmlwrapper.py

Copyright 2025 NeuroML contributors
Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com>
"""

import logging
import os
import sys

from ..runners import run_jneuroml


def __jnmlwrapper():
    """Wrapper around jNeuroML jar shipped with PyNeuroML.

    The following environment variables can be set:

    - JNML_MAX_MEMORY_LOCAL: set the maximum memory available to the Java
      Virtual Machine (default: 400M)

    """
    max_memory = os.getenv("JNML_MAX_MEMORY_LOCAL", "400M")
    logging.getLogger("pyneuroml.runners").setLevel(logging.ERROR)

    output = run_jneuroml(
        pre_args=" ".join(sys.argv[1:]),
        target_file="",
        post_args="",
        max_memory=max_memory,
        report_jnml_output=False,
        output_prefix="",
        return_string=True,
    )
    # if it errors, it'll always print out the command line output
    if output[0]:
        print(output[1])
