import logging
import os
import tempfile
from typing import Dict, List, Optional, Set

import neuroml.writers as writers
from LoadSWC import SWCGraph, SWCNode, load_swc
from neuroml import (
    Cell,
    Include,
    Member,
    Morphology,
    NeuroMLDocument,
    Property,
    Segment,
    SegmentGroup,
)
from neuroml.nml.nml import Point3DWithDiam, SegmentParent

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NeuroMLWriter:
    def __init__(self, swc_graph: SWCGraph):
        """
        Initialize the NeuroMLWriter.

        :param swc_graph: The graph representation of the SWC file.
        :type swc_graph: SWCGraph
        """
        logger.info("Initializing NeuroMLWriter")
        self.swc_graph = swc_graph
        self.points: List[SWCNode] = swc_graph.nodes
        self.section_types: List[str] = [
            "undefined",
            "soma",
            "axon",
            "basal dendrite",
            "apical dendrite",
        ]
        self.morphology_origin: str = swc_graph.metadata.get(
            "ORIGINAL_SOURCE", "Unknown"
        )
        self.cell: Optional[Cell] = None
        self.nml_doc: Optional[NeuroMLDocument] = None
        self.seg_per_typ: List[int] = [0] * len(self.points)
        self.segment_groups: Dict[str, SegmentGroup] = {}
        self.cable_ids_vs_indices: Dict[int, List[int]] = {}
        self.point_indices_vs_seg_ids: Dict[int, int] = {}
        self.next_segment_id: int = 0
        self.next_cable_id: int = 0
        self.cable_prefix_v2: str = "Cable_"
        self.verbose: bool = True
        self.processed_nodes: Set[int] = set()
        self.segment_types: Dict[int, int] = {}
        logger.debug(f"NeuroMLWriter initialized with {len(self.points)} points")

    def create_cell(self) -> Cell:
        """
        Create a Cell object.

        :return: The created Cell object.
        :rtype: Cell
        """
        logger.info("Creating Cell object")
        cell_name = self.get_cell_name()

        self.cell = Cell(id=cell_name)
        self.cell.notes = f"Neuronal morphology exported from Python Based Converter. Original file: {self.morphology_origin}"

        morphology = Morphology(id=f"morphology_{cell_name}")
        self.cell.morphology = morphology

        logger.debug(f"Created Cell object with name: {cell_name}")
        return self.cell

    def get_cell_name(self) -> str:
        """
        Generate a cell name based on the morphology origin.

        :return: The generated cell name.
        :rtype: str
        """
        logger.debug("Generating cell name")
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
            logger.error(f"Error in generating cell name: {e}")
        logger.debug(f"Generated cell name: {cell_name}")
        return cell_name

    def nml_string(self, version: str) -> str:
        """
        Generate NeuroML string representation.

        :param version: NeuroML version.
        :type version: str
        :return: NeuroML string representation.
        :rtype: str
        """
        logger.info("Starting NeuroML generation")
        if (
            len(self.points) < 2
            or len(self.section_types) < 2
            or self.section_types[1].lower() != "soma"
        ):
            logger.error("Null data or section types in nmlWrite")
            return ""

        self.create_cell()
        start_point = self.find_start_point()

        logger.debug(f"Cell name: {self.cell.id}")
        logger.debug(f"Start point: {start_point}")

        self.parse_tree(start_point, start_point, True, True, version)
        self.create_segment_groups()

        self.nml_doc = NeuroMLDocument(id=self.cell.id)
        self.nml_doc.cells.append(self.cell)

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
            writers.NeuroMLWriter.write(self.nml_doc, temp_file)
            temp_file_path = temp_file.name

        with open(temp_file_path, "r") as temp_file:
            nml_content = temp_file.read()

        os.unlink(temp_file_path)

        logger.info("NeuroML generation completed")
        return nml_content

    def find_start_point(self) -> SWCNode:
        """
        Find the starting point (soma) in the SWC graph.

        :return: The starting point (soma) node.
        :rtype: SWCNode
        """
        logger.debug("Finding start point (soma)")
        for point in self.points:
            if point.type == SWCNode.SOMA:
                logger.debug(f"Soma found: {point}")
                return point
        logger.warning("No soma points found, using first point")
        return self.points[0]

    def parse_tree(
        self,
        parent_point: SWCNode,
        this_point: SWCNode,
        new_cable: bool,
        new_cell: bool,
        version: str,
    ) -> None:
        """
        Parse the SWC tree and create NeuroML segments.

        :param parent_point: The parent point in the SWC tree.
        :type parent_point: SWCNode
        :param this_point: The current point being processed.
        :type this_point: SWCNode
        :param new_cable: Whether to start a new cable.
        :type new_cable: bool
        :param new_cell: Whether this is a new cell.
        :type new_cell: bool
        :param version: NeuroML version.
        :type version: str
        """
        logger.debug(
            f"Parsing tree: Point {this_point.id}, Type {this_point.type}, NewCable: {new_cable}, NewCell: {new_cell}"
        )

        this_type = max(this_point.type, 0)
        cable_id = -1

        if new_cable:
            cable_id = self.next_cable_id
            self.next_cable_id += 1
            self.cable_ids_vs_indices[cable_id] = []
            logger.debug(f"New cable created: Cable ID {cable_id}")
        else:
            cable_id = max(self.cable_ids_vs_indices.keys())
            logger.debug(f"Using existing cable: Cable ID {cable_id}")

        if this_point.type == SWCNode.SOMA:
            self.handle_soma(this_point, parent_point, cable_id, version, new_cell)
        elif this_point.type != SWCNode.SOMA and parent_point.type == SWCNode.SOMA:
            logger.debug("Parent point is on soma! Not creating 'real' segment")
        else:
            logger.debug(f"Creating segment for point {this_point.id}")
            self.create_segment(this_point, parent_point, cable_id, version, new_cable)

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
                    logger.debug(f"Continuing soma: {this_point.id} -> {next_point.id}")
                logger.debug(
                    f"Processing child point {next_point.id}, NewCable: {new_cable}"
                )
                self.parse_tree(this_point, next_point, new_cable, False, version)

    def handle_soma(
        self,
        this_point: SWCNode,
        parent_point: SWCNode,
        cable_id: int,
        version: str,
        new_cell: bool,
    ) -> None:
        """
         Handle the creation of soma segments based on different soma representation cases.
         This method implements the soma representation guidelines as described in
        "Soma format representation in NeuroMorpho.Org as of version 5.3".
         For full details, see: https://github.com/NeuroML/Cvapp-NeuroMorpho.org/blob/master/caseExamples/SomaFormat-NMOv5.3.pdf

          The method handles the following cases:
         1. Single contour (most common, ~80% of cases):
          Converted to a three-point soma cylinder.
         2. Soma absent (~8% of cases):
          Not handled in this method (no changes made).
         3. Multiple contours (~5% of cases):
          Converted to a three-point soma cylinder, averaging all contour points.
         4. Multiple cylinders (~4% of cases):
          Kept as is, no conversion needed.
         5. Single point (~3% of cases):
          Converted to a three-point soma cylinder.
         The three-point soma representation consists of:
         - First point: Center of the soma
         - Second point: Shifted -r_s in y-direction
         - Third point: Shifted +r_s in y-direction
         Where r_s is the equivalent radius computed from the soma surface area.
         This method specifically handles cases 1, 3, and 5. Case 2 is not applicable,
         and case 4 is handled implicitly by not modifying the existing representation.

        :param this_point: The current soma point being processed.
        :type this_point: SWCNode
        :param parent_point: The parent point of the current soma point.
        :type parent_point: SWCNode
        :param cable_id: The ID of the current cable.
        :type cable_id: int
        :param version: NeuroML version.
        :type version: str
        :param new_cell: Whether this is a new cell.
        :type new_cell: bool
        """
        logger.debug(f"Handling soma point: {this_point.id}")
        soma_points = [p for p in self.points if p.type == SWCNode.SOMA]

        if len(soma_points) == 3:
            if this_point.id == soma_points[0].id:
                logger.debug("Processing first point of 3-point soma")
                middle_point = soma_points[1]
                end_point = soma_points[2]

                segment = Segment(
                    id=self.next_segment_id, name=f"Seg_{self.next_segment_id}"
                )
                segment.proximal = Point3DWithDiam(
                    x=middle_point.x,
                    y=middle_point.y,
                    z=middle_point.z,
                    diameter=2 * middle_point.radius,
                )
                segment.distal = Point3DWithDiam(
                    x=this_point.x,
                    y=this_point.y,
                    z=this_point.z,
                    diameter=2 * this_point.radius,
                )
                self.cell.morphology.segments.append(segment)
                self.point_indices_vs_seg_ids[this_point.id] = self.next_segment_id
                self.cable_ids_vs_indices[cable_id].append(self.next_segment_id)
                self.segment_types[self.next_segment_id] = SWCNode.SOMA
                self.next_segment_id += 1

                segment = Segment(
                    id=self.next_segment_id, name=f"Seg_{self.next_segment_id}"
                )
                segment.parent = SegmentParent(segments=self.next_segment_id - 1)
                segment.distal = Point3DWithDiam(
                    x=end_point.x,
                    y=end_point.y,
                    z=end_point.z,
                    diameter=2 * end_point.radius,
                )
                self.cell.morphology.segments.append(segment)
                self.point_indices_vs_seg_ids[end_point.id] = self.next_segment_id
                self.cable_ids_vs_indices[cable_id].append(self.next_segment_id)
                self.segment_types[self.next_segment_id] = SWCNode.SOMA
                self.next_segment_id += 1

            elif (
                this_point.id == soma_points[1].id or this_point.id == soma_points[2].id
            ):
                pass  # These points are already handled
        elif len(soma_points) > 3:
            if this_point.id == soma_points[0].id:
                logger.debug("Processing first point of multi-point soma")

                # First segment
                segment = Segment(
                    id=self.next_segment_id, name=f"Seg_{self.next_segment_id}"
                )
                segment.proximal = Point3DWithDiam(
                    x=this_point.x,
                    y=this_point.y,
                    z=this_point.z,
                    diameter=2 * this_point.radius,
                )
                next_point = soma_points[1]
                segment.distal = Point3DWithDiam(
                    x=next_point.x,
                    y=next_point.y,
                    z=next_point.z,
                    diameter=2 * next_point.radius,
                )
                self.cell.morphology.segments.append(segment)
                self.point_indices_vs_seg_ids[this_point.id] = self.next_segment_id
                self.cable_ids_vs_indices[cable_id].append(self.next_segment_id)
                self.segment_types[self.next_segment_id] = SWCNode.SOMA
                self.next_segment_id += 1

            elif this_point.id != soma_points[-1].id:
                # Middle segments
                parent_seg_id = self.point_indices_vs_seg_ids[parent_point.id]
                segment = Segment(
                    id=self.next_segment_id, name=f"Seg_{self.next_segment_id}"
                )
                segment.parent = SegmentParent(segments=parent_seg_id)
                next_point = soma_points[soma_points.index(this_point) + 1]
                segment.distal = Point3DWithDiam(
                    x=next_point.x,
                    y=next_point.y,
                    z=next_point.z,
                    diameter=2 * next_point.radius,
                )
                self.cell.morphology.segments.append(segment)
                self.point_indices_vs_seg_ids[this_point.id] = self.next_segment_id
                self.cable_ids_vs_indices[cable_id].append(self.next_segment_id)
                self.segment_types[self.next_segment_id] = SWCNode.SOMA
                self.next_segment_id += 1

            # We don't need to do anything for the last point, as it's already represented by the distal of the previous segment

        else:
            logger.debug(f"Creating regular segment for soma point {this_point.id}")
            self.create_segment(this_point, parent_point, cable_id, version, True)

    def create_segment(
        self,
        this_point: SWCNode,
        parent_point: SWCNode,
        cable_id: int,
        version: str,
        new_cable: bool,
    ) -> None:
        """
        Create a NeuroML segment.

        :param this_point: The current point being processed.
        :type this_point: SWCNode
        :param parent_point: The parent point of the current point.
        :type parent_point: SWCNode
        :param cable_id: The ID of the current cable.
        :type cable_id: int
        :param version: NeuroML version.
        :type version: str
        :param new_cable: Whether this is a new cable.
        :type new_cable: bool
        """
        logger.debug(
            f"Creating segment: Point {this_point.id}, Type {this_point.type}, Parent {parent_point.id}, Cable {cable_id}"
        )
        seg_id = self.next_segment_id
        self.next_segment_id += 1

        segment = Segment(id=seg_id, name=f"Seg_{seg_id}")

        if parent_point.id in self.point_indices_vs_seg_ids:
            parent_seg_id = self.point_indices_vs_seg_ids[parent_point.id]
            segment.parent = SegmentParent(segments=parent_seg_id)
        else:
            segment.proximal = Point3DWithDiam(
                x=parent_point.x,
                y=parent_point.y,
                z=parent_point.z,
                diameter=2 * parent_point.radius,
            )

        segment.distal = Point3DWithDiam(
            x=this_point.x,
            y=this_point.y,
            z=this_point.z,
            diameter=2 * this_point.radius,
        )

        self.cell.morphology.segments.append(segment)
        self.point_indices_vs_seg_ids[this_point.id] = seg_id
        self.cable_ids_vs_indices[cable_id].append(seg_id)
        self.segment_types[seg_id] = this_point.type

    def create_segment_groups(self) -> None:
        """
        Create segment groups based on the cell morphology.
        """
        logger.info("Creating segment groups")

        def get_groups_for_type(segment_type: int) -> List[str]:
            """
            Get the list of groups a segment belongs to based on its type.

            :param segment_type: The type of the segment.
            :type segment_type: int
            :return: List of group names the segment belongs to.
            :rtype: List[str]
            """
            groups = ["all"]
            if segment_type == SWCNode.SOMA:
                groups.extend(["soma_group", "color_white"])
            elif segment_type == SWCNode.AXON:
                groups.extend(["axon_group", "color_grey"])
            elif segment_type == SWCNode.BASAL_DENDRITE:
                groups.extend(["basal_dendrite", "dendrite_group", "color_green"])
            elif segment_type == SWCNode.APICAL_DENDRITE:
                groups.extend(["apical_dendrite", "dendrite_group", "color_magenta"])
            elif segment_type >= 5:
                groups.extend([f"SWC_group_{segment_type}", "dendrite_group"])
            elif segment_type == 0:
                groups.extend(["SWC_group_0_assuming_soma", "soma_group"])
            elif segment_type == -1:
                groups.extend(["SWC_group_-1_assuming_soma", "soma_group"])
            return groups

        # Initialize all groups
        all_groups = set(
            [
                "all",
                "soma_group",
                "axon_group",
                "dendrite_group",
                "basal_dendrite",
                "apical_dendrite",
            ]
        )
        all_groups.update([f"SWC_group_{i}" for i in range(-1, 10)])
        all_groups.update(["color_white", "color_grey", "color_green", "color_magenta"])

        group_members: Dict[str, Set[int]] = {group: set() for group in all_groups}

        # Assign segments to groups
        for segment in self.cell.morphology.segments:
            segment_type = self.segment_types[segment.id]
            groups = get_groups_for_type(segment_type)

            for group in groups:
                group_members[group].add(segment.id)

        # Create SegmentGroup objects
        for group_name, members in group_members.items():
            if members:
                group = SegmentGroup(id=group_name)
                for member_id in sorted(members):  # Sort to ensure consistent order
                    group.members.append(Member(segments=member_id))
                self.cell.morphology.segment_groups.append(group)

        # Add cable groups (assuming we're using NeuroML v2)
        for cable_id, segments in self.cable_ids_vs_indices.items():
            cable_group = SegmentGroup(id=f"{self.cable_prefix_v2}{cable_id}")
            for seg_id in sorted(set(segments)):  # Remove duplicates and sort
                cable_group.members.append(Member(segments=seg_id))
            self.cell.morphology.segment_groups.append(cable_group)

        # Add the cell_type property
        self.cell.properties.append(
            Property(tag="cell_type", value="converted_from_swc")
        )

        logger.info("Segment groups created successfully")

    def print_soma_segments(self) -> None:
        """
        Print information about soma segments.
        """
        logger.info("Printing soma segments:")
        for segment in self.cell.morphology.segments:
            if self.segment_types.get(segment.id) == SWCNode.SOMA:
                print(f"Soma Segment ID: {segment.id}")
                print(f"  Name: {segment.name}")
                if segment.proximal:
                    print(
                        f"  Proximal: x={segment.proximal.x}, y={segment.proximal.y}, z={segment.proximal.z}, diameter={segment.proximal.diameter}"
                    )
                print(
                    f"  Distal: x={segment.distal.x}, y={segment.distal.y}, z={segment.distal.z}, diameter={segment.distal.diameter}"
                )
                if segment.parent:
                    print(f"  Parent Segment ID: {segment.parent.segments}")
                print()

    def export_to_nml_file(self, filename: str) -> None:
        """
        Export the NeuroML document to a file.

        :param filename: The name of the file to export to.
        :type filename: str
        """
        if self.nml_doc is None:
            self.nml_string("2.0")  # This creates self.nml_doc if it doesn't exist

        writers.NeuroMLWriter.write(self.nml_doc, filename)
        logger.info(f"NeuroML file exported to: {filename}")
