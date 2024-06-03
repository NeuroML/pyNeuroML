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
