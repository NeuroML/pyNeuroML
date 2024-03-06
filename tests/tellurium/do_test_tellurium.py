#!/usr/bin/env python3

"""
tests for "pynml <sedml_file> -run-tellurium" feature
named so that pytest will not test this file
rather runs directly from test-ghactions.sh
from the examples directory
as pytest is segfaulting
"""


from pyneuroml import tellurium

import os


def test_run_tellurium_on_valid_file():
    "ensure it runs a basic sedml file without error"

    fname = "../tests/sedml/test_data/valid_doc.sedml"
    tellurium.run_from_sedml_file([fname], args=["-outputdir", "none"])


def test_run_tellurium_pdf_output():
    "ensure it outputs expected pdf file"

    if os.path.exists("./d1.pdf"):
        os.unlink("./d1.pdf")

    fname = "../tests/tellurium/test_data/LEMS_NML2_Ex9_FN.sedml"
    tellurium.run_from_sedml_file([fname], args=[])

    assert os.path.exists("./d1.pdf")
    os.unlink("./d1.pdf")


def test_run_hindmarsh_rose():
    "test run of hindmarsh rose"

    fname = "../tests/tellurium/test_data/LEMS_Regular_HindmarshRose.sedml"
    tellurium.run_from_sedml_file([fname], args=["-outputdir", "none"])


if __name__ == "__main__":
    test_run_tellurium_on_valid_file()
    test_run_tellurium_pdf_output()
    test_run_hindmarsh_rose()
