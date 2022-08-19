#!/usr/bin/env python3
"""
Utilities use in writing console scripts.

File: pyneuroml/utils/cli.py

Copyright 2022 NeuroML contributors
"""


import argparse
import re


def convert_case(name):
    """Converts from camelCase to under_score"""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def build_namespace(DEFAULTS={}, a=None, **kwargs):
    if a is None:
        a = argparse.Namespace()

    # Add arguments passed in by keyword.
    for key, value in kwargs.items():
        setattr(a, key, value)

    # Add defaults for arguments not provided.
    for key, value in DEFAULTS.items():
        if not hasattr(a, key):
            setattr(a, key, value)
    # Change all keys to camel case
    for key, value in a.__dict__.copy().items():
        new_key = convert_case(key)
        if new_key != key:
            setattr(a, new_key, value)
            delattr(a, key)
    return a
