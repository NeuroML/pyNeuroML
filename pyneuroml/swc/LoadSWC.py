import logging
import re

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SWCNode:
    """
    Represents a single node in an SWC (Standardized Morphology Data Format) file.

    The SWC format is a widely used standard for representing neuronal morphology data.
    It consists of a series of lines, each representing a single node or sample point
    along the neuronal structure. For more information on the SWC format, see:
    https://swc-specification.readthedocs.io/en/latest/swc.html

    :param UNDEFINED: ID representing an undefined node type
    :type UNDEFINED: int
    :param SOMA: ID representing a soma node
    :type SOMA: int
    :param AXON: ID representing an axon node
    :type AXON: int
    :param BASAL_DENDRITE: ID representing a basal dendrite node
    :type BASAL_DENDRITE: int
    :param APICAL_DENDRITE: ID representing an apical dendrite node
    :type APICAL_DENDRITE: int
    :param CUSTOM: ID representing a custom node type
    :type CUSTOM: int
    :param UNSPECIFIED_NEURITE: ID representing an unspecified neurite node
    :type UNSPECIFIED_NEURITE: int
    :param GLIA_PROCESSES: ID representing a glia process node
    :type GLIA_PROCESSES: int
    :param TYPE_NAMES: A mapping of node type IDs to their string representations
    :type TYPE_NAMES: dict
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

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the node.

        :return: A string representation of the node
        :rtype: str
        """
        type_name = self.TYPE_NAMES.get(self.type, f"Custom_{self.type}")
        return f"Node ID: {self.id}, Type: {type_name}, Coordinates: ({self.x:.2f}, {self.y:.2f}, {self.z:.2f}), Radius: {self.radius:.2f}, Parent ID: {self.parent_id}"


class SWCGraph:
    """Graph data structure holding SWCNode objects"""

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

        :param node: The node to be added
        :type node: SWCNode
        :raises ValueError: If a node with the same ID already exists in the graph or if multiple root nodes are detected
        """
        if any(existing_node.id == node.id for existing_node in self.nodes):
            self.logger.error(f"Duplicate node ID: {node.id}")
            raise ValueError(f"Duplicate node ID: {node.id}")

        if node.parent_id == -1:
            if self.root is not None:
                raise ValueError(
                    "Attempted to add multiple root nodes. Only one root node is allowed."
                )
            self.root = node
            self.logger.debug(f"Root node set: {node}")
        else:
            parent = next((n for n in self.nodes if n.id == node.parent_id), None)
            if parent:
                parent.children.append(node)
                self.logger.debug(f"Node {node.id} added as child to node {parent.id}")
            else:
                raise ValueError(
                    f"Parent node {node.parent_id} not found for node {node.id}"
                )

        self.nodes.append(node)
        self.logger.debug(f"New node added: {node}")

    def get_node(self, node_id):
        """
        Get a node from the graph by its ID.

        :param node_id: The ID of the node to retrieve
        :type node_id: int
        :return: The node with the specified ID
        :rtype: SWCNode
        :raises ValueError: If the specified node_id is not found in the SWC tree
        """
        node = next((n for n in self.nodes if n.id == node_id), None)
        if node is None:
            raise ValueError(f"Node {node_id} not found in the SWC tree")
        return node

    def add_metadata(self, key, value):
        """
        Add metadata to the SWC graph.

        :param key: The key for the metadata
        :type key: str
        :param value: The value for the metadata
        :type value: str
        """

        if key in self.HEADER_FIELDS:
            self.metadata[key] = value
            self.logger.debug(f"Added metadata: {key}: {value}")
        else:
            self.logger.warning(f"Ignoring unrecognized header field: {key}: {value}")

    def get_parent(self, node_id):
        """
        Get the parent node of a given node in the SWC tree.

        :param node_id: The ID of the node for which to retrieve the parent
        :type node_id: int
        :return: The parent Node object if the node has a parent, otherwise None
        :rtype: SWCNode or None
        :raises ValueError: If the specified node_id is not found in the SWC tree

        """

        node = self.get_node(node_id)
        if node.parent_id == -1:
            return None
        return self.get_node(node.parent_id)

    def get_children(self, node_id):
        """
        Get a list of child nodes for a given node.

        :param node_id: The ID of the node for which to get the children
        :type node_id: int
        :return: A list of SWCNode objects representing the children of the given node
        :rtype: list
        :raises ValueError: If the provided node_id is not found in the graph

        """

        parent_node = self.get_node(node_id)
        children = [node for node in self.nodes if node.parent_id == node_id]
        parent_node.children = children
        return children

    def get_nodes_with_multiple_children(self, type_id=None):
        """
        Get nodes with multiple children, optionally filtered by type.

        :param type_id: The type ID to filter nodes by (optional)
        :type type_id: int or None
        :return: A list of SWCNode objects that have multiple children and match the specified type (if provided)
        :rtype: list
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

        :param type_id: The type ID of the nodes to retrieve
        :type type_id: int
        :return: A list of SWCNode objects that have the specified type ID
        :rtype: list
        """
        return [node for node in self.nodes if node.type == type_id]

    def get_branch_points(self, *types):
        """
        Get all branch points (nodes with multiple children) of the given types.

        :param types: One or more node type IDs to filter the branch points by
        :type types: int
        :return: A dictionary of lists of SWCNode objects that represent branch points of the specified types
        :rtype: dict
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

    :param line: A single line from the SWC file header
    :type line: str
    :return: A tuple containing the matched header field name and corresponding value (or None if no match)
    :rtype: tuple

    """

    for field in SWCGraph.HEADER_FIELDS:
        match = re.match(rf"{field}\s+(.+)", line, re.IGNORECASE)
        if match:
            return field, match.group(1).strip()
    return None, None


def load_swc(filename):
    """
    Load an SWC file and create an SWCGraph object.

    :param filename: The path to the SWC file to be loaded
    :type filename: str
    :return: An SWCGraph object representing the loaded SWC file
    :rtype: SWCGraph
    :raises FileNotFoundError: If the specified file does not exist
    :raises IOError: If there's an error reading the file
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
