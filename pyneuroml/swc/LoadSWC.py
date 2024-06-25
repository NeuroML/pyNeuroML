import logging
import re
import sys

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


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
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid data types in SWC line: {e}")

    def to_string(self):
        """
        Returns a human-readable string representation of the node.
        """
        type_name = self.TYPE_NAMES.get(self.type, f"Custom_{self.type}")
        return f"Node ID: {self.id}, Type: {type_name}, Coordinates: ({self.x:.2f}, {self.y:.2f}, {self.z:.2f}), Radius: {self.radius:.2f}, Parent ID: {self.parent_id}"


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
        self.root = None
        self.metadata = {}
        self.logger = logging.getLogger(__name__)

    def add_node(self, node):
        """
        Add a node to the SWC graph.

        Args:
            node (SWCNode): The node to be added.

        Raises:
            ValueError: If a node with the same ID already exists in the graph.
            ValueError: If multiple root nodes are detected.
        """
        if any(existing_node.id == node.id for existing_node in self.nodes):
            self.logger.error(f"Duplicate node ID: {node.id}")
            raise ValueError(f"Duplicate node ID: {node.id}")

        if node.parent_id == -1:
            if self.root is not None:
                self.logger.error("Attempted to add multiple root nodes")
                raise ValueError(
                    "Multiple root nodes detected. Only one root node is allowed."
                )
            self.root = node
            self.logger.debug(f"Root node set: {node}")
        else:
            parent = next((n for n in self.nodes if n.id == node.parent_id), None)
            if parent:
                parent.children.append(node)
                self.logger.debug(f"Node {node.id} added as child to node {parent.id}")
            else:
                self.logger.warning(
                    f"Parent node {node.parent_id} not found for node {node.id}"
                )

        self.nodes.append(node)
        self.logger.debug(f"New node added: {node}")

    def get_node(self, node_id):
        """
        Get a node from the graph by its ID.

        Args:
            node_id (int): The ID of the node to retrieve.

        Returns:
              SWCNode: The node with the specified ID.

        Raises:
              ValueError: If the specified node_id is not found in the SWC tree.
        """
        node = next((n for n in self.nodes if n.id == node_id), None)
        if node is None:
            raise ValueError(f"Node {node_id} not found in the SWC tree")
        return node

    def add_metadata(self, key, value):
        """
        Add metadata to the SWC graph.

        Args:
            key (str): The key for the metadata.
            value (str): The value for the metadata.

        Note:
            Only valid header fields (as defined in HEADER_FIELDS) are added as metadata.
            A warning is logged for unrecognized header fields.
        """
        if key in self.HEADER_FIELDS:
            self.metadata[key] = value
            self.logger.debug(f"Added metadata: {key}: {value}")
        else:
            self.logger.warning(f"Ignoring unrecognized header field: {key}: {value}")

    def get_parent(self, node_id):
        """
        Get the parent node of a given node in the SWC tree.

        Args:
        node_id (int): The ID of the node for which to retrieve the parent.

        Returns:
        Node or None: The parent Node object if the node has a parent, otherwise None.

        Raises:
        ValueError: If the specified node_id is not found in the SWC tree.

        """
        node = self.get_node(node_id)
        if node.parent_id == -1:
            return None
        return self.get_node(node.parent_id)

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
        parent_node = self.get_node(node_id)
        children = [node for node in self.nodes if node.parent_id == node_id]
        parent_node.children = children
        return children

    def get_nodes_with_multiple_children(self, type_id=None):
        """
        Get nodes with multiple children, optionally filtered by type.

        Args:
            type_id (int, optional): The type ID to filter nodes by. If None, all types are considered.

        Returns:
            list: A list of SWCNode objects that have multiple children and match the specified type (if provided).

        Note:
            Prints the number of nodes found if a specific type_id is provided.
        """
        nodes = []
        for node in self.nodes:
            children = self.get_children(node.id)
            if len(children) > 1 and (type_id is None or node.type == type_id):
                nodes.append(node)

        if type_id is not None:
            print(f"Found {len(nodes)} nodes of type {type_id} with multiple children.")

        return nodes

    def get_nodes_by_type(self, type_id):
        """
        Get a list of nodes of a specific type.

        Args:
            type_id (int): The type ID of the nodes to retrieve.

        Returns:
            list: A list of SWCNode objects that have the specified type ID.
        """
        return [node for node in self.nodes if node.type == type_id]

    def get_branch_points(self, *types):
        """
        Get all branch points (nodes with multiple children) of the given types.

        Args:
           *types (int): One or more node type IDs to filter the branch points by.
              If no types are provided, all branch points in the graph will be returned.

        Returns:
            list: A list of SWCNode objects that represent branch points (nodes with
                  multiple children) of the specified types. If no types are provided,
                  all branch points in the graph are returned.
        """
        branch_points = {}

        if not types:
            # If no types are specified, return all branch points under a None key
            branch_points[None] = self.get_nodes_with_multiple_children()
        else:
            for type_id in types:
                branch_points[type_id] = self.get_nodes_with_multiple_children(type_id)

        return branch_points


