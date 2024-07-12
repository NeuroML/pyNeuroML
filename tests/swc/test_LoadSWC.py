import os
import unittest

from pyneuroml.swc.LoadSWC import SWCGraph, SWCNode, load_swc


class TestSWCNode(unittest.TestCase):
    """Test cases for the SWCNode class."""

    def test_init(self):
        """Test the initialization of an SWCNode object."""
        node = SWCNode(1, 1, 0.0, 0.0, 0.0, 1.0, -1)
        self.assertEqual(node.id, 1)
        self.assertEqual(node.type, 1)
        self.assertEqual(node.x, 0.0)
        self.assertEqual(node.y, 0.0)
        self.assertEqual(node.z, 0.0)
        self.assertEqual(node.radius, 1.0)
        self.assertEqual(node.parent_id, -1)

    def test_invalid_init(self):
        """Test that initializing an SWCNode with invalid data raises a ValueError."""
        with self.assertRaises(ValueError):
            SWCNode("a", 1, 0.0, 0.0, 0.0, 1.0, -1)


class TestSWCGraph(unittest.TestCase):
    """Test cases for the SWCGraph class."""

    def setUp(self):
        """Set up a sample SWCGraph for testing."""
        self.tree = SWCGraph()
        self.node1 = SWCNode(1, 1, 0.0, 0.0, 0.0, 1.0, -1)
        self.node2 = SWCNode(2, 3, 1.0, 0.0, 0.0, 0.5, 1)
        self.node3 = SWCNode(3, 3, 2.0, 0.0, 0.0, 0.5, 2)
        self.tree.add_node(self.node1)
        self.tree.add_node(self.node2)
        self.tree.add_node(self.node3)

    def test_duplicate_node(self):
        """Test that adding a duplicate node raises a ValueError."""
        with self.assertRaises(ValueError):
            self.tree.add_node(SWCNode(1, 1, 0.0, 0.0, 0.0, 1.0, -1))

    def test_add_metadata(self):
        """Test adding valid metadata to the SWCGraph."""
        self.tree.add_metadata("ORIGINAL_SOURCE", "file.swc")
        self.assertEqual(self.tree.metadata["ORIGINAL_SOURCE"], "file.swc")

    def test_invalid_metadata(self):
        """Test that adding invalid metadata does not modify the metadata dictionary."""
        self.tree.add_metadata("INVALID_FIELD", "value")
        self.assertEqual(self.tree.metadata, {})

    def test_get_parent(self):
        """Test getting the parent node of a given node."""
        self.assertIsNone(self.tree.get_parent(self.node1.id))
        self.assertEqual(self.tree.get_parent(self.node2.id), self.node1)
        self.assertEqual(self.tree.get_parent(self.node3.id), self.node2)
        with self.assertRaises(ValueError):
            self.tree.get_parent(4)

    def test_get_children(self):
        """Test getting the children of a given node."""
        self.assertEqual(self.tree.get_children(self.node1.id), [self.node2])
        self.assertEqual(self.tree.get_children(self.node2.id), [self.node3])
        with self.assertRaises(ValueError):
            self.tree.get_parent(4)

    def test_get_nodes_with_multiple_children(self):
        """Test getting nodes with multiple children."""
        node4 = SWCNode(4, 3, 3.0, 0.0, 0.0, 0.5, 2)
        self.tree.add_node(node4)
        self.assertEqual(self.tree.get_nodes_with_multiple_children(), [self.node2])

    def test_get_nodes_by_type(self):
        """Test getting nodes by their type."""
        self.assertEqual(self.tree.get_nodes_by_type(1), [self.node1])
        self.assertEqual(self.tree.get_nodes_by_type(3), [self.node2, self.node3])


class TestSWCExport(unittest.TestCase):
    """Test cases for exporting SWC files."""

    def setUp(self):
        """Set up file paths for testing."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.input_file = os.path.join(current_dir, "Case1_new.swc")
        self.output_file = os.path.join(current_dir, "Case1_exported.swc")

    def test_load_export_compare(self):
        """Test loading an SWC file, exporting it, and comparing the results."""
        # Load the original file
        original_tree = load_swc(self.input_file)

        # Export the loaded tree
        original_tree.export_to_swc_file(self.output_file)

        # Check if the exported file was created
        self.assertTrue(os.path.exists(self.output_file))

        # Load the exported file
        exported_tree = load_swc(self.output_file)

        # Compare the original and exported trees
        self.assertEqual(len(original_tree.nodes), len(exported_tree.nodes))

        # Compare a few key properties of the first and last nodes
        self.compare_nodes(original_tree.nodes[0], exported_tree.nodes[0])
        self.compare_nodes(original_tree.nodes[-1], exported_tree.nodes[-1])

        # Compare metadata
        self.assertEqual(original_tree.metadata, exported_tree.metadata)

    def compare_nodes(self, node1, node2):
        """Compare two SWCNode objects for equality."""
        self.assertEqual(node1.id, node2.id)
        self.assertEqual(node1.type, node2.type)
        self.assertEqual(node1.parent_id, node2.parent_id)
        self.assertAlmostEqual(node1.x, node2.x, places=4)
        self.assertAlmostEqual(node1.y, node2.y, places=4)
        self.assertAlmostEqual(node1.z, node2.z, places=4)
        self.assertAlmostEqual(node1.radius, node2.radius, places=4)

    def tearDown(self):
        """Clean up by removing the exported file if it exists."""
        if os.path.exists(self.output_file):
            os.remove(self.output_file)


if __name__ == "__main__":
    unittest.main()
