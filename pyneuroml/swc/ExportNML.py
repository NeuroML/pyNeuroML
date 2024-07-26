from typing import Dict, List, Optional, Set

from LoadSWC import SWCGraph, SWCNode


class NeuroMLWriter:
    def __init__(self, swc_graph: "SWCGraph"):
        """
        Initialize the NeuroMLWriter.

        :param swc_graph: The SWC graph containing the neuronal morphology.
        """
        print("Initializing NeuroMLWriter")
        self.swc_graph: "SWCGraph" = swc_graph
        self.points: List[SWCNode] = swc_graph.nodes
        self.section_types: List[str] = SWCNode.TYPE_NAMES
        self.morphology_origin: str = swc_graph.metadata.get(
            "ORIGINAL_SOURCE", "Unknown"
        )
        self.seg_per_typ: List[int] = [0] * len(self.points)
        self.segment_content: List[str] = []
        self.group_content: List[str] = []
        self.cable_ids_vs_indices: Dict[int, int] = {}
        self.point_indices_vs_seg_ids: Dict[int, int] = {}
        self.segment_groups: Dict[str, List[str]] = {}
        self.next_segment_id: int = 0
        self.next_cable_id: int = 0
        self.cable_prefix_v2: str = "Cable_"
        self.verbose: bool = True
        self.processed_nodes: Set[int] = set()
        print(f"NeuroMLWriter initialized with {len(self.points)} points")

    def nml_string(self, version: str) -> str:
        """
        Generate the NeuroML string representation.

        :param version: The NeuroML version to use.
        :return: The NeuroML string representation.
        """
        print("Starting NeuroML generation")
        if (
            len(self.points) < 2
            or len(self.section_types) < 2
            or self.section_types[1].lower() != "soma"
        ):
            print("Error: null data or section types in nmlWrite")
            return ""

        cell_name = self.get_cell_name()
        start_point = self.find_start_point()

        print(f"Cell name: {cell_name}")
        print(f"Start point: {start_point}")

        self.parse_tree(start_point, start_point, True, True, version)

        nml_content = self.generate_nml_content(cell_name, version)

        print("NeuroML generation completed")
        return "\n".join(nml_content)

    def get_cell_name(self) -> str:
        """
        Generate a cell name based on the morphology origin.

        :return: The generated cell name.
        """
        print("Generating cell name")
        cell_name = "cell1"
        try:
            cell_name = (
                self.morphology_origin.split("/")[-1]
                .replace(".swc", "")
                .replace(".", "_")
                .replace("-", "_")
            )
            if cell_name[0].isdigit():
                cell_name = "Cell_" + cell_name
        except Exception as e:
            print(f"Error in generating cell name: {e}")
        print(f"Generated cell name: {cell_name}")
        return cell_name

    def find_start_point(self) -> SWCNode:
        """
        Find the starting point (soma) of the neuron.

        :return: The starting SWCNode (soma).
        """
        print("Finding start point (soma)")
        for point in self.points:
            if point.type == SWCNode.SOMA:
                print(f"Soma found: {point}")
                return point
        print("No soma points found, using first point")
        return self.points[0]

    def parse_tree(
        self,
        parent_point: SWCNode,
        this_point: SWCNode,
        new_cable: bool,
        new_cell: bool,
        version: str,
    ):
        """
        Parse the neural tree structure recursively.

        :param parent_point: The parent SWCNode.
        :param this_point: The current SWCNode being processed.
        :param new_cable: Whether this point starts a new cable.
        :param new_cell: Whether this is the start of a new cell.
        :param version: The NeuroML version being used.
        """
        print(
            f"Parsing tree: Point {this_point.id}, Type {this_point.type}, NewCable: {new_cable}, NewCell: {new_cell}"
        )

        this_type = max(this_point.type, 0)
        cable_id = -1

        if new_cable:
            cable_id = self.next_cable_id
            self.next_cable_id += 1
            self.cable_ids_vs_indices[this_point.id] = cable_id
            print(f"New cable created: Cable ID {cable_id}")
        else:
            cable_id = self.cable_ids_vs_indices[parent_point.id]
            self.cable_ids_vs_indices[this_point.id] = cable_id
            print(f"Using existing cable: Cable ID {cable_id}")

        fract_along_parent_cable = 1

        if this_point.type == SWCNode.SOMA:
            self.handle_soma(this_point, parent_point, cable_id, version, new_cell)
        elif this_point.type != SWCNode.SOMA and parent_point.type == SWCNode.SOMA:
            print("Parent point is on soma! Not creating 'real' segment")
            self.segment_content.append(
                "      <!-- Parent point is on soma! Not creating 'real' segment -->"
            )
            if (
                parent_point.id == 0
                and parent_point.id not in self.point_indices_vs_seg_ids
            ):
                fract_along_parent_cable = 0
        else:
            print(f"Creating segment for point {this_point.id}")
            self.create_segment(this_point, parent_point, cable_id, version, new_cable)

        if new_cable:
            print(f"Handling new cable for point {this_point.id}")
            self.handle_new_cable(
                this_point, cable_id, this_type, fract_along_parent_cable, version
            )

        self.processed_nodes.add(this_point.id)

        num_neighbs_not_done = sum(
            1 for nbr in this_point.children if nbr.id not in self.processed_nodes
        )
        diff_type_any_neighb = any(
            nbr.type != this_point.type
            for nbr in this_point.children
            if nbr.id not in self.processed_nodes
        )

        for next_point in this_point.children:
            if next_point.id not in self.processed_nodes:
                new_cable = diff_type_any_neighb or num_neighbs_not_done > 1
                if this_point.type == SWCNode.SOMA and next_point.type == SWCNode.SOMA:
                    new_cable = False
                    print(f"Continuing soma: {this_point.id} -> {next_point.id}")
                print(f"Processing child point {next_point.id}, NewCable: {new_cable}")
                self.parse_tree(this_point, next_point, new_cable, False, version)

    def handle_soma(
        self,
        this_point: SWCNode,
        parent_point: SWCNode,
        cable_id: int,
        version: str,
        new_cell: bool,
    ):
        """
        Handle the soma point in the neural structure.

        :param this_point: The current soma SWCNode.
        :param parent_point: The parent SWCNode.
        :param cable_id: The ID of the current cable.
        :param version: The NeuroML version being used.
        :param new_cell: Whether this is the start of a new cell.
        """
        print(f"Handling soma point: {this_point.id}")
        soma_points = [p for p in self.points if p.type == SWCNode.SOMA]

        if len(soma_points) == 3:
            if this_point.id == soma_points[1].id:  # Middle point
                print("Processing middle point of 3-point soma")
                self.segment_content.append(
                    "      <!-- First point is of a multi point soma => not spherical! -->"
                )
                self.segment_content.append("      <!-- Cylindrical soma... -->")

                # Create first segment (from second point to first point)
                seg_id = self.next_segment_id
                self.next_segment_id += 1
                self.point_indices_vs_seg_ids[this_point.id] = seg_id

                segment = [f'      <segment id="{seg_id}" name="Seg_{seg_id}"']
                if version.startswith("1"):
                    segment.append(f' cable="{cable_id}">')
                else:
                    segment.append(f'> <!-- "Cable" is {cable_id}-->')

                self.point_append(soma_points[1], 0.0, "proximal", segment)
                self.point_append(soma_points[0], 0.0, "distal", segment)
                segment.append("      </segment>")
                self.segment_content.extend(segment)

                # Create second segment (from second point to third point)
                seg_id = self.next_segment_id
                self.next_segment_id += 1
                self.point_indices_vs_seg_ids[soma_points[2].id] = seg_id

                segment = [f'      <segment id="{seg_id}" name="Seg_{seg_id}"']
                if version.startswith("1"):
                    segment.append(f' cable="{cable_id}">')
                else:
                    segment.append(f'> <!-- "Cable" is {cable_id}-->')

                segment.append(f'        <parent segment="{seg_id-1}"/>')
                self.point_append(soma_points[2], 0.0, "distal", segment)
                segment.append("      </segment>")
                self.segment_content.extend(segment)
            elif (
                this_point.id == soma_points[0].id or this_point.id == soma_points[2].id
            ):
                # Do nothing for first and third points as they're handled with the middle point
                pass
        elif new_cell and parent_point.type == SWCNode.SOMA:
            print("First point of multi-point soma")
            self.segment_content.append(
                "      <!-- First point is of a multi point soma => not spherical! -->"
            )
        else:
            print(f"Creating regular segment for soma point {this_point.id}")
            self.create_segment(this_point, parent_point, cable_id, version, True)

    def create_segment(
        self,
        this_point: SWCNode,
        parent_point: SWCNode,
        cable_id: int,
        version: str,
        new_cable: bool,
    ):
        """
        Create a segment in the NeuroML structure.

        :param this_point: The current SWCNode.
        :param parent_point: The parent SWCNode.
        :param cable_id: The ID of the current cable.
        :param version: The NeuroML version being used.
        :param new_cable: Whether this point starts a new cable.
        """
        print(
            f"Creating segment: Point {this_point.id}, Parent {parent_point.id}, Cable {cable_id}"
        )
        seg_id = self.next_segment_id
        self.next_segment_id += 1
        self.point_indices_vs_seg_ids[this_point.id] = seg_id

        segment = [f'      <segment id="{seg_id}" name="Seg_{seg_id}"']

        parent_element = self.get_parent_element(seg_id, parent_point, version)

        if version.startswith("1"):
            segment.append(f' cable="{cable_id}">')
        else:
            segment.append(f'> <!-- "Cable" is {cable_id}-->')

        if parent_element:
            segment.append(f"        {parent_element}")

        append_disjointed_proximal = (
            parent_element and "UNKNOWN_PARENT" in parent_element
        )
        if append_disjointed_proximal or new_cable:
            print(f"Appending proximal point for segment {seg_id}")
            self.point_append(parent_point, 0.0, "proximal", segment)

        print(f"Appending distal point for segment {seg_id}")
        self.point_append(this_point, 0.0, "distal", segment)

        segment.append("      </segment>")
        self.segment_content.extend(segment)

        if version.startswith("2"):
            cable_name = f"{self.cable_prefix_v2}{cable_id}"
            if cable_name not in self.segment_groups:
                self.segment_groups[cable_name] = []
            self.segment_groups[cable_name].append(str(seg_id))
            print(f"Added segment {seg_id} to cable group {cable_name}")

    def get_parent_element(
        self, seg_id: int, parent_point: SWCNode, version: str
    ) -> Optional[str]:
        """
        Get the parent element for a segment.

        :param seg_id: The ID of the current segment.
        :param parent_point: The parent SWCNode.
        :param version: The NeuroML version being used.
        :return: The parent element string or None.
        """
        print(
            f"Getting parent element for segment {seg_id}, parent point {parent_point.id}"
        )
        if seg_id > 0 and parent_point.id >= 0:
            if parent_point.id not in self.point_indices_vs_seg_ids:
                if (
                    parent_point.children
                    and parent_point.children[0].type == SWCNode.SOMA
                    and parent_point.children[0].id in self.point_indices_vs_seg_ids
                ):
                    par_seg_id = self.point_indices_vs_seg_ids[
                        parent_point.children[0].id
                    ]
                    print(f"Using soma child as parent: {par_seg_id}")
                elif (
                    parent_point.children
                    and parent_point.children[0].type == SWCNode.SOMA
                    and parent_point.children[0].id == 0
                ):
                    par_seg_id = 0
                    print("Using soma root as parent")
                else:
                    print(f"Unknown parent for segment {seg_id}: {parent_point.id}")
                    return (
                        f'<parent segment="UNKNOWN_PARENT_{parent_point.id}"/>'
                        if version.startswith("2")
                        else f' parent="UNKNOWN_PARENT_{parent_point.id}"'
                    )

                return (
                    f'<parent segment="{par_seg_id}"/>'
                    if version.startswith("2")
                    else f' parent="{par_seg_id}"'
                )
            else:
                par_seg_id = self.point_indices_vs_seg_ids[parent_point.id]
                print(f"Parent segment found: {par_seg_id}")
                return (
                    f'<parent segment="{par_seg_id}"/>'
                    if version.startswith("2")
                    else f' parent="{par_seg_id}"'
                )
        return ""

    def handle_new_cable(
        self,
        this_point: SWCNode,
        cable_id: int,
        this_type: int,
        fract_along_parent_cable: float,
        version: str,
    ):
        """
        Handle the creation of a new cable in the NeuroML structure.

        :param this_point: The current SWCNode.
        :param cable_id: The ID of the current cable.
        :param this_type: The type of the current point.
        :param fract_along_parent_cable: The fractional position along the parent cable.
        :param version: The NeuroML version being used.
        """
        print(
            f"Handling new cable: Point {this_point.id}, Cable {cable_id}, Type {this_type}"
        )
        if version.startswith("1"):
            fract_info = (
                f' fract_along_parent="{fract_along_parent_cable}"'
                if fract_along_parent_cable != 1
                else ""
            )
            self.group_content.append(
                f'      <cable id="{cable_id}" name="{self.segment_name(this_type)}_{self.seg_per_typ[this_type]}"{fract_info}>'
            )
            for group in self.get_groups_for_type(this_point):
                self.group_content.append(f"        <meta:group>{group}</meta:group>")
            self.group_content.append("      </cable>")
        else:
            for group in self.get_groups_for_type(this_point):
                if group not in self.segment_groups:
                    self.segment_groups[group] = []
                self.segment_groups[group].append(f"{self.cable_prefix_v2}{cable_id}")
                print(f"Added cable {cable_id} to group {group}")

        self.seg_per_typ[this_type] += 1

    def point_append(self, p: SWCNode, dz: float, loc: str, segment: List[str]):
        """
        Append a point to the segment content.

        :param p: The SWCNode to append.
        :param dz: The z-offset to apply.
        :param loc: The location identifier ('proximal' or 'distal').
        :param segment: The list of segment content strings.
        """
        print(
            f"Appending {loc} point: x={p.x:.6f}, y={p.y:.6f}, z={p.z + dz:.6f}, diameter={2 * p.radius:.6f}"
        )
        segment.append(
            f'        <{loc} x="{p.x:.6f}" y="{p.y:.6f}" z="{p.z + dz:.6f}" diameter="{2 * p.radius:.6f}"/>'
        )

    def get_groups_for_type(self, p: SWCNode) -> List[str]:
        """
        Get the groups associated with a given point type.

        :param p: The SWCNode to get groups for.
        :return: A list of group names.
        """
        print(f"Getting groups for point type {p.type}")
        groups = ["all"]
        type_groups = {
            SWCNode.SOMA: ["soma_group", "color_white"],
            SWCNode.AXON: ["axon_group", "color_grey"],
            SWCNode.BASAL_DENDRITE: ["basal_dendrite", "dendrite_group", "color_green"],
            SWCNode.APICAL_DENDRITE: [
                "apical_dendrite",
                "dendrite_group",
                "color_magenta",
            ],
        }
        groups.extend(
            type_groups.get(p.type, [f"SWC_group_{p.type}", "dendrite_group"])
        )
        print(f"Groups for point type {p.type}: {groups}")
        return groups

    def segment_name(self, ityp: int) -> str:
        """
        Get the segment name for a given type.

        :param ityp: The integer type of the segment.
        :return: The string name of the segment type.
        """
        print(f"Getting segment name for type {ityp}")
        if ityp >= 5:
            return f"user{ityp}"
        elif ityp < 0:
            print("Negative segment type converted to 'unknown'")
            return "unknown"
        else:
            return self.section_types[ityp]

    def generate_nml_content(self, cell_name: str, version: str) -> List[str]:
        """
        Generate the full NeuroML content.

        :param cell_name: The name of the cell.
        :param version: The NeuroML version being used.
        :return: A list of strings representing the NeuroML content.
        """
        print("Generating full NeuroML content")
        nml_content = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<neuroml xmlns="http://www.neuroml.org/schema/neuroml2"',
            f'    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
            f'    xsi:schemaLocation="http://www.neuroml.org/schema/neuroml2  https://raw.github.com/NeuroML/NeuroML2/development/Schemas/NeuroML2/NeuroML_v{version}.xsd"',
            f'    id="{cell_name}">',
            f'  <cell id="{cell_name}">',
            f"    <notes>",
            f"      Neuronal morphology exported in NeuroML v{version} from Python Based Converter )",
            f"      Original file: {self.morphology_origin}",
            f"    </notes>",
            f'    <morphology id="morphology_{cell_name}">',
        ]

        nml_content.extend(self.segment_content)

        if version.startswith("1"):
            nml_content.extend(self.group_content)
        else:
            for group_name, segments in self.segment_groups.items():
                print(f"Adding segment group: {group_name}")
                nml_content.append(f'      <segmentGroup id="{group_name}">')
                for segment in segments:
                    if segment.startswith(self.cable_prefix_v2):
                        nml_content.append(
                            f'        <include segmentGroup="{segment}"/>'
                        )
                    else:
                        nml_content.append(f'        <member segment="{segment}"/>')
                nml_content.append("      </segmentGroup>")

        nml_content.extend(["   </morphology>", " </cell>", "</neuroml>"])

        print("NeuroML content generation completed")
        return nml_content
