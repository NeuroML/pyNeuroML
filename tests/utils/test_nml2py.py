#!/usr/bin/env python3
"""
Test nml2py.py

File: tests/utils/test_nml2py.py

Copyright 2026 Ankur Sinha
Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com>
"""

import logging
from pathlib import Path

import pytest
from neuroml.utils import component_factory

from pyneuroml.io import read_neuroml2_file
from pyneuroml.utils.nml2py import NmlPythonizer, _sanitize_var_name

logging.basicConfig(
    format="%(name)s (%(levelname)s) >>> %(message)s\n", level=logging.WARNING
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# NOTE: when using xdist, one cannot print to stdout. -s won't work.
# So, use logging, which works with xdist.


@pytest.fixture(autouse=True)
def to_test_dir(monkeypatch, request):
    target_dir = request.path.parent.parent
    monkeypatch.chdir(target_dir)


def test_nml2py():
    converter = NmlPythonizer("HH_example_net.nml", "temp_nml2py_1")
    files = converter.write()
    script = files[-1]

    assert Path(script).exists()


def test_collect_one():
    """Test _collect_one"""
    nml_doc = component_factory("NeuroMLDocument", id="nml_doc")
    net = nml_doc.add("Network", id="nml_net", validate=False)
    inc = nml_doc.add("IncludeType", href="test.nml")

    # set up mock file
    converter = NmlPythonizer("somefile.nml", "temp_nml2py_1")
    net_var = converter._collect_one(net, "nml_doc")

    assert id(net) in converter._obj_to_var
    assert converter._obj_to_var.get(id(net)) == net_var

    assert converter._collect_one(inc, "nml_doc") is None


def test_make_var_name():
    """Test _make_var_name"""
    nml_doc = component_factory("NeuroMLDocument", id="nml_doc")

    # set up mock file
    converter = NmlPythonizer("somefile.nml", "temp_nml2py_1")
    net_var = converter._make_var_name(nml_doc, "NeuroMLDocument")
    assert net_var == "nml_doc"
    assert converter._var_counters["nml_doc"] == 0


def test_sanitize_var_name_int():
    """Test _sanitize_var_name"""
    vname = _sanitize_var_name(15)
    assert vname == "_15"


def test_sanitize_var_name_str():
    """Test _sanitize_var_name"""
    vname = _sanitize_var_name("lol$name")
    assert vname == "lol_name"


def test_walk_children():
    """Test _walk_children"""
    converter = NmlPythonizer("HH_example_net.nml", "temp_nml2py_1")
    raw_doc = read_neuroml2_file("HH_example_net.nml", include_includes=False)
    converter._walk_children(raw_doc, "nml_doc")

    logger.debug(f"{converter._obj_to_var = }", flush=True)
    logger.debug(f"{converter._components = }", flush=True)

    assert True
