import unittest
from io import StringIO
from unittest.mock import patch

import networkx as nx

from pyneuroml.swc.LoadSWC import SWCGraph, SWCNode


class TestSWCNode(unittest.TestCase):
    def test_init(self):
        node = SWCNode(1, 1, 0.0, 0.0, 0.0, 1.0, -1)
        self.assertEqual(node.id, 1)
        self.assertEqual(node.type, 1)
        self.assertEqual(node.x, 0.0)
        self.assertEqual(node.y, 0.0)
        self.assertEqual(node.z, 0.0)
        self.assertEqual(node.radius, 1.0)
        self.assertEqual(node.parent_id, -1)

    def test_invalid_init(self):
        with self.assertRaises(ValueError):
            SWCNode("a", 1, 0.0, 0.0, 0.0, 1.0, -1)
