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

from pyneuroml.utils.nml2py import NmlPythonizer

logging.basicConfig(
    format="%(name)s (%(levelname)s) >>> %(message)s\n", level=logging.WARNING
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@pytest.fixture(autouse=True)
def to_test_dir(monkeypatch, request):
    target_dir = request.path.parent.parent
    monkeypatch.chdir(target_dir)


def test_nml2py():
    converter = NmlPythonizer("HH_example_net.nml", "temp_nml2py_1")
    files = converter.write()
    script = files[-1]

    assert Path(script).exists()
