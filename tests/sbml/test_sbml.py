#!/usr/bin/env python3

from pyneuroml import sbml

fname = "tests/sbml/test_data/test_doc.sbml"
doc = sbml.validate_sbml_files(fname)
