#!/usr/bin/env python3
"""
Utility methods related to xml processing

File: pyneuroml/utils/xml.py

Copyright 2024 NeuroML contributors
"""


def _find_elements(el, name, rdf=False):
    ns = "http://www.neuroml.org/schema/neuroml2"
    if rdf:
        ns = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    return el.findall(".//{%s}%s" % (ns, name))


def _get_attr_in_element(el, name, rdf=False):
    ns = "http://www.neuroml.org/schema/neuroml2"
    if rdf:
        ns = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    aname = "{%s}%s" % (ns, name)
    return el.attrib[aname] if aname in el.attrib else None
