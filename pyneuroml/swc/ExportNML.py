import os
from enum import Enum
from typing import Dict, List, Tuple

from LoadSWC import SWCGraph, SWCNode, load_swc
from neuroml import (
    Cell,
    Include,
    Member,
    Morphology,
    NeuroMLDocument,
    Point3DWithDiam,
    Segment,
    SegmentGroup,
    SegmentParent,
)
from neuroml.utils import validate_neuroml2
from neuroml.writers import NeuroMLWriter


class NeuroMLVersion(Enum):
    NEUROML_VERSION_1_8_1 = "1.8.1"
    NEUROML_VERSION_2_alpha = "2alpha"
    NEUROML_VERSION_2_beta = "2beta4"
    NEUROML_VERSION_2_3_1 = "2.3.1"

    def is_version_2(self):
        return not self.is_version_1()

    def is_version_2beta(self):
        return self == NeuroMLVersion.NEUROML_VERSION_2_beta

    def is_version_1(self):
        return self.value.startswith("1.")


class NeuroMLConverter:
    def __init__(self, swc_graph: SWCGraph, cell_name: str):
        self.swc_graph = swc_graph
        self.cell_name = cell_name
        self.segment_id = 0
        self.cable_id = 0
        self.segments: Dict[int, Segment] = {}
        self.cable_groups: Dict[str, List[int]] = {}
        self.point_to_segment: Dict[int, int] = {}
        self.CABLE_PREFIX = "Cable_"
        self.UNKNOWN_PARENT = "UNKNOWN_PARENT_"
        self.segment_groups: Dict[str, List[str]] = {}
        self.cable_ids_vs_indices: Dict[int, int] = {}
        self.processed_nodes: Dict[int, bool] = {}
        self.INDENT = "  "
        self.verbose = True

    def swc_to_neuroml(
        self, version: NeuroMLVersion, morphology_only: bool = False
    ) -> NeuroMLDocument:
        doc = NeuroMLDocument(id=self.cell_name)

        if version.is_version_1():
            doc.xmlns = "http://morphml.org/neuroml/schema"
            doc.xsi_schemaLocation = f"http://morphml.org/neuroml/schema http://www.neuroml.org/NeuroMLValidator/NeuroMLFiles/Schemata/v1.8.1/Level1/NeuroML_Level1_v1.8.1.xsd"
        else:
            doc.xmlns = "http://www.neuroml.org/schema/neuroml2"
            doc.xsi_schemaLocation = f"http://www.neuroml.org/schema/neuroml2 https://raw.github.com/NeuroML/NeuroML2/development/Schemas/NeuroML2/NeuroML_v{version.value}.xsd"

        if not morphology_only:
            cell = Cell(id=self.cell_name)
            doc.cells.append(cell)

        morphology = Morphology(id=f"morphology_{self.cell_name}")

        if not morphology_only:
            cell.morphology = morphology
        else:
            doc.morphology.append(morphology)

        start_point = self.find_start_point()
        if start_point is None:
            raise ValueError("Could not find a valid starting point in the SWC graph.")

        self.create_segments_and_groups(start_point, None, True, True, version)

        for segment in self.segments.values():
            morphology.segments.append(segment)

        self.create_segment_groups(morphology, version)

        if not morphology_only:
            cell.notes = f"Neuronal morphology exported in NeuroML v{version.value} from Python based converter\nOriginal file: {self.swc_graph.metadata.get('ORIGINAL_SOURCE', 'unknown')}"

        return doc

    def create_segments_and_groups(
        self,
        this_point: SWCNode,
        parent_point: SWCNode,
        new_cable: bool,
        new_cell: bool,
        version: NeuroMLVersion,
    ) -> None:
        if this_point is None:
            print("Warning: Encountered None point in create_segments_and_groups")
            return

        if self.verbose:
            print(
                f"\n-- Handling point: {this_point}, NewCable: {new_cable}\n-- With parent point: {parent_point}"
            )

        this_type = max(this_point.type, 0)
        cable_id = -1

        if new_cable:
            cable_id = self.cable_id
            self.cable_id += 1
            self.cable_ids_vs_indices[this_point.id] = cable_id
        else:
            cable_id = self.cable_ids_vs_indices.get(parent_point.id, -1)
            self.cable_ids_vs_indices[this_point.id] = cable_id

        fract_along_parent_cable = 1.0

        segment = None
        if (
            new_cell
            and this_point.type == 1
            and parent_point
            and parent_point.type == 1
        ):
            pass  # First point is of a multi point soma => not spherical!
        elif this_point.type != 1 and parent_point and parent_point.type == 1:
            if parent_point.id == 0 and parent_point.id not in self.point_to_segment:
                fract_along_parent_cable = 0
        else:
            segment = self.create_segment(
                this_point,
                parent_point,
                is_soma=(this_point.type == 1),
                version=version,
                fract_along_parent=fract_along_parent_cable,
            )
            self.segments[self.segment_id] = segment
            self.point_to_segment[this_point.id] = self.segment_id

            cable_name = f"{self.CABLE_PREFIX}{cable_id}"
            if cable_name not in self.cable_groups:
                self.cable_groups[cable_name] = []
            self.cable_groups[cable_name].append(self.segment_id)

            self.segment_id += 1

        if new_cable:
            self.handle_new_cable(
                this_point, cable_id, fract_along_parent_cable, version
            )

        self.processed_nodes[this_point.id] = True

        num_neighbs_not_done = 0
        diff_type_any_neighb = False

        for neighbor in self.swc_graph.get_children(this_point.id):
            if not self.processed_nodes.get(neighbor.id, False):
                num_neighbs_not_done += 1
                if neighbor.type != this_point.type:
                    diff_type_any_neighb = True

        for neighbor in self.swc_graph.get_children(this_point.id):
            if not self.processed_nodes.get(neighbor.id, False):
                new_cable_for_child = False
                if this_point.type == 1 and neighbor.type == 1:
                    new_cable_for_child = False
                elif diff_type_any_neighb or num_neighbs_not_done > 1:
                    new_cable_for_child = True
                self.create_segments_and_groups(
                    neighbor, this_point, new_cable_for_child, False, version
                )

    def create_segment(
        self,
        node: SWCNode,
        parent_node: SWCNode,
        is_soma: bool,
        version: NeuroMLVersion,
        fract_along_parent: float = 1.0,
    ) -> Segment:
        segment = Segment(id=self.segment_id, name=f"Seg_{self.segment_id}")

        if parent_node:
            parent_id = str(parent_node.id)
            if parent_id in self.point_to_segment:
                parent_segment_id = self.point_to_segment[parent_id]
                if version.is_version_1():
                    segment.parent = str(parent_segment_id)
                else:
                    segment.parent = SegmentParent(segments=str(parent_segment_id))
            elif is_soma and parent_node.type == 1:
                proximal = Point3DWithDiam(
                    x=parent_node.x,
                    y=parent_node.y,
                    z=parent_node.z,
                    diameter=parent_node.radius * 2,
                )
                segment.proximal = proximal
            else:
                if version.is_version_1():
                    segment.parent = parent_id
                else:
                    segment.parent = SegmentParent(segments=parent_id)

            if not is_soma or (is_soma and parent_node.type != 1):
                proximal = Point3DWithDiam(
                    x=parent_node.x,
                    y=parent_node.y,
                    z=parent_node.z,
                    diameter=parent_node.radius * 2,
                )
                segment.proximal = proximal

        distal = Point3DWithDiam(x=node.x, y=node.y, z=node.z, diameter=node.radius * 2)
        segment.distal = distal

        return segment

    def handle_new_cable(
        self,
        point: SWCNode,
        cable_id: int,
        fract_along_parent: float,
        version: NeuroMLVersion,
    ):
        cable_name = f"{self.CABLE_PREFIX}{cable_id}"
        if version.is_version_2():
            for group in self.get_groups_for_type(point):
                if group not in self.segment_groups:
                    self.segment_groups[group] = []
                self.segment_groups[group].append(cable_name)

    def get_groups_for_type(self, point: SWCNode) -> List[str]:
        groups = ["all"]
        type_code = point.type

        if type_code == 1:
            groups.extend(["soma_group", "color_white"])
        elif type_code == 2:
            groups.extend(["axon_group", "color_grey"])
        elif type_code == 3:
            groups.extend(["basal_dendrite", "dendrite_group", "color_green"])
        elif type_code == 4:
            groups.extend(["apical_dendrite", "dendrite_group", "color_magenta"])
        elif type_code in [5, 6, 7, 8, 9]:
            groups.extend([f"SWC_group_{type_code}", "dendrite_group"])
            if type_code == 5:
                groups.append("color_blue")
            elif type_code == 6:
                groups.append("color_yellow")
        elif type_code in [0, -1]:
            groups.extend([f"SWC_group_{type_code}_assuming_soma", "soma_group"])
        else:
            groups.append(f"SWC_group_{type_code}_unknown")

        return groups

    def create_segment_groups(
        self, morphology: Morphology, version: NeuroMLVersion
    ) -> None:
        for cable_name, segment_ids in self.cable_groups.items():
            seg_group = SegmentGroup(id=cable_name)
            for segment_id in segment_ids:
                seg_group.members.append(Member(segments=str(segment_id)))
            morphology.segment_groups.append(seg_group)

        for group_name, cable_names in self.segment_groups.items():
            seg_group = SegmentGroup(id=group_name)
            for cable_name in cable_names:
                if cable_name.startswith(self.CABLE_PREFIX):
                    seg_group.includes.append(Include(segment_groups=cable_name))
                else:
                    seg_group.members.append(Member(segments=cable_name))
            morphology.segment_groups.append(seg_group)

    def find_start_point(self) -> SWCNode:
        for node in self.swc_graph.nodes:
            if node.type == 1 and node.parent_id == -1:
                return node
        return self.swc_graph.nodes[0] if self.swc_graph.nodes else None


