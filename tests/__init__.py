#!/usr/bin/env python3


import pathlib as pl
import unittest


class BaseTestCase(unittest.TestCase):
    """Base test case class to implement extra assertions"""

    def assertIsFile(self, path):
        """Assertion to test existence of file.

        :param path: path of file to test
        :type path: str or path object
        :raises: AssertionError

        """
        if not pl.Path(path).resolve().is_file():
            raise AssertionError(f"File does not exist: {path}")
