class Point:
    def __init__(self, x, y, z, diameter):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.diameter = float(diameter)


class Segment:
    def __init__(self, segment_id, name=None):
        self.id = int(segment_id)
        self.name = name or f"Segment_{segment_id}"
        self.proximal = None
        self.distal = None
        self.parent_id = None
        self.parent = None
        self.children = []

    def set_proximal(self, x, y, z, diameter):
        self.proximal = Point(x, y, z, diameter)

    def set_distal(self, x, y, z, diameter):
        self.distal = Point(x, y, z, diameter)


class SegmentGroup:
    def __init__(self, group_id, name, neurolex_id=None):
        self.id = group_id
        self.name = name
        self.neurolex_id = neurolex_id
        self.members = set()

    def add_member(self, segment_id):
        self.members.add(segment_id)