def export_neuroml(
    swc_graph: SWCGraph,
    filename: str,
    cell_name: str,
    version: NeuroMLVersion,
    morphology_only: bool = False,
) -> None:
    converter = NeuroMLConverter(swc_graph, cell_name)
    doc = converter.swc_to_neuroml(version, morphology_only)

    if not morphology_only:
        print("Validating cell morphology...")
        cell = doc.cells[0]
        try:
            cell.morphology.validate()
            print("Morphology validation successful.")
        except Exception as e:
            print(f"Morphology validation failed: {str(e)}")
            return
    else:
        print("Validating standalone morphology...")
        try:
            doc.morphology[0].validate()
            print("Morphology validation successful.")
        except Exception as e:
            print(f"Morphology validation failed: {str(e)}")
            return

    NeuroMLWriter.write(doc, filename)
    print(f"NeuroML file has been generated: {filename}")


if __name__ == "__main__":
    swc_file = "Case3_new.swc"

    try:
        swc_graph = load_swc(swc_file)
        if not swc_graph or not swc_graph.nodes:
            raise ValueError("SWC graph is empty or invalid.")

        cell_name = os.path.splitext(os.path.basename(swc_file))[0]

        print("SWC Graph structure:")
        for node in swc_graph.nodes:
            print(
                f"Node {node.id}: type={node.type}, parent={node.parent_id}, x={node.x}, y={node.y}, z={node.z}, radius={node.radius}"
            )

        print("\nAttempting to export to NeuroML...")
        export_neuroml(
            swc_graph,
            f"{cell_name}.nml",
            cell_name,
            NeuroMLVersion.NEUROML_VERSION_2_3_1,
        )
        print("Export completed successfully.")
    except FileNotFoundError:
        print(f"Error: The file '{swc_file}' was not found.")
    except ValueError as ve:
        print(f"Error: {str(ve)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        import traceback

        traceback.print_exc()
