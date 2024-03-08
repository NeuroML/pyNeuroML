#!/usr/bin/env python3
"""
Tests for neuron utils

File: tests/neuron/__init__.py

Copyright 2023 NeuroML contributors
"""


import pathlib
import subprocess


from pyneuroml.neuron import load_hoc_or_python_file


def load_olm_cell():
    """Setup for all tests"""
    thispath = pathlib.Path(__file__)
    dirname = str(thispath.parent / pathlib.Path("test_data"))
    subprocess.run(["nrnivmodl", dirname + "/mods"])
    # must be done after mod files have been compiled
    from neuron import h

    # if the template is already defined, do not re-define.
    # NEURON doesn't like it, and I cannot figure out how to "delete" an
    # already defined template
    if hasattr(h, "olm"):
        allsections = list(h.allsec())
        return allsections
    else:
        retval = load_hoc_or_python_file(f"{dirname}/olm.hoc")
        if retval:
            h("objectvar acell")
            h("acell = new olm()")
            allsections = list(h.allsec())

            return allsections
    return []
