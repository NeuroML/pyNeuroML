#!/usr/bin/env python3

from pyneuroml import sbml

fname = "test_data/test_doc.sbml"
doc = sbml.validate_sbml_files(fname)
