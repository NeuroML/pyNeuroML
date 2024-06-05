import networkx as nx


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
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid data types in SWC line: {e}")

    def __repr__(self):
        type_name = self.TYPE_NAMES.get(self.type, f"Custom_{self.type}")
        return f"SWCNode(id={self.id}, type={type_name}, x={self.x:.2f}, y={self.y:.2f}, z={self.z:.2f}, radius={self.radius:.2f}, parent_id={self.parent_id})"


class SWCGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.root = None

    def add_node(self, node):
        if node.id in self.graph:
            raise ValueError(f"Duplicate node ID: {node.id}")
        self.graph.add_node(node.id, data=node)
        if node.parent_id == -1:
            if self.root is not None:
                raise ValueError("Multiple root nodes found")
            self.root = node.id
        elif node.parent_id not in self.graph:
            raise ValueError(f"Parent {node.parent_id} not found for node {node.id}")
        else:
            self.graph.add_edge(node.parent_id, node.id)

    def get_node(self, node_id):
        return self.graph.nodes[node_id]["data"]

    def get_parent(self, node_id):
        node = self.get_node(node_id)
        return self.get_node(node.parent_id) if node.parent_id != -1 else None

    def get_descendants(self, node_id):
        node = self.get_node(node_id)
        descendants = []
        queue = [node_id]
        while queue:
            node_id = queue.pop(0)
            node = self.get_node(node_id)
            queue.extend(self.graph.successors(node_id))
            descendants.append(node)
        return descendants

    def get_nodes_with_multiple_children(self, type_id=None):
        nodes = []
        for node_id, out_degree in self.graph.out_degree():
            if out_degree > 1:
                node = self.get_node(node_id)
                if type_id is None or node.type == type_id:
                    nodes.append(node)
        return nodes