def parse_header(line):
    """
    Parse a header line from an SWC file.

    This function attempts to match the given line against known header fields
    defined in SWCGraph.HEADER_FIELDS. It performs a case-insensitive match.

    Args:
        line (str): A single line from the SWC file header.

    Returns:
        Tuple[Optional[str], Optional[str]]: A tuple containing two elements:
            - The matched header field name (or None if no match)
            - The corresponding value (or None if no match)
    """

    for field in SWCGraph.HEADER_FIELDS:
        match = re.match(rf"{field}\s+(.+)", line, re.IGNORECASE)
        if match:
            return field, match.group(1).strip()
    return None, None


def load_swc(filename):
    """
    Load an SWC file and create an SWCGraph object.

    Args:
        filename (str): The path to the SWC file to be loaded.

    Returns:
        SWCGraph: An SWCGraph object representing the loaded SWC file.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        IOError: If there's an error reading the file.
    """
    tree = SWCGraph()
    try:
        with open(filename, "r") as file:
            for line_number, line in enumerate(file, 1):
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
                    logger.warning(
                        f"Line {line_number}: Invalid number of fields. Expected 7, got {len(parts)}. Skipping line: {line}"
                    )
                    continue

                try:
                    node_id, type_id, x, y, z, radius, parent_id = parts
                    node = SWCNode(node_id, type_id, x, y, z, radius, parent_id)
                    tree.add_node(node)
                except ValueError as e:
                    logger.warning(
                        f"Line {line_number}: {str(e)}. Skipping line: {line}"
                    )

    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        raise
    except IOError as e:
        logger.error(f"Error reading file {filename}: {str(e)}")
        raise

    return tree


output_file = open("output.txt", "w")
sys.stdout = output_file

swc_graph = load_swc("H16-06-013-05-01-01_576675715_m_dendriteaxon.CNG.swc")

# Access the metadata
print("Metadata:")
for key, value in swc_graph.metadata.items():
    print(f"{key}: {value}")

# Get all branch points
all_branch_points = swc_graph.get_branch_points()
print("\nAll branch points:")
for node in all_branch_points[None]:  # None key for all branch points
    print(node.to_string())

# Get the parent of a node with ID 10
parent_node = swc_graph.get_parent(10)
if parent_node:
    print(f"\nParent of node 10: {parent_node.to_string()}")
else:
    print("\nNode 10 has no parent")

# Get the children of a node with ID 5
children = swc_graph.get_children(5)
if children:
    print("\nChildren of node 5:")
    for child in children:
        print(child.to_string())
else:
    print("\nNode 5 has no children")

parent_node = swc_graph.get_parent(6)
if parent_node:
    print(f"\nParent of node 6: {parent_node.to_string()}")
else:
    print("\nNode 6 has no parent")

# Get branch points for specific types
type_specific_branch_points = swc_graph.get_branch_points(
    SWCNode.AXON, SWCNode.GLIA_PROCESSES
)

print("\nAxon branch points:")
for node in type_specific_branch_points.get(SWCNode.AXON, []):
    print(node.to_string())

print("\nGlia process branch points:")
for node in type_specific_branch_points.get(SWCNode.GLIA_PROCESSES, []):
    print(node.to_string())

print("\nAll nodes with multiple children:")
all_multi_children = swc_graph.get_nodes_with_multiple_children()
for node in all_multi_children:
    children = swc_graph.get_children(node.id)
    print(f"Node: {node.to_string()}")
    print(f"  Number of children: {len(children)}")
    print(f"  Children IDs: {[child.id for child in children]}")
    print()

print("\nSoma nodes with multiple children:")
soma_multi_children = swc_graph.get_nodes_with_multiple_children(SWCNode.SOMA)
for node in soma_multi_children:
    children = swc_graph.get_children(node.id)
    print(f"Node: {node.to_string()}")
    print(f"  Number of children: {len(children)}")
    print(f"  Children IDs: {[child.id for child in children]}")
    print()

output_file.close()
sys.stdout = sys.__stdout__
