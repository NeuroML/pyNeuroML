#!/usr/bin/env python3
"""
Utility methods related to xml processing

File: pyneuroml/utils/xml.py

Copyright 2024 NeuroML contributors
"""

import typing
from lxml import etree


def _find_elements(el: etree.Element, name: str, rdf: bool = False) -> typing.Iterator:
    """Find elements with name in an XML string with root el

    :param el: root element
    :type el: etree.Element
    :param name: name of element to find
    :type name: str
    :param rdf: toggle whether elements are in an RDF namespace
    :type rdf: bool
    :returns: iterator over elements with name
    """
    ns = "http://www.neuroml.org/schema/neuroml2"
    if rdf:
        ns = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    return el.findall(".//{%s}%s" % (ns, name))


def _get_attr_in_element(
    el: etree.Element, name: str, rdf: bool = False
) -> typing.Optional[str]:
    """Get value of an attribute name in element el

    :param el: element
    :type el: etree.Element
    :param name: attribute name
    :type name: str
    :param rdf: toggle whether elements are in an RDF namespace
    :type rdf: bool
    :returns: value of attribute or None of no attribute is found
    """
    ns = "http://www.neuroml.org/schema/neuroml2"
    if rdf:
        ns = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    aname = "{%s}%s" % (ns, name)
    return el.attrib[aname] if aname in el.attrib else None
