import re


class SWCNode:
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
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid data types in SWC line: {e}")

    def __repr__(self):
        type_name = self.TYPE_NAMES.get(self.type, f"Custom_{self.type}")
        return f"SWCNode(id={self.id}, type={type_name}, x={self.x:.2f}, y={self.y:.2f}, z={self.z:.2f}, radius={self.radius:.2f}, parent_id={self.parent_id})"


class SWCTree:
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
        self.nodes = {}
        self.root = None
        self.metadata = {}

    def add_node(self, node):
        if node.id in self.nodes:
            raise ValueError(f"Duplicate node ID: {node.id}")
        self.nodes[node.id] = node
        if node.parent_id == -1:
            if self.root is not None:
                raise ValueError("Multiple root nodes found")
            self.root = node
        elif node.parent_id in self.nodes:
            parent = self.nodes[node.parent_id]
            parent.children.append(node.id)
        else:
            print(f"Warning: Parent {node.parent_id} not found for node {node.id}")

    def add_metadata(self, key, value):
        if key in self.HEADER_FIELDS:
            self.metadata[key] = value

    def get_parent(self, node_id):
        """Get the parent of a given node."""
        node = self.nodes.get(node_id)
        if node is None:
            raise ValueError(f"Node {node_id} not found")
        return self.nodes.get(node.parent_id) if node.parent_id != -1 else None

    def get_descendants(self, node_id):
        """Get all descendants of a given node."""
        node = self.nodes.get(node_id)
        if node is None:
            raise ValueError(f"Node {node_id} not found")

        descendants = []
        queue = node.children.copy()
        while queue:
            child_id = queue.pop(0)
            child = self.nodes[child_id]
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
        return [node for node in self.nodes.values() if node.type == type_id]

    def get_branch_points(self, *types):
        """Get all branch points (nodes with multiple children) of the given types."""
        nodes = []
        for type_id in types:
            nodes.extend(self.get_nodes_with_multiple_children(type_id))
        return nodes


def parse_header(line):
    for field in SWCTree.HEADER_FIELDS:
        match = re.match(rf"{field}\s+(.+)", line, re.IGNORECASE)
        if match:
            return field, match.group(1).strip()
    return None, None


def load_swc(filename):
    tree = SWCTree()
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
