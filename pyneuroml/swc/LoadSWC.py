import re
from math import sqrt

import networkx as nx


class SWCNode:
    """
    Represents a single node in an SWC (Standardized Morphology Data Format) file.

    The SWC format is a widely used standard for representing neuronal morphology data.
    It consists of a series of lines, each representing a single node or sample point
    along the neuronal structure. For more information on the SWC format, see:
    https://swc-specification.readthedocs.io/en/latest/swc.html

    Attributes:
        UNDEFINED (int): ID representing an undefined node type.
        SOMA (int): ID representing a soma node.
        AXON (int): ID representing an axon node.
        BASAL_DENDRITE (int): ID representing a basal dendrite node.
        APICAL_DENDRITE (int): ID representing an apical dendrite node.
        CUSTOM (int): ID representing a custom node type.
        UNSPECIFIED_NEURITE (int): ID representing an unspecified neurite node.
        GLIA_PROCESSES (int): ID representing a glia process node.
        TYPE_NAMES (dict): A mapping of node type IDs to their string representations.
    """

    UNDEFINED = 0
    SOMA = 1
    AXON = 2
    BASAL_DENDRITE = 3
    APICAL_DENDRITE = 4
    CUSTOM = 5
    UNSPECIFIED_NEURITE = 6
    GLIA_PROCESSES = 7

    TYPE_NAMES = {
        UNDEFINED: "Undefined",
        SOMA: "Soma",
        AXON: "Axon",
        BASAL_DENDRITE: "Basal Dendrite",
        APICAL_DENDRITE: "Apical Dendrite",
        CUSTOM: "Custom",
        UNSPECIFIED_NEURITE: "Unspecified Neurite",
        GLIA_PROCESSES: "Glia Processes",
    }

    def __init__(self, node_id, type_id, x, y, z, radius, parent_id):
        try:
            self.id = int(node_id)
            self.type = int(type_id)
            self.x = float(x)
            self.y = float(y)
            self.z = float(z)
            self.radius = float(radius)
            self.parent_id = int(parent_id)
            self.children = []
            self.fraction_along = 0.0
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid data types in SWC line: {e}")

    def __repr__(self):
        type_name = self.TYPE_NAMES.get(self.type, f"Custom_{self.type}")
        return f"SWCNode(id={self.id}, type={type_name}, x={self.x:.2f}, y={self.y:.2f}, z={self.z:.2f}, radius={self.radius:.2f}, parent_id={self.parent_id})"


class SWCGraph:
    HEADER_FIELDS = [
        "ORIGINAL_SOURCE",
        "CREATURE",
        "REGION",
        "FIELD/LAYER",
        "TYPE",
        "CONTRIBUTOR",
        "REFERENCE",
        "RAW",
        "EXTRAS",
        "SOMA_AREA",
        "SHRINKAGE_CORRECTION",
        "VERSION_NUMBER",
        "VERSION_DATE",
        "SCALE",
    ]

    def __init__(self):
        self.nodes = []
        self.root = None  # New attribute to store the root node
        self.metadata = {}

    def add_node(self, node):
        """
        Add a node to the SWC graph.

        Args:
            node (SWCNode): The node to be added.

        Raises:
            ValueError: If a node with the same ID already exists in the graph.
        """
        if any(existing_node.id == node.id for existing_node in self.nodes):
            raise ValueError(f"Duplicate node ID: {node.id}")

        self.nodes.append(node)

    def add_metadata(self, key, value):
        """
        Add metadata to the SWC graph.

        Args:
            key (str): The key for the metadata.
            value (str): The value for the metadata.

        Note:
            Only valid header fields (as defined in HEADER_FIELDS) are added as metadata.
        """
        if key in self.HEADER_FIELDS:
            self.metadata[key] = value

    def get_parent(self, node_id):
        """Get the parent of a given node."""
        node = next((n for n in self.nodes if n.id == node_id), None)
        if node is None:
            raise ValueError(f"Node {node_id} not found")
        parent_id = node.parent_id
        if parent_id == -1:
            return None
        else:
            parent_node = next((n for n in self.nodes if n.id == parent_id), None)
            return parent_node

    def get_children(self, node_id):
        """
        Get a list of child nodes for a given node.

        Args:
            node_id (int): The ID of the node for which to get the children.

        Returns:
            list: A list of SWCNode objects representing the children of the given node.

        Raises:
            ValueError: If the provided node_id is not found in the graph.
        """
        children = [node for node in self.nodes if node.parent_id == node_id]
        if not children:
            raise ValueError(f"Node {node_id} not found or has no children")
        return children

    def get_descendants(self, node_id):
        """Get all descendants of a given node."""

        node = next((n for n in self.nodes if n.id == node_id), None)
        print(f"node_id: {node_id}, node: {node}")
        if node is None:
            raise ValueError(f"Node {node_id} not found")

        descendants = []
        queue = node.children.copy()
        while queue:
            child_id = queue.pop(0)
            child = next((n for n in self.nodes if n.id == child_id), None)
            if child is None:
                continue
            descendants.append(child)
            queue.extend(child.children)
        return descendants

    def get_nodes_with_multiple_children(self, type_id=None):
        """Get all nodes that have more than one child, optionally filtering by type."""
        nodes = []
        for node in self.nodes.values():
            if len(node.children) > 1:
                if type_id is None or node.type == type_id:
                    nodes.append(node)
        return nodes

    def get_nodes_by_type(self, type_id):
        """Get all nodes of a specific type."""
        return [node for node in self.nodes if node.type == type_id]

    def get_branch_points(self, *types):
        """Get all branch points (nodes with multiple children) of the given types."""
        nodes = []
        for type_id in types:
            nodes.extend(self.get_nodes_with_multiple_children(type_id))
        return nodes

    def has_soma_node(self):
        """
        Check if the graph contains at least one soma node (type 1).
        """
        return any(node.type == SWCNode.SOMA for node in self.nodes.values())


def parse_header(line):
    for field in SWCGraph.HEADER_FIELDS:
        match = re.match(rf"{field}\s+(.+)", line, re.IGNORECASE)
        if match:
            return field, match.group(1).strip()
    return None, None


def load_swc(filename):
    tree = SWCGraph()
    try:
        with open(filename, "r") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("#"):
                    key, value = parse_header(line[1:].strip())
                    if key:
                        tree.add_metadata(key, value)
                    continue

                parts = line.split()
                if len(parts) != 7:
                    print(f"Warning: Skipping invalid line: {line}")
                    continue

                node_id, type_id, x, y, z, radius, parent_id = parts
                try:
                    node = SWCNode(node_id, type_id, x, y, z, radius, parent_id)
                    tree.add_node(node)
                except ValueError as e:
                    print(f"Warning: {e} in line: {line}")

    except (FileNotFoundError, IOError) as e:
        print(f"Error reading file {filename}: {e}")

    return tree
