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


try:
    from contextlib import chdir  # Python 3.11+
except ImportError:
    from contextlib import contextmanager

    @contextmanager
    def chdir(path):
        """chdir context manager for python < 3.11

        :param path: path to change to
        :type path: str or os.PathLike
        """
        prev_cwd = os.getcwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(prev_cwd)
