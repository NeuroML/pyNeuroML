#!/usr/bin/env python3

from pyneuroml import sbml


def test_validate_sbml_files():
    fname = "tests/sbml/test_data/test_doc.sbml"
    doc = sbml.validate_sbml_files([fname])


def test_validate_sbml_files2():
    doc = sbml.validate_sbml_files([])


if __name__ == "__main__":
    test_validate_sbml_files()
    test_validate_sbml_files2()
