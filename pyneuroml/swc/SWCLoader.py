class Point:
    def __init__(self, x, y, z, diameter):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.diameter = float(diameter)


class Node:
    def __init__(self, node_id, type_id):
        self.id = int(node_id)
        self.type_id = int(type_id)
        self.type = None
        self.point = None
        self.parent_id = None
        self.parent = None
        self.children = []

    def set_point(self, x, y, z, diameter):
        self.point = Point(x, y, z, diameter)

class Morphology:
    NODE_TYPES = {
        0: "undefined",
        1: "soma",
        2: "axon",
        3: "basal dendrite",
        4: "apical dendrite",
        5: "fork point",
        6: "end point",
        7: "custom"
    }

    def __init__(self):
        self.nodes = {}
        self.root = None
        self.node_count = {type_name: 0 for type_name in self.NODE_TYPES.values()}

    def add_node(self, node):
        self.nodes[node.id] = node
        node.type = self.NODE_TYPES.get(node.type_id, "unknown")
        self.node_count[node.type] += 1

        if node.parent_id == -1:
            self.root = node
        elif node.parent_id in self.nodes:
            node.parent = self.nodes[node.parent_id]
            node.parent.children.append(node)