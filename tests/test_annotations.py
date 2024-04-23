#!/usr/bin/env python3
"""
Test annotations related methods

File: tests/test_annotations.py

Copyright 2024 NeuroML contributors
"""


import logging

from pyneuroml.annotations import create_annotation

from . import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestAnnotations(BaseTestCase):
    """Test annotations module"""

    def test_create_annotation(self):
        """Test create_annotations"""
        annotation = create_annotation(
            "model.nml",
            "A tests model",
            abstract="lol, something nice",
            keywords=["something", "and something"],
            thumbnails=["lol.png"],
            organisms={
                "http://identifiers.org/taxonomy/4896": "Schizosaccharomyces pombe"
            },
            encodes_other_biology={
                "http://identifiers.org/GO:0009653": "anatomical structure morphogenesis",
                "http://identifiers.org/kegg:ko04111": "Cell cycle - yeast",
            },
            sources={"https://github.com/lala": "GitHub"},
            predecessors={"http://omex-library.org/BioSim0001.omex/model.xml": "model"},
            creation_date="2024-04-18",
            modified_dates=["2024-04-18", "2024-04-19"],
        )
        self.assertIsNotNone(annotation)
        print(annotation)
