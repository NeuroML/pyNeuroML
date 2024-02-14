#!/usr/bin/env python3

"""
tests for "pynml <sedml_file> -run-tellurium" feature
"""


from pyneuroml import tellurium


def test_run_tellurium_on_valid_file():
    "ensure it runs a basic sedml file without error"

    fname = "tests/sedml/test_data/valid_doc.sedml"
    tellurium.run_from_sedml_file([fname], args=[])


if __name__ == "__main__":
    test_run_tellurium_on_valid_file()
