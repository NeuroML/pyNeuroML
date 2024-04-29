#!/usr/bin/env python3
"""
Test annotations related methods

File: tests/test_annotations.py

Copyright 2024 NeuroML contributors
"""

import logging

from pyneuroml.annotations import create_annotation
import neuroml

from . import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestAnnotations(BaseTestCase):
    """Test annotations module"""

    def test_create_annotation(self):
        """Test create_annotations"""
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
            "predecessors": {
                "http://omex-library.org/BioSim0001.omex/model.xml": "model"
            },
            "creation_date": "2024-04-18",
            "modified_dates": ["2024-04-18", "2024-04-19"],
            "authors": {
                "John Doe": {
                    "https://someurl.com": "orcid",
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
        annotation = create_annotation(
            **common,
            annotation_style="miriam",
        )
        self.assertIsNotNone(annotation)
        print(annotation)

        newdoc = neuroml.NeuroMLDocument(id="test")
        newdoc.annotation = neuroml.Annotation([annotation])
        self.assertIsNone(newdoc.annotation.validate())
        self.assertIsNone(newdoc.validate(recursive=True))

        # biosimulations
        annotation = create_annotation(
            **common,
            annotation_style="biosimulations",
        )
        self.assertIsNotNone(annotation)
        print(annotation)
