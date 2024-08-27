"""
Module for exporting NeuroML from SWC files.

.. versionadded:: 1.3.9

Copyright 2024 NeuroML contributors
"""

import argparse
import logging
from typing import Dict, List, Optional, Set

from neuroml import (
    Cell,
    Member,
    Morphology,
    NeuroMLDocument,
    Point3DWithDiam,
    Property,
    Segment,
    SegmentGroup,
    SegmentParent,
)

from pyneuroml.io import write_neuroml2_file
from pyneuroml.utils.cli import build_namespace

from .LoadSWC import SWCGraph, SWCNode, load_swc

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class NeuroMLWriter:
    """
    A class to convert SWC graph data to NeuroML format.

    This class takes an SWC graph and converts it into a NeuroML representation,
    handling different neuron segment types and creating appropriate segment groups.
    """

    def __init__(self, swc_graph: SWCGraph) -> None:
        """
        Initialize the NeuroMLWriter with an SWC graph.

        :param swc_graph: The SWC graph to be converted to NeuroML.
        :type swc_graph: SWCGraph
        """
        logger.debug("Initializing NeuroMLWriter")
        self.swc_graph = swc_graph
        self.points = swc_graph.nodes
        self.section_types = [
            "undefined",
            "soma",
            "axon",
            "basal dendrite",
            "apical dendrite",
        ]
        self.morphology_origin = swc_graph.metadata.get("ORIGINAL_SOURCE", "Unknown")
        self.cell: Optional[Cell] = None
        self.nml_doc: Optional[NeuroMLDocument] = None
        self.point_indices_vs_seg_ids: Dict[str, str] = {}
        self.next_segment_id = 0
        self.processed_nodes: Set[int] = set()
        self.segment_types: Dict[str, int] = {}
        self.second_points_of_new_types: Set[str] = set()
        self.segment_groups: Dict[str, Set[str]] = {
            "all": set(),
            "soma_group": set(),
            "axon_group": set(),
            "dendrite_group": set(),
            "basal_dendrite": set(),
            "apical_dendrite": set(),
        }
        logger.debug(f"NeuroMLWriter initialized with {len(self.points)} points")

    def __create_cell(self) -> Cell:
        """
        Create a Cell object for the NeuroML representation.

        :return: The created Cell object.
        :rtype: Cell
        """
        logger.debug("Creating Cell object")
        cell_name = self.__get_cell_name()
        notes = f"Neuronal morphology exported from Python Based Converter. Original file: {self.morphology_origin}"
        self.cell = Cell(id=cell_name, notes=notes)
        self.cell.morphology = Morphology(id=f"morphology_{cell_name}")
        logger.debug(f"Created Cell object with name: {cell_name}")

        assert self.cell is not None
        return self.cell

    def __get_cell_name(self) -> str:
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

    def __generate_neuroml(self):
        """Generate NeuroML representation.

        Main worker function
        """
        logger.debug("Starting NeuroML generation")
        if (
            len(self.points) < 2
            or len(self.section_types) < 2
            or self.section_types[1].lower() != "soma"
        ):
            logger.error("Null data or section types in nmlWrite")
            return ""

        self.__create_cell()
        start_point = self.__find_start_point()

        logger.debug(f"Cell name: {self.cell.id}")
        logger.debug(f"Start point: {start_point}")

        self.__parse_tree(start_point, start_point)
        self.__create_segment_groups()

        self.nml_doc = NeuroMLDocument(id=self.cell.id)
        self.nml_doc.cells.append(self.cell)

        logger.debug("NeuroML generation completed")

    def __find_start_point(self) -> SWCNode:
        """
        Find the starting point (soma) in the SWC graph.

        :return: The starting point (soma) of the neuron.
        :rtype: SWCNode
        """
        logger.debug("Finding start point (soma)")
        for point in self.points:
            if point.type == SWCNode.SOMA:
                logger.debug(f"Soma found: {point}")
                return point
        logger.warning("No soma points found, using first point")
        return self.points[0]

    def __parse_tree(
        self,
        parent_point: SWCNode,
        this_point: SWCNode,
    ) -> None:
        """
        Recursively parse the SWC tree to create NeuroML segments.

        :param parent_point: The parent point of the current point.
        :type parent_point: SWCNode
        :param this_point: The current point being processed.
        :type this_point: SWCNode
        """
        if (
            this_point.id in self.processed_nodes
            and this_point.id not in self.second_points_of_new_types
        ):
            logger.debug(f"Point {this_point.id} already processed, skipping")
            return

        logger.debug(f"Parsing tree: Point {this_point.id}, Type {this_point.type}")

        type_change = this_point.type != parent_point.type
        new_branch = len(parent_point.children) > 1 if parent_point else False

        if this_point.type == SWCNode.SOMA:
            self.__handle_soma(this_point, parent_point)
        else:
            if this_point.id not in self.second_points_of_new_types:
                logger.debug(f"Processing non-soma point: {this_point.id}")
                self.__create_segment(
                    this_point, parent_point, new_branch or type_change
                )
                self.processed_nodes.add(this_point.id)
            else:
                logger.debug(
                    f"Point {this_point.id} already processed, skipping segment creation"
                )

        self.processed_nodes.add(this_point.id)

        for child_point in this_point.children:
            if child_point.id not in self.processed_nodes:
                self.__parse_tree(this_point, child_point)

    def __handle_soma(
        self,
        this_point: SWCNode,
        parent_point: SWCNode,
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
        """
        logger.debug(f"Handling soma point: {this_point.id}")

        if this_point.id in self.processed_nodes:
            logger.debug(f"Soma point {this_point.id} already processed, skipping")
            return

        soma_points = [p for p in self.points if p.type == SWCNode.SOMA]
        if len(soma_points) == 0:
            logger.debug("No soma points found, processing as non-soma point")
            return
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
                self.segment_types[self.next_segment_id] = SWCNode.SOMA
                self.__add_segment_to_groups(self.next_segment_id, SWCNode.SOMA)
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
                self.segment_types[self.next_segment_id] = SWCNode.SOMA
                self.__add_segment_to_groups(self.next_segment_id, SWCNode.SOMA)
                self.next_segment_id += 1

            elif (
                this_point.id == soma_points[1].id or this_point.id == soma_points[2].id
            ):
                pass  # These points are already handled

        elif len(soma_points) == 1:
            logger.debug("Processing single-point soma")
            segment = Segment(
                id=self.next_segment_id, name=f"soma_Seg_{self.next_segment_id}"
            )
            segment.proximal = Point3DWithDiam(
                x=this_point.x,
                y=this_point.y,
                z=this_point.z,
                diameter=2 * this_point.radius,
            )
            segment.distal = Point3DWithDiam(
                x=this_point.x,
                y=this_point.y,
                z=this_point.z,
                diameter=2 * this_point.radius,
            )
            self.cell.morphology.segments.append(segment)
            self.point_indices_vs_seg_ids[this_point.id] = self.next_segment_id
            self.segment_types[self.next_segment_id] = SWCNode.SOMA
            self.__add_segment_to_groups(self.next_segment_id, SWCNode.SOMA)
            self.next_segment_id += 1

        elif len(soma_points) > 3:
            logger.debug(f"Processing multi-point soma with {len(soma_points)} points")

            if this_point == soma_points[0]:
                logger.debug("Processing multi-point soma")

                for i in range(len(soma_points) - 1):
                    current_point = soma_points[i]
                    next_point = soma_points[i + 1]

                    segment = Segment(
                        id=self.next_segment_id,
                        name=f"soma_Seg_{self.next_segment_id}",
                    )

                    if i == 0:
                        segment.proximal = Point3DWithDiam(
                            x=current_point.x,
                            y=current_point.y,
                            z=current_point.z,
                            diameter=2 * current_point.radius,
                        )
                    else:
                        segment.parent = SegmentParent(
                            segments=self.next_segment_id - 1
                        )

                    segment.distal = Point3DWithDiam(
                        x=next_point.x,
                        y=next_point.y,
                        z=next_point.z,
                        diameter=2 * next_point.radius,
                    )

                    self.cell.morphology.segments.append(segment)
                    self.point_indices_vs_seg_ids[current_point.id] = (
                        self.next_segment_id
                    )
                    self.segment_types[self.next_segment_id] = SWCNode.SOMA
                    self.__add_segment_to_groups(self.next_segment_id, SWCNode.SOMA)

                    if current_point.id == this_point.id:
                        self.processed_nodes.add(current_point.id)

                    self.next_segment_id += 1

                self.processed_nodes.add(soma_points[-1].id)

            else:
                logger.debug(f"Soma point {this_point.id} not the first, skipping")

        logger.debug(f"Finished handling soma point: {this_point.id}")
        logger.debug(f"Processed nodes after soma: {self.processed_nodes}")
        logger.debug(f"Total segments created so far: {self.next_segment_id}")

    def __create_segment(
        self,
        this_point: SWCNode,
        parent_point: SWCNode,
        new_branch: True,
    ) -> None:
        """
        Create a NeuroML segment from an SWC point.

        :param this_point: The current point being processed.
        :type this_point: SWCNode
        :param parent_point: The parent point of the current point.
        :type parent_point: SWCNode
        :param new_branch: Whether this point starts a new branch.
        :type new_branch: bool
        """

        logger.debug(
            f"Creating segment: Point {this_point.id}, Type {this_point.type}, Parent {parent_point.id}"
        )
        seg_id = self.next_segment_id
        self.next_segment_id += 1

        segment_type = (
            self.section_types[this_point.type]
            if this_point.type < len(self.section_types)
            else f"type_{this_point.type}"
        )
        segment = Segment(id=seg_id, name=f"{segment_type}_Seg_{seg_id}")

        is_branch_point = len(parent_point.children) > 1
        is_type_change = this_point.type != parent_point.type
        parent_seg_id = self.point_indices_vs_seg_ids.get(parent_point.id)

        # Print the second point of new branches
        if parent_seg_id is not None and is_type_change and this_point.children:
            second_point = this_point.children[0]
            logger.debug(
                f"{second_point.id} {second_point.type} {second_point.x} {second_point.y} {second_point.z} {this_point.id}"
            )
            self.second_points_of_new_types.add(second_point.id)

            self.point_indices_vs_seg_ids[second_point.id] = seg_id
        if parent_point.id in self.point_indices_vs_seg_ids:
            parent_seg_id = self.point_indices_vs_seg_ids[parent_point.id]
            segment.parent = SegmentParent(segments=parent_seg_id)

        if is_type_change:
            segment.proximal = Point3DWithDiam(
                x=this_point.x,
                y=this_point.y,
                z=this_point.z,
                diameter=2 * this_point.radius,
            )

            if this_point.children:
                next_point = this_point.children[0]
                segment.distal = Point3DWithDiam(
                    x=next_point.x,
                    y=next_point.y,
                    z=next_point.z,
                    diameter=2 * next_point.radius,
                )
            else:
                segment.distal = Point3DWithDiam(
                    x=this_point.x,
                    y=this_point.y,
                    z=this_point.z,
                    diameter=2 * this_point.radius,
                )

        elif is_branch_point:
            logger.debug("Setting proximal and distal for branch point")
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
        elif this_point.id not in self.second_points_of_new_types:
            segment.distal = Point3DWithDiam(
                x=this_point.x,
                y=this_point.y,
                z=this_point.z,
                diameter=2 * this_point.radius,
            )

        self.cell.morphology.segments.append(segment)
        self.point_indices_vs_seg_ids[this_point.id] = seg_id
        self.segment_types[seg_id] = this_point.type
        self.__add_segment_to_groups(seg_id, this_point.type)

        self.processed_nodes.add(this_point.id)

        logger.debug(f"Created segment {seg_id} for point {this_point.id}")

    def __add_segment_to_groups(self, seg_id: int, segment_type: int) -> None:
        """
        Add a segment to the appropriate segment groups.

        :param seg_id: The ID of the segment to add.
        :type seg_id: int
        :param segment_type: The type of the segment.
        :type segment_type: int
        """
        groups = self.__get_groups_for_type(segment_type)
        for group in groups:
            self.segment_groups[group].add(seg_id)

    def __get_groups_for_type(self, segment_type: int) -> List[str]:
        """
        Get the list of group names a segment should belong to based on its type.

        :param segment_type: The type of the segment.
        :type segment_type: int
        :return: A list of group names the segment should belong to.
        :rtype: List[str]
        """
        groups = ["all"]
        if segment_type == SWCNode.SOMA:
            groups.extend(["soma_group"])
        elif segment_type == SWCNode.AXON:
            groups.extend(["axon_group"])
        elif segment_type == SWCNode.BASAL_DENDRITE:
            groups.extend(["basal_dendrite", "dendrite_group"])
        elif segment_type == SWCNode.APICAL_DENDRITE:
            groups.extend(["apical_dendrite", "dendrite_group"])
        elif segment_type >= 5:
            groups.append("dendrite_group")
        return groups

    def __create_segment_groups(self) -> None:
        """
        Create NeuroML segment groups based on the segments created.
        """
        logger.debug("Creating segment groups")

        for group_name, members in self.segment_groups.items():
            if members:
                group = SegmentGroup(id=group_name)
                for member_id in sorted(members):
                    group.members.append(Member(segments=member_id))
                self.cell.morphology.segment_groups.append(group)

        if not self.segment_types:
            logger.warning(
                "No segments were created. Skipping unbranched segment group creation."
            )
            return

        if any(seg_type == SWCNode.SOMA for seg_type in self.segment_types.values()):
            root_segment_id = min(
                seg_id
                for seg_id, seg_type in self.segment_types.items()
                if seg_type == SWCNode.SOMA
            )
        else:
            root_segment_id = min(self.segment_types.keys())

        self.cell.create_unbranched_segment_group_branches(
            root_segment_id,
            use_convention=True,
            reorder_segment_groups=True,
            optimise_segment_groups=True,
        )

        self.cell.properties.append(
            Property(tag="cell_type", value="converted_from_swc")
        )

        logger.debug("Segment groups created successfully")

    def export_to_nml_file(self, filename: str) -> None:
        """
        Export the NeuroML representation to a file.

        :param filename: The name of the file to export to.
        :type filename: str
        """
        if self.nml_doc is None:
            self.__generate_neuroml()

        write_neuroml2_file(self.nml_doc, filename, validate=True)
        logger.info(f"NeuroML file exported to: {filename}")


def convert_swc_to_neuroml(swc_file: str, neuroml_file: str):
    """Convert an SWC file to NeuroML

    :param swc_file: SWC input file
    :type swc_file: str
    :param neuroml_file: output NeuroML file
    :type neuroml_file: str
    """
    swc_graph = load_swc(swc_file)
    writer = NeuroMLWriter(swc_graph)
    writer.export_to_nml_file(neuroml_file)


def main(args=None):
    "Main CLI runner method"
    if args is None:
        args = process_args()

    a = build_namespace(DEFAULTS={}, a=args)
    logger.debug(a)

    if args.neuroml_file is None:
        neuroml_file = args.swc_file.replace(".swc", ".cell.nml")
    else:
        neuroml_file = a.neuroml_file

    convert_swc_to_neuroml(swc_file=a.swc_file, neuroml_file=neuroml_file)


def process_args():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=("Convert provided SWC file to NeuroML2")
    )

    parser.add_argument(
        "swcFile",
        type=str,
        metavar="<SWC file>",
        help="Name of the input SWC file",
    )

    parser.add_argument(
        "-neuromlFile",
        type=str,
        metavar="<NeuroML file>",
        help="Name of the output NeuroML file",
        required=False,
    )

    return parser.parse_args()
