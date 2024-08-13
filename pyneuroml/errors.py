#!/usr/bin/env python3
"""
Error descriptions.

File: pyneuroml/errors.py

Copyright 2024 NeuroML contributors
"""

FILE_NOT_FOUND_ERR = 13
ARGUMENT_ERR = 14
UNKNOWN_ERR = 15


class NMLFileTypeError(RuntimeError):
    """A custom file type error to use for failing file checks."""

    pass
