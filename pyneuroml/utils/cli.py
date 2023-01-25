#!/usr/bin/env python3
"""
Utilities use in writing console scripts.

File: pyneuroml/utils/cli.py

Copyright 2023 NeuroML contributors
"""


import argparse
from . import convert_case


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
