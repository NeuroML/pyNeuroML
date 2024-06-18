#!/usr/bin/env python3
"""
Test annotations related methods

File: tests/test_annotations.py

Copyright 2024 NeuroML contributors
"""

import logging
import os

import neuroml

from pyneuroml.annotations import create_annotation, extract_annotations
from pyneuroml.io import write_neuroml2_file

from . import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestAnnotations(BaseTestCase):
    """Test annotations module"""

    annotation_args = {
        "description": "A tests model",
        "abstract": "lol, something nice",
        "keywords": ["something", "and something"],
        "thumbnails": ["lol.png"],
        "organisms": {
            "http://identifiers.org/taxonomy/4896": "Schizosaccharomyces pombe"
        },
        "is_": {"http://uri.neuinfo.org/nif/nifstd/nifext_2511": "An ion channel"},
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
                "https://orcid.org/0000-0001-7568-7167": "orcid",
            },
            "Jane Smith": {},
        },
        "contributors": {"Jane Doe", "John Smith", "Jane Smith"},
        "see_also": {"http://link.com": "a link"},
        "references": {"http://reference.com": "a reference"},
        "funders": {"http://afundingbody.org": "a funding body"},
        "license": {"https://identifiers.org/spdx:CC0": "CC0"},
    }
    func_args = {
        "xml_header": False,
        "subject": "model.nml",
    }

    def test_create_annotation_miriam(self):
        """Test create_annotations: MIRIAM"""
        annotation = create_annotation(
            **self.annotation_args, **self.func_args, annotation_style="miriam"
        )
        self.assertIsNotNone(annotation)
        print(annotation)

        newdoc = neuroml.NeuroMLDocument(id="test")
        newdoc.annotation = neuroml.Annotation([annotation])
        self.assertIsNone(newdoc.annotation.validate())
        self.assertIsNone(newdoc.validate(recursive=True))

    def test_create_annotation_biosimulations(self):
        """Test create_annotations: biosimulations"""
        annotation2 = create_annotation(
            **self.annotation_args, **self.func_args, annotation_style="biosimulations"
        )
        self.assertIsNotNone(annotation2)
        print(annotation2)

    def test_extract_annotations_miriam(self):
        """Test the extract_annotations function."""
        fname = "TestAnnotationMiriam.xml"
        annotation = create_annotation(
            **self.annotation_args,
            **self.func_args,
            annotation_style="miriam",
        )
        self.assertIsNotNone(annotation)
        newdoc = neuroml.NeuroMLDocument(id="test")
        newdoc.annotation = neuroml.Annotation([annotation])
        write_neuroml2_file(newdoc, fname)
        extracted = extract_annotations(fname)
        for key, val in self.annotation_args.items():
            print(f"{key}: {val} vs {extracted['test'][key]}")
            # miriam only has keys
            if isinstance(val, dict):
                self.assertEqual(len(val), len(extracted["test"][key]))
            elif isinstance(val, str):
                self.assertEqual(val, extracted["test"][key])
        os.unlink(fname)

    def test_extract_annotations_biosimulations(self):
        """Test the extract_annotations function."""
        fname = "TestAnnotationBiosimulations.xml"
        annotation = create_annotation(
            **self.annotation_args,
            **self.func_args,
            annotation_style="biosimulations",
        )
        self.assertIsNotNone(annotation)

        newdoc = neuroml.NeuroMLDocument(id="test")
        newdoc.annotation = neuroml.Annotation([annotation])
        write_neuroml2_file(newdoc, fname)
        extracted = extract_annotations(fname)
        for key, val in self.annotation_args.items():
            print(f"{key}: {val} vs {extracted['test'][key]}")
            self.assertEqual(len(val), len(extracted["test"][key]))

        os.unlink(fname)
