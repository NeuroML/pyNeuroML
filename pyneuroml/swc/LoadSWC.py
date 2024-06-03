class SWCNode:
    TYPE_NAMES = {
        0: "undefined",
        1: "soma",
        2: "axon",
        3: "basal dendrite",
        4: "apical dendrite",
        5: "custom",
        6: "unspecified neurite",
        7: "glial process",
    }

    def __init__(self, index, type, x, y, z, radius, parent):
        self.index = int(index)
        self.type = int(type)
        self.type_name = self.TYPE_NAMES.get(self.type, "custom")
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.radius = float(radius)
        self.parent = int(parent)
        self.children = []
        self.distance_to_soma = None

    def get_position(self):
        return (self.x, self.y, self.z)

    def get_shape(self, parent=None):
        if not parent:
            return "sphere" if self.parent == -1 else None
        if self.x == parent.x and self.y == parent.y and self.z == parent.z:
            return "sphere" if self.radius == parent.radius else "error"
        elif self.radius == parent.radius:
            return "cylinder"
        else:
            return "conical frustum"


class SWCFile:
    def __init__(self, filename):
        self.filename = filename
        self.nodes = {}
        self.root = None
        self.metadata = {}
        self.load()
        self._calculate_distances()
