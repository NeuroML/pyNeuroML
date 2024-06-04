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


class Morphology:
    NEUROLEX_IDS = {
        "soma": "sao1044911821",
        "axon": "sao1369643253",
        "dendrite": "sao1211023249",
        "apical_dendrite": "sao285106870",
        "basal_dendrite": "sao735526996",
    }

    SWC_TO_GROUP = {
        1: ("soma", "Soma"),
        2: ("axon", "Axon"),
        3: ("dendrite", "BasalDendrite"),
        4: ("dendrite", "ApicalDendrite"),
    }

    def __init__(self):
        self.segments = {}
        self.segment_groups = {}
        self.root = None

    def add_segment(self, segment):
        self.segments[segment.id] = segment
        if segment.parent_id == -1:
            self.root = segment
        elif segment.parent_id in self.segments:
            segment.parent = self.segments[segment.parent_id]
            segment.parent.children.append(segment)

    def create_segment_groups(self):
        for group_id, (name, display_name) in self.SWC_TO_GROUP.items():
            self.segment_groups[name] = SegmentGroup(
                name, display_name, self.NEUROLEX_IDS.get(name)
            )

        for segment in self.segments.values():
            swc_type = int(segment.name.split("_")[1])
            if swc_type in self.SWC_TO_GROUP:
                group_name, _ = self.SWC_TO_GROUP[swc_type]
                self.segment_groups[group_name].add_member(segment.id)
