"""
Module for loading SWC files

.. versionadded:: 1.3.9

Copyright 2024 NeuroML contributors
"""

import logging
import re
import typing

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

    def __init__(
        self,
        node_id: typing.Union[str, int],
        type_id: typing.Union[str, int],
        x: typing.Union[str, float],
        y: typing.Union[str, float],
        z: typing.Union[str, float],
        radius: typing.Union[str, float],
        parent_id: typing.Union[str, int],
    ):
        try:
            self.id = int(node_id)
            self.type = int(type_id)
            self.x = float(x)
            self.y = float(y)
            self.z = float(z)
            self.radius = float(radius)
            self.parent_id = int(parent_id)
            self.children: typing.List[SWCNode] = []
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

    def __init__(self) -> None:
        self.nodes: typing.List[SWCNode] = []
        self.root: typing.Optional[SWCNode] = None
        self.metadata: typing.Dict[str, str] = {}

    def add_node(self, node: SWCNode):
        """
        Add a node to the SWC graph.

        :param node: The node to be added
        :type node: SWCNode
        :raises ValueError: If a node with the same ID already exists in the graph or if multiple root nodes are detected
        """
        if any(existing_node.id == node.id for existing_node in self.nodes):
            raise ValueError(f"Duplicate node ID: {node.id}")

        if node.parent_id == -1:
            if self.root is not None:
                raise ValueError(
                    "Attempted to add multiple root nodes. Only one root node is allowed."
                )
            self.root = node
            logger.debug(f"Root node set: {node}")
        else:
            parent = next((n for n in self.nodes if n.id == node.parent_id), None)
            if parent:
                parent.children.append(node)
                logger.debug(f"Node {node.id} added as child to node {parent.id}")
            else:
                raise ValueError(
                    f"Parent node {node.parent_id} not found for node {node.id}"
                )

        self.nodes.append(node)
        logger.debug(f"New node added: {node}")

    def get_node(self, node_id: int) -> SWCNode:
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

    def add_metadata(self, key: str, value: str):
        """
        Add metadata to the SWC graph.

        :param key: The key for the metadata
        :type key: str
        :param value: The value for the metadata
        :type value: str
        """

        if key in self.HEADER_FIELDS:
            self.metadata[key] = value
            logger.debug(f"Added metadata: {key}: {value}")
        else:
            logger.warning(f"Ignoring unrecognized header field: {key}: {value}")

    def get_parent(self, node_id: int) -> typing.Optional[SWCNode]:
        """
        Get the parent node of a given node in the SWC tree.

        :param node_id: The ID of the node for which to retrieve the parent
        :type node_id: int
        :return: The parent node if the node has a parent, otherwise None
        :rtype: SWCNode or None
        :raises ValueError: If the specified node_id is not found in the SWC tree

        """

        node = self.get_node(node_id)
        if node.parent_id == -1:
            logger.info("Root node given, does not have a parent. Returning None")
            return None
        return self.get_node(node.parent_id)

    def get_children(self, node_id: int) -> typing.List[SWCNode]:
        """
        Get a list of child nodes for a given node.

        :param node_id: The ID of the node for which to get the children
        :type node_id: int
        :return: A list of SWCNode objects representing the children of the given node
        :rtype: list
        :raises ValueError: If the provided node_id is not found in the graph

        """

        children = [node for node in self.nodes if node.parent_id == node_id]
        return children

    def get_nodes_with_multiple_children(
        self, type_id: typing.Optional[int] = None
    ) -> typing.List[SWCNode]:
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
            logger.debug(
                f"Found {len(nodes)} nodes of type {type_id} with multiple children."
            )
        else:
            logger.debug(f"Found {len(nodes)} nodes with multiple children.")

        return nodes

    def get_nodes_by_type(self, type_id: int) -> typing.List[SWCNode]:
        """
        Get a list of nodes of a specific type.

        :param type_id: The type ID of the nodes to retrieve
        :type type_id: int
        :return: A list of SWCNode objects that have the specified type ID
        :rtype: list
        """
        return [node for node in self.nodes if node.type == type_id]

    def get_branch_points(
        self, types: typing.Optional[typing.List[int]]
    ) -> typing.Union[typing.List[SWCNode], typing.Dict[int, typing.List[SWCNode]]]:
        """
        Get all branch points (nodes with multiple children) of the given types.

        :param types: One or more node type IDs to filter the branch points by
        :type types: int
        :return: if node types are given, a dictionary with keys as the node
            type and lists of nodes as values; otherwise a list of all nodes
        :rtype: list or dict
        """

        if not types:
            # If no types are specified, return all branch points
            return self.get_nodes_with_multiple_children()
        else:
            branch_points = {}
            for type_id in types:
                branch_points[type_id] = self.get_nodes_with_multiple_children(type_id)
            return branch_points

    def export_to_swc_file(self, filename: str) -> None:
        """
        Export the SWCGraph to a new SWC file.

        :param filename: The path to the output SWC file
        :type filename: str
        """
        with open(filename, "w") as file:
            # Write metadata
            for key, value in self.metadata.items():
                file.write(f"# {key} {value}\n")

            # Write node data
            for node in sorted(self.nodes, key=lambda n: n.id):
                file.write(
                    f"{node.id} {node.type} {node.x:.4f} {node.y:.4f} {node.z:.4f} {node.radius:.4f} {node.parent_id}\n"
                )


