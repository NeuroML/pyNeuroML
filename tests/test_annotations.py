#!/usr/bin/env python3
"""
Test annotations related methods

File: tests/test_annotations.py

Copyright 2024 NeuroML contributors
"""

import logging

from pyneuroml.annotations import create_annotation, extract_annotations
from pyneuroml.io import write_neuroml2_file
import neuroml
import copy

from . import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestAnnotations(BaseTestCase):
    """Test annotations module"""

    common = {
        "subject": "model.nml",
        "description": "A tests model",
        "abstract": "lol, something nice",
        "keywords": ["something", "and something"],
        "thumbnails": ["lol.png"],
        "xml_header": False,
        "organisms": {
            "http://identifiers.org/taxonomy/4896": "Schizosaccharomyces pombe"
        },
        "encodes_other_biology": {
            "http://identifiers.org/GO:0009653": "anatomical structure morphogenesis",
            "http://identifiers.org/kegg:ko04111": "Cell cycle - yeast",
        },
        "sources": {"https://github.com/lala": "GitHub"},
        "predecessors": {"http://omex-library.org/BioSim0001.omex/model.xml": "model"},
        "creation_date": "2024-04-18",
        "modified_dates": ["2024-04-18", "2024-04-19"],
        "authors": {
            "John Doe": {
                "https://someurl.com": "homepage",
                "https://anotherurl": "github",
            },
            "Jane Smith": {},
        },
        "contributors": {"Jane Doe", "John Smith", "Jane Smith"},
        "see_also": {"http://link.com": "a link"},
        "references": {"http://reference.com": "a reference"},
        "funders": {"http://afundingbody.org": "a funding body"},
        "license": {"CC0": "license"},
    }

    def test_create_annotation(self):
        """Test create_annotations"""
        common1 = copy.deepcopy(self.common)
        annotation = create_annotation(**common1, annotation_style="miriam")
        self.assertIsNotNone(annotation)
        print(annotation)

        newdoc = neuroml.NeuroMLDocument(id="test")
        newdoc.annotation = neuroml.Annotation([annotation])
        self.assertIsNone(newdoc.annotation.validate())
        self.assertIsNone(newdoc.validate(recursive=True))

        # biosimulations
        common2 = copy.deepcopy(self.common)
        annotation2 = create_annotation(**common2, annotation_style="biosimulations")
        self.assertIsNotNone(annotation2)
        print(annotation2)

    def test_extract_annotations(self):
        """Test the extract_annotations function."""
        annotation = create_annotation(
            **self.common,
            annotation_style="miriam",
        )
        self.assertIsNotNone(annotation)
        newdoc = neuroml.NeuroMLDocument(id="test")
        newdoc.annotation = neuroml.Annotation([annotation])
        write_neuroml2_file(newdoc, "TestAnnotation.xml")
        extract_annotations("TestAnnotation.xml")
