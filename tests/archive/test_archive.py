#!/usr/bin/env python3
"""
Tests for pyneuroml.archive module

File: test_archive.py

Copyright 2023 NeuroML contributors
"""

import json
import logging
import pathlib
import tempfile
import unittest
from zipfile import ZipFile

from pyneuroml.archive import (
    create_combine_archive,
    create_combine_archive_manifest,
    create_ro_crate,
)
from pyneuroml.runners import run_jneuroml
from pyneuroml.utils import get_model_file_list
from pyneuroml.utils.misc import chdir

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

try:
    import rocrate  # noqa: F401

    HAS_ROCRATE = True
except ImportError:
    HAS_ROCRATE = False


class TestArchiveModule(unittest.TestCase):
    """Test the pyneuroml.archive module."""

    def test_get_model_file_list_1(self):
        """Test get_model_file_list."""
        # a NeuroML file in the tests directory
        thispath = pathlib.Path(__file__)
        dirname = str(thispath.parent.parent)
        filelist = []
        get_model_file_list("HH_example_cell.nml", filelist, dirname)
        self.assertEqual(4, len(filelist))

    def test_get_model_file_list_2(self):
        # a LEMS file in the examples directory
        thispath = pathlib.Path(__file__)
        dirname = str(thispath.parent.parent.parent)
        filelist = []
        get_model_file_list(
            "LEMS_NML2_Ex5_DetCell.xml", filelist, dirname + "/examples"
        )
        self.assertEqual(5, len(filelist))

    def test_get_model_file_list_2a(self):
        # a LEMS file in the examples directory
        thispath = pathlib.Path(__file__)
        dirname = str(thispath.parent.parent.parent)

        with chdir(dirname + "/examples"):
            filelist = []
            get_model_file_list(
                "LEMS_NML2_Ex5_DetCell.xml", filelist, dirname + "/examples"
            )
            self.assertEqual(5, len(filelist))

    def test_get_model_file_list_3(self):
        thispath = pathlib.Path(__file__)
        # a SEDML file in the examples directory
        dirname = str(thispath.parent.parent.parent)
        run_jneuroml(
            "",
            "LEMS_NML2_Ex5_DetCell.xml",
            "-sedml",
            exec_in_dir="examples",
            max_memory="1G",
            exit_on_fail=True,
        )
        filelist = []
        get_model_file_list(
            "LEMS_NML2_Ex5_DetCell.sedml", filelist, dirname + "/examples"
        )
        self.assertEqual(6, len(filelist))

    def test_get_model_file_list_4(self):
        thispath = pathlib.Path(__file__)
        # NeuroML file in examples directory
        dirname = str(thispath.parent.parent.parent)
        filelist = []
        get_model_file_list(
            "NML2_SingleCompHHCell.nml", filelist, dirname + "/examples"
        )
        self.assertEqual(4, len(filelist))

    def test_get_model_file_list_5(self):
        thispath = pathlib.Path(__file__)
        # HL23 network
        dirname = str(thispath.parent.parent)
        filelist = []
        get_model_file_list(
            "HL23VIP.cell.nml", filelist, dirname + "/plot/L23-example/"
        )
        self.assertEqual(13, len(filelist))

    def test_create_combine_archive_manifest(self):
        """Test create_combine_archive_manifest function."""
        thispath = pathlib.Path(__file__)
        dirname = str(thispath.parent.parent)
        filelist = []
        get_model_file_list("HH_example_cell.nml", filelist, dirname)
        create_combine_archive_manifest("HH_example_cell.nml", filelist, dirname)
        self.assertTrue(pathlib.Path(dirname + "/manifest.xml").exists())

        # a LEMS file in the examples directory
        dirname = str(thispath.parent.parent.parent)
        filelist = []
        get_model_file_list(
            "LEMS_NML2_Ex5_DetCell.xml", filelist, dirname + "/examples"
        )
        create_combine_archive_manifest(
            "LEMS_NML2_Ex5_DetCell.xml", filelist, dirname + "/examples"
        )
        self.assertTrue(pathlib.Path(dirname + "/examples/manifest.xml").exists())

        # NeuroML file in examples directory
        dirname = str(thispath.parent.parent.parent)
        filelist = []
        get_model_file_list(
            "NML2_SingleCompHHCell.nml", filelist, dirname + "/examples"
        )
        create_combine_archive_manifest(
            "NML2_SingleCompHHCell.nml", filelist, dirname + "/examples"
        )
        self.assertTrue(pathlib.Path(dirname + "/examples/manifest.xml").exists())

    def test_create_combine_archive(self):
        """Test create_combine_archive."""

        thispath = pathlib.Path(__file__)
        filelist = []
        dirname = str(thispath.parent.parent)
        create_combine_archive(
            zipfile_name="HH_example",
            rootfile=dirname + "/HH_example_cell.nml",
            filelist=filelist,
        )
        self.assertTrue(pathlib.Path(dirname + "/HH_example.neux.zip").exists())

        dirname = str(thispath.parent.parent.parent)
        filelist = []
        create_combine_archive(
            zipfile_name="LEMS_NML2_Ex5_DetCell",
            rootfile=dirname + "/examples/LEMS_NML2_Ex5_DetCell.xml",
            filelist=filelist,
        )
        self.assertTrue(
            pathlib.Path(dirname + "/examples/LEMS_NML2_Ex5_DetCell.neux.zip").exists()
        )

        dirname = str(thispath.parent.parent.parent)
        filelist = []
        create_combine_archive(
            zipfile_name="NML2_SingleCompHHCell",
            rootfile=dirname + "/examples/NML2_SingleCompHHCell.nml",
            filelist=filelist,
        )
        self.assertTrue(
            pathlib.Path(dirname + "/examples/NML2_SingleCompHHCell.neux.zip").exists()
        )

    @unittest.skipUnless(HAS_ROCRATE, "rocrate is not installed")
    def test_create_ro_crate(self):
        """Test create_ro_crate with a NeuroML file and its includes."""
        thispath = pathlib.Path(__file__)
        dirname = str(thispath.parent.parent)
        filelist = []
        outfile = create_ro_crate(
            rootfile=dirname + "/HH_example_cell.nml",
            zipfile_name="HH_example",
            filelist=filelist,
            name="HH example cell",
            license="https://creativecommons.org/licenses/by/4.0/",
        )
        self.addCleanup(pathlib.Path(outfile).unlink, missing_ok=True)
        # the caller's list is not modified
        self.assertEqual(0, len(filelist))
        self.assertTrue(outfile.endswith("HH_example.crate.zip"))
        self.assertTrue(pathlib.Path(outfile).exists())

        with ZipFile(outfile) as archive:
            names = archive.namelist()
            self.assertIn("ro-crate-metadata.json", names)
            metadata = json.loads(archive.read("ro-crate-metadata.json"))

        expected_files = [
            "HH_example_cell.nml",
            "HH_example_k_channel.nml",
            "HH_example_leak_channel.nml",
            "HH_example_na_channel.nml",
        ]
        for f in expected_files:
            self.assertIn(f, names)

        entities = {e["@id"]: e for e in metadata["@graph"]}
        root = entities["./"]
        self.assertEqual("HH example cell", root["name"])
        self.assertEqual({"@id": "HH_example_cell.nml"}, root["mainEntity"])
        self.assertEqual(
            sorted(expected_files), sorted(p["@id"] for p in root["hasPart"])
        )
        for f in expected_files:
            self.assertEqual("File", entities[f]["@type"])
            self.assertEqual("application/xml", entities[f]["encodingFormat"])

    @unittest.skipUnless(HAS_ROCRATE, "rocrate is not installed")
    def test_create_ro_crate_lems(self):
        """Test create_ro_crate with a LEMS file and an explicit file list."""
        thispath = pathlib.Path(__file__)
        dirname = str(thispath.parent.parent.parent) + "/examples"
        with tempfile.TemporaryDirectory() as tmpdir:
            # extra files are relative to the root file
            extra = pathlib.Path(dirname) / "README_rocrate_test.txt"
            extra.write_text("test")
            # a format not in RO_CRATE_ENCODING_FORMATS
            unknown = pathlib.Path(dirname) / "rocrate_test.dat"
            unknown.write_text("1 2 3")
            try:
                outfile = create_ro_crate(
                    rootfile=dirname + "/LEMS_NML2_Ex5_DetCell.xml",
                    zipfile_name="LEMS_NML2_Ex5_DetCell",
                    extra_files=["README_rocrate_test.txt", "rocrate_test.dat"],
                )
            finally:
                extra.unlink()
                unknown.unlink()
            self.addCleanup(pathlib.Path(outfile).unlink, missing_ok=True)

            with ZipFile(outfile) as archive:
                archive.extractall(tmpdir)
            metadata = json.loads(
                (pathlib.Path(tmpdir) / "ro-crate-metadata.json").read_text()
            )

        entities = {e["@id"]: e for e in metadata["@graph"]}
        root = entities["./"]
        self.assertEqual({"@id": "LEMS_NML2_Ex5_DetCell.xml"}, root["mainEntity"])
        self.assertIn("NML2_SingleCompHHCell.nml", entities)
        self.assertEqual(
            "text/plain", entities["README_rocrate_test.txt"]["encodingFormat"]
        )
        # files of other formats are still included, just without encodingFormat
        self.assertIn("rocrate_test.dat", entities)
        self.assertNotIn("encodingFormat", entities["rocrate_test.dat"])