def parse_header(
    line_number: int, line: str
) -> typing.Optional[typing.Tuple[str, str]]:
    """
    Parse a header line from an SWC file.

    :param line_number: line number, for logging purposes
    :type line_number: int
    :param line: A single line from the SWC file header
    :type line: str
    :return: A tuple containing the matched header field name and corresponding value (or None if no match)
    :rtype: tuple

    """

    for field in SWCGraph.HEADER_FIELDS:
        match = re.match(rf"{field}\s+(.+)", line, re.IGNORECASE)
        if match:
            return field, match.group(1).strip()

    logger.warning(
        f"Ignoring line {line_number}: does not match header format: # {line}"
    )
    return None


def load_swc(filename: str) -> SWCGraph:
    """
    Load an SWC file and create an SWCGraph object.

    :param filename: The path to the SWC file to be loaded
    :type filename: str
    :return: An SWCGraph object representing the loaded SWC file
    :rtype: SWCGraph
    :raises ValueError: If a non header line with more than the required number
        of fields is found
    """

    tree = SWCGraph()
    with open(filename, "r") as file:
        point_line_count = 0
        for line_number, line in enumerate(file, 1):
            line = line.strip()
            logger.debug(f"Processing line {line_number}: '{line}'")

            if not line:
                continue

            if line.startswith("#"):
                header = parse_header(line_number, line[1:].strip())
                if header:
                    tree.add_metadata(header[0], header[1])
                continue

            parts = line.split()
            if len(parts) != 7:
                raise ValueError(
                    f"Line {line_number}: Invalid number of fields. Expected 7, got {len(parts)}. Skipping line: {line}"
                )

            # the add_node bit throws errors if things don't work out as
            # expected
            node_id, type_id, x, y, z, radius, parent_id = parts

            if point_line_count == 0:
                if parent_id != "-1":
                    raise ValueError(
                        f"First point in file must have parent '-1' (root). Got: {line}"
                    )

            node = SWCNode(node_id, type_id, x, y, z, radius, parent_id)
            tree.add_node(node)
            point_line_count += 1

    # add file name as new metadata if not included
    if "ORIGINAL_SOURCE" not in tree.metadata.keys():
        tree.metadata["ORIGINAL_SOURCE"] = filename

    logger.info(f"Processed {point_line_count} SWC points in {line_number} lines")

    return tree
