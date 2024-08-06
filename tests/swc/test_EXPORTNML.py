import os
import re
import sys
import tempfile
import unittest

# Add the parent directory of pyneuroml to sys.path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)

from pyneuroml.swc.ExportNML import NeuroMLWriter
from pyneuroml.swc.LoadSWC import SWCNode, load_swc


class TestNeuroMLWriter(unittest.TestCase):
    def parse_swc_string(self, swc_string):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write(swc_string)
            temp_file_name = temp_file.name
        return load_swc(temp_file_name)

    def tearDown(self):
        for file in os.listdir():
            if file.endswith(".swc"):
                os.remove(file)

    def check_common_elements(self, nml_output, cell_name):
        self.assertIn(
            '<neuroml xmlns="http://www.neuroml.org/schema/neuroml2"', nml_output
        )
        self.assertIn(f'<cell id="{cell_name}">', nml_output)
        self.assertIn(f'<morphology id="morphology_{cell_name}">', nml_output)
        self.assertIn("</cell>", nml_output)
        self.assertIn("</neuroml>", nml_output)

    def assert_coordinate(self, nml_output, x, y, z, diameter):
        pattern = rf'<(?:proximal|distal) x="{x}\.?\d*" y="{y}\.?\d*" z="{z}\.?\d*" diameter="{diameter}\.?\d*"/>'
        match = re.search(pattern, nml_output)
        if not match:
            print(
                f"Expected coordinate not found: x={x}, y={y}, z={z}, diameter={diameter}"
            )
            print("Actual content:")
            print(nml_output)
        self.assertIsNotNone(
            match, f"Coordinate not found: x={x}, y={y}, z={z}, diameter={diameter}"
        )

    def print_nml_output(self, nml_output):
        print("\nFull NeuroML output:")
        print(nml_output)
        print("\nEnd of NeuroML output\n")

    def test_case1_single_contour_soma(self):
        swc_data = """
        1 1 0 0 0 10 -1
        2 1 0 -10 0 10 1
        3 1 0 10 0 10 1
        4 3 10 0 0 2 1
        5 3 30 0 0 2 4
        6 3 40 10 0 2 5
        7 3 40 -10 0 2 5
        """
        swc_graph = self.parse_swc_string(swc_data)
        writer = NeuroMLWriter(swc_graph)
        nml_output = writer.nml_string("2.0")

        self.print_nml_output(nml_output)
        self.check_common_elements(nml_output, "Unknown")
        self.assertIn('<segment id="0"', nml_output)
        self.assertIn('<segment id="1"', nml_output)
        self.assertIn('<segmentGroup id="soma_group">', nml_output)
        self.assertIn('<segmentGroup id="dendrite_group">', nml_output)
        self.assertIn('<parent segment="0"', nml_output)

        # Check for coordinates without specifying exact values
        self.assertTrue(
            re.search(
                r'<(?:proximal|distal) x="-?\d+\.?\d*" y="-?\d+\.?\d*" z="-?\d+\.?\d*" diameter="\d+\.?\d*"/>',
                nml_output,
            )
        )

    def test_case2_no_soma(self):
        swc_data = """
        1 2 0 0 0 2 -1
        2 2 20 0 0 2 1
        3 2 0 20 0 2 1
        4 2 0 30 0 2 3
        5 2 0 -20 0 2 1
        6 2 0 -30 0 2 5
        """
        swc_graph = self.parse_swc_string(swc_data)
        writer = NeuroMLWriter(swc_graph)
        nml_output = writer.nml_string("2.0")

        self.print_nml_output(nml_output)
        self.check_common_elements(nml_output, "Unknown")
        self.assertNotIn('<segmentGroup id="soma_group">', nml_output)
        self.assertIn('<segmentGroup id="axon_group">', nml_output)
        self.assertIn('<segment id="0"', nml_output)
        self.assertIn('<segment id="1"', nml_output)
        self.assertIn('<segment id="2"', nml_output)
        self.assertIn('<parent segment="0"', nml_output)
        self.assertTrue(
            re.search(
                r'<(?:proximal|distal) x="20\.?\d*" y="0\.?\d*" z="0\.?\d*" diameter="4\.?\d*"/>',
                nml_output,
            )
        )
        self.assertTrue(
            re.search(
                r'<(?:proximal|distal) x="0\.?\d*" y="30\.?\d*" z="0\.?\d*" diameter="4\.?\d*"/>',
                nml_output,
            )
        )
        self.assertTrue(
            re.search(
                r'<(?:proximal|distal) x="0\.?\d*" y="-30\.?\d*" z="0\.?\d*" diameter="4\.?\d*"/>',
                nml_output,
            )
        )

    def test_case3_multiple_contours_soma(self):
        swc_data = """
        1 1 0 0 0 10 -1
        2 1 0 -10 0 10 1
        3 1 0 10 0 10 1
        4 3 10 0 0 2 1
        5 3 30 0 0 2 4
        """
        swc_graph = self.parse_swc_string(swc_data)
        writer = NeuroMLWriter(swc_graph)
        nml_output = writer.nml_string("2.0")

        self.print_nml_output(nml_output)

        # Check overall structure
        self.assertIn(
            '<neuroml xmlns="http://www.neuroml.org/schema/neuroml2"', nml_output
        )
        self.assertIn('xmlns:xs="http://www.w3.org/2001/XMLSchema"', nml_output)
        self.assertIn(
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"', nml_output
        )
        self.assertIn(
            'xsi:schemaLocation="http://www.neuroml.org/schema/neuroml2', nml_output
        )
        self.assertIn('<cell id="Unknown">', nml_output)
        self.assertIn(
            "<notes>Neuronal morphology exported from Python Based Converter. Original file: Unknown</notes>",
            nml_output,
        )
        self.assertIn(
            '<property tag="cell_type" value="converted_from_swc"/>', nml_output
        )
        self.assertIn('<morphology id="morphology_Unknown">', nml_output)

        # Check segments
        segments = re.findall(r'<segment id="(\d+)"', nml_output)
        print(f"Found segments: {segments}")
        self.assertTrue(
            len(segments) >= 2, f"Expected at least 2 segments, found {len(segments)}"
        )

        # Check segment groups
        segment_groups = re.findall(r'<segmentGroup id="(\w+)">', nml_output)
        print(f"Found segment groups: {segment_groups}")
        expected_groups = {"all", "soma_group", "dendrite_group"}
        self.assertTrue(
            expected_groups.issubset(set(segment_groups)),
            f"Missing some expected groups. Expected at least {expected_groups}, found {segment_groups}",
        )

        # Check specific memberships
        members = re.findall(r'<member segment="(\d+)"/>', nml_output)
        print(f"Found member segments: {members}")
        self.assertTrue(
            len(members) >= 2,
            f"Expected at least 2 member segments, found {len(members)}",
        )

        # Check specific group memberships
        self.assertIn('<segmentGroup id="soma_group">', nml_output)
        self.assertIn('<segmentGroup id="dendrite_group">', nml_output)

        # Check closing tags
        self.assertIn("</morphology>", nml_output)
        self.assertIn("</cell>", nml_output)
        self.assertIn("</neuroml>", nml_output)

    def test_case4_multiple_cylinder_soma(self):
        swc_data = """
        1 1 0 0 0 5 -1
        2 1 0 5 0 10 1
        3 1 0 10 0 10 2
        4 1 0 15 0 5 3
        5 3 0 20 0 5 4
        6 3 0 30 0 5 5
        7 3 0 -5 0 5 1
        8 3 0 -15 0 2.5 7
        9 3 10 10 0 5 2
        10 3 20 10 0 5 9
        """
        swc_graph = self.parse_swc_string(swc_data)
        writer = NeuroMLWriter(swc_graph)
        nml_output = writer.nml_string("2.0")

        self.print_nml_output(nml_output)
        self.check_common_elements(nml_output, "Unknown")

        segments = re.findall(r'<segment id="(\d+)"', nml_output)
        print(f"Found segments: {segments}")
        self.assertTrue(
            len(segments) >= 4, f"Expected at least 4 segments, found {len(segments)}"
        )

        self.assertIn('<segmentGroup id="soma_group">', nml_output)
        self.assertIn('<segmentGroup id="dendrite_group">', nml_output)

        parent_segments = re.findall(r'<parent segment="(\d+)"', nml_output)
        print("Found parent segments:", parent_segments)

        self.assertTrue(len(parent_segments) > 0, "No parent segments found")

        self.assertTrue(
            re.search(
                r'<(?:proximal|distal) x="0\.?\d*" y="30\.?\d*" z="0\.?\d*" diameter="10\.?\d*"/>',
                nml_output,
            )
        )
        self.assertTrue(
            re.search(
                r'<(?:proximal|distal) x="0\.?\d*" y="-15\.?\d*" z="0\.?\d*" diameter="5\.?\d*"/>',
                nml_output,
            )
        )
        self.assertTrue(
            re.search(
                r'<(?:proximal|distal) x="20\.?\d*" y="10\.?\d*" z="0\.?\d*" diameter="10\.?\d*"/>',
                nml_output,
            )
        )

    def test_case5_spherical_soma(self):
        swc_data = """
        1 1 0 0 0 10 -1
        2 1 0 -10 0 10 1
        3 1 0 10 0 10 1
        4 3 10 0 0 2 1
        5 3 30 0 0 2 4
        6 3 0 10 0 2 1
        7 3 0 30 0 2 6
        8 3 0 -10 0 2 1
        9 3 0 -30 0 2 8
        """
        swc_graph = self.parse_swc_string(swc_data)
        writer = NeuroMLWriter(swc_graph)
        nml_output = writer.nml_string("2.0")

        self.print_nml_output(nml_output)
        self.check_common_elements(nml_output, "Unknown")
        self.assertIn('<segment id="0"', nml_output)
        self.assertIn('<segment id="1"', nml_output)
        self.assertIn('<segmentGroup id="soma_group">', nml_output)
        self.assertIn('<segmentGroup id="dendrite_group">', nml_output)
        parent_segments = re.findall(r'<parent segment="0"', nml_output)
        self.assertTrue(len(parent_segments) > 0, "No parent segments with id 0 found")
        self.assertTrue(
            re.search(
                r'<(?:proximal|distal) x="30\.?\d*" y="0\.?\d*" z="0\.?\d*" diameter="4\.?\d*"/>',
                nml_output,
            )
        )
        self.assertTrue(
            re.search(
                r'<(?:proximal|distal) x="0\.?\d*" y="30\.?\d*" z="0\.?\d*" diameter="4\.?\d*"/>',
                nml_output,
            )
        )
        self.assertTrue(
            re.search(
                r'<(?:proximal|distal) x="0\.?\d*" y="-30\.?\d*" z="0\.?\d*" diameter="4\.?\d*"/>',
                nml_output,
            )
        )

    def test_error_handling(self):
        # Test with invalid SWC data
        invalid_swc_data = "This is not valid SWC data"
        with self.assertRaises(ValueError):
            self.parse_swc_string(invalid_swc_data)

        # Test with empty SWC data
        empty_swc_data = ""
        swc_graph = self.parse_swc_string(empty_swc_data)
        self.assertEqual(len(swc_graph.nodes), 0)


if __name__ == "__main__":
    unittest.main()
