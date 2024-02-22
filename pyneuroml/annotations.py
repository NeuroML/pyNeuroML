#!/usr/bin/env python3
"""
Methods related to annotations

File: pyneuroml/annotations.py

Copyright 2024 NeuroML contributors
"""


import logging
import pprint

from lxml import etree

from pyneuroml.utils.xml import _find_elements, _get_attr_in_element

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def extract_annotations(nml2_file: str) -> None:
    """Extract and print annotations from a NeuroML 2 file.

    :param nml2_file: name of NeuroML2 file to parse
    :type nml2_file: str
    """
    pp = pprint.PrettyPrinter()
    test_file = open(nml2_file)
    root = etree.parse(test_file).getroot()
    annotations = {}  # type: dict

    for a in _find_elements(root, "annotation"):
        for r in _find_elements(a, "Description", rdf=True):
            desc = _get_attr_in_element(r, "about", rdf=True)
            annotations[desc] = []

            for info in r:
                if isinstance(info.tag, str):
                    kind = info.tag.replace(
                        "{http://biomodels.net/biology-qualifiers/}", "bqbiol:"
                    )
                    kind = kind.replace(
                        "{http://biomodels.net/model-qualifiers/}", "bqmodel:"
                    )

                    for li in _find_elements(info, "li", rdf=True):
                        attr = _get_attr_in_element(li, "resource", rdf=True)
                        if attr:
                            annotations[desc].append({kind: attr})

    logger.info("Annotations in %s: " % (nml2_file))
    pp.pprint(annotations)
