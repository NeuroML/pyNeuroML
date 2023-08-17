#!/usr/bin/env python3
"""
Test utils

File: tests/utils/test_utils.py

Copyright 2023 NeuroML contributors
"""


import logging
import math
import pathlib as pl

import neuroml
from pyneuroml.pynml import read_neuroml2_file, write_neuroml2_file
from pyneuroml.utils import (
    extract_position_info,
    get_files_generated_after,
    rotate_cell,
)

from .. import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestUtils(BaseTestCase):

    """Test utils module"""

    def test_extract_position_info(self):
        """Test extract_position_info"""
        nml_files = ["tests/plot/L23-example/TestNetwork.net.nml"]
        for nml_file in nml_files:
            nml_model = read_neuroml2_file(
                nml_file,
                include_includes=True,
                check_validity_pre_include=False,
                verbose=True,
                optimized=True,
            )

            (
                cell_id_vs_cell,
                pop_id_vs_cell,
                positions,
                pop_id_vs_color,
                pop_id_vs_radii,
            ) = extract_position_info(nml_model)

            for c in ["HL23PV", "HL23PYR", "HL23VIP", "HL23SST"]:
                self.assertIn(c, cell_id_vs_cell.keys())

    def test_get_files_generated_after(self):
        """test get_files_generated_after method."""
        # compare to epoch, should just list all files
        files = get_files_generated_after(timestamp=0, include_suffixes=[".sh", ".ini"])
        logger.debug(files)
        current_files = list(pl.Path(".").glob("*.sh"))
        current_files.extend(list(pl.Path(".").glob("*.ini")))
        current_files = [f for f in current_files if f.is_file()]
        self.assertEqual(len(files), len(current_files))

        files = get_files_generated_after(
            timestamp=0, include_suffixes=[".sh", ".ini"], ignore_suffixes=[".sh"]
        )
        logger.debug(files)
        current_files = list(pl.Path(".").glob("*.ini"))
        current_files = [f for f in current_files if f.is_file()]
        self.assertEqual(len(files), len(current_files))

    def test_rotate_cell(self):
        """Test rotate_cell"""
        acell = neuroml.utils.component_factory(
            "Cell", id="test_cell", validate=False
        )  # type: neuroml.Cell

        soma = acell.add_segment(
            prox=[0, 0, 0, 15],
            dist=[0, 0, 0, 15],
            seg_id=0,
            use_convention=False,
            reorder_segment_groups=False,
            optimise_segment_groups=False,
        )

        acell.add_segment(
            prox=[0, 0, 0, 12],
            dist=[100, 0, 0, 12],
            seg_id=1,
            use_convention=False,
            reorder_segment_groups=False,
            optimise_segment_groups=False,
            parent=soma,
        )

        acell.add_segment(
            prox=[0, 0, 0, 7],
            dist=[0, 150, 0, 7],
            seg_id=2,
            use_convention=False,
            reorder_segment_groups=False,
            optimise_segment_groups=False,
            parent=soma,
        )

        acell.add_segment(
            prox=[0, 0, 0, 4],
            dist=[0, 0, 200, 4],
            seg_id=3,
            use_convention=False,
            reorder_segment_groups=False,
            optimise_segment_groups=False,
            parent=soma,
        )

        print(acell)

        rotated_cell = rotate_cell(acell, x=math.pi / 20, y=0, z=0, order="xyz")
        rotated_cell.id = "test_rotated_cell"
        print(rotated_cell)

        newdoc = neuroml.utils.component_factory(
            "NeuroMLDocument", id="test_doc"
        )  # type: neuroml.NeuroMLDocument
        newdoc.add(acell)
        newdoc.add(rotated_cell)

        net = newdoc.add("Network", id="test_net", validate=False)
        pop1 = net.add(
            "Population",
            id="test_pop1",
            size=1,
            component=acell.id,
            type="populationList",
            validate=False,
        )
        pop1.add(
            "Instance", id=0, location=pop1.component_factory("Location", x=0, y=0, z=0)
        )

        pop2 = net.add(
            "Population",
            id="test_pop2",
            size=1,
            component=rotated_cell.id,
            type="populationList",
            validate=False,
        )
        pop2.add(
            "Instance",
            id=0,
            location=pop1.component_factory("Location", x=200, y=0, z=0),
        )

        newdoc.validate(recursive=True)
        write_neuroml2_file(newdoc, "tests/utils/test_rotation.net.nml", validate=True)
