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
        # segment group types
        self.section_types = [
            "undefined",
            "soma",
            "axon",
            "basal dendrite",
            "apical dendrite",
        ]
        # TODO: use something better than UNKNOWN
        self.morphology_origin = swc_graph.metadata.get("ORIGINAL_SOURCE", "Unknown")
        # hold the cell object
        self.cell: Optional[Cell] = None
        # holds the NeuroML document object
        self.nml_doc: Optional[NeuroMLDocument] = None
        # dict, key is the index of a point, value is the corresponding segment
        # id
        self.point_indices_vs_seg_ids: Dict[int, int] = {}
        # keeps track of the next segment id, incremented after a segment is
        # processed
        self.next_segment_id = 0
        # stores processed nodes
        self.processed_nodes: Set[int] = set()
        # dict, key is the segment id, value is the segment type
        self.segment_types: Dict[int, int] = {}
        # set of points that are the second point after a type change
        self.second_points_of_new_types: Set[int] = set()
        # holds different default segment groups
        self.segment_groups: Dict[str, Set[int]] = {
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
        self.cell = Cell(id=cell_name)
        self.cell.morphology = Morphology(id=f"morphology_{cell_name}", notes=notes)
        logger.debug(f"Created Cell object with name: {cell_name}")

        assert self.cell
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

        if this_point.type == SWCNode.SOMA:
            self.__handle_soma(parent_point, this_point)
        else:
            if this_point.id not in self.second_points_of_new_types:
                logger.debug(f"Processing non-soma point: {this_point.id}")
                self.__create_segment(parent_point, this_point)
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
        parent_point: SWCNode,
        this_point: SWCNode,
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

        :param parent_point: The parent point of the current soma point.
        :type parent_point: SWCNode
        :param this_point: The current soma point being processed.
        :type this_point: SWCNode
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
        parent_point: SWCNode,
        this_point: SWCNode,
    ) -> None:
        """
        Create a NeuroML segment from an SWC point.


        Cases:

        1. if a point's parent is a soma point, but the point itself is not, we
           do not create a new segment with the point as the distal point (under
           the assumption that the distal of the previous point is the
           proximal). Instead, in this case, the point becomes the proximal of
           the new segment, and its first child becomes the distal point.

           This is because, it's quite possible for non-soma points to not be
           connected to the soma, i.e., they can float at a distance. While
           from a morphology perspective, this is incorrect, from a modelling
           perspective, this is OK since by specifying the soma as a parent, we
           continue to have the soma and the floating segment electrically
           connected.


        2. if the parent and child are of different types, but the parent is
           not of a soma type, treat it like any other segment (below)

        3. create new segment for all other cases with current point as distal
           and the parent's distal assumed to be proximal (which does not need to
           be specified)

        :param parent_point: The parent point of the current point.
        :type parent_point: SWCNode
        :param this_point: The current point being processed.
        :type this_point: SWCNode
        """

        # cell cannot be None at this point
        assert self.cell

        logger.debug(
            f"Creating segment: Point {this_point.id}, Type {this_point.type}, Parent {parent_point.id}"
        )
        seg_id = self.next_segment_id
        self.next_segment_id += 1

        # get the segment type
        try:
            segment_type = self.section_types[this_point.type]
        except IndexError:
            segment_type = f"type_{this_point.type}"

        # is first point: only possible if there's no soma at all
        is_first_point = parent_point == this_point
        # is the point type changing?
        is_type_change = this_point.type != parent_point.type
        # is the parent a soma: special case
        is_parent_soma = parent_point.type == SWCNode.SOMA

        # Case 1
        if is_first_point or (is_type_change and is_parent_soma):
            if is_first_point:
                logger.debug(f"First point: {this_point}")
            else:
                logger.debug(f"Type change and parent is soma: {this_point}")

            # there must be a second point, otherwise it should error
            second_point = this_point.children[0]

            # parent segment
            parent = None
            if not is_first_point:
                parent_seg_id = self.point_indices_vs_seg_ids.get(parent_point.id, None)

                if parent_seg_id is not None:
                    parent = self.cell.get_segment(parent_seg_id)
                else:
                    raise ValueError(f"Parent not found for {this_point}")

            # addition to segment groups is handled separately after all
            # segments have been created
            self.cell.add_segment(
                prox=[this_point.x, this_point.y, this_point.z, 2 * this_point.radius],
                dist=[
                    second_point.x,
                    second_point.y,
                    second_point.z,
                    2 * second_point.radius,
                ],
                seg_id=seg_id,
                name=f"{segment_type.replace(' ', '_')}_Seg_{seg_id}",
                parent=parent,
                fraction_along=1.0,
                use_convention=False,
                reorder_segment_groups=False,
                optimise_segment_groups=False,
            )

            self.point_indices_vs_seg_ids[this_point.id] = seg_id
            self.point_indices_vs_seg_ids[second_point.id] = seg_id
            self.second_points_of_new_types.add(second_point.id)

        else:
            # segment parent id
            parent_seg_id = self.point_indices_vs_seg_ids.get(parent_point.id, None)

            if parent_seg_id is not None:
                parent = self.cell.get_segment(parent_seg_id)
            else:
                raise ValueError(f"Parent not found for {this_point}")

            self.cell.add_segment(
                prox=None,
                dist=[this_point.x, this_point.y, this_point.z, 2 * this_point.radius],
                seg_id=seg_id,
                name=f"{segment_type.replace(' ', '_')}_Seg_{seg_id}",
                parent=parent,
                fraction_along=1.0,
                use_convention=False,
                reorder_segment_groups=False,
                optimise_segment_groups=False,
            )
            self.point_indices_vs_seg_ids[this_point.id] = seg_id

        # common for all cases
        # add to groups
        self.segment_types[seg_id] = this_point.type
        self.__add_segment_to_groups(seg_id, this_point.type)

        self.processed_nodes.add(this_point.id)

        logger.debug(f"Created segment {seg_id} for point {this_point.id}")

    def __add_segment_to_groups(self, seg_id: int, segment_type: int) -> None:
        """
        Add a segment to the appropriate segment group set.

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
        assert self.cell

        if not self.segment_types:
            logger.warning("No segments were created. Skipping segment group creation.")
            return

        logger.debug("Creating segment groups")
        for group_name, members in self.segment_groups.items():
            if members:
                group = SegmentGroup(id=group_name)
                for member_id in sorted(members):
                    group.members.append(Member(segments=member_id))
                self.cell.morphology.segment_groups.append(group)

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

    def generate_neuroml(self, standalone_morphology: bool = True) -> NeuroMLDocument:
        """Generate NeuroML representation.

        Main worker function

        :param standalone_morphology: export morphology as standalone object
            (not as part of a Cell object)
        :type standalone_morphology: bool
        :returns: the NeuroML document
        :rtype: NeuroMLDocument
        """
        if self.nml_doc is not None:
            return self.nml_doc

        logger.debug("Starting NeuroML generation")
        if len(self.points) < 2:
            ValueError("SWC has fewer than two points. Cannot convert.")

        self.__create_cell()
        assert self.cell

        start_point = self.swc_graph.root

        logger.debug(f"Start point: {start_point}")

        # create all the segments
        self.__parse_tree(start_point, start_point)
        # create all the groups
        self.__create_segment_groups()

        self.nml_doc = NeuroMLDocument(id=self.cell.id)

        if standalone_morphology:
            self.nml_doc.morphology.append(self.cell.morphology)
        else:
            self.nml_doc.cells.append(self.cell)

        logger.debug("NeuroML generation completed")

        return self.nml_doc

    def export_to_nml_file(
        self, filename: str, standalone_morphology: bool = True
    ) -> None:
        """
        Export the NeuroML representation to a file.

        :param filename: The name of the file to export to.
        :type filename: str
        :param standalone_morphology: export morphology as standalone object
            (not as part of a Cell object)
        :type standalone_morphology: bool
        """
        self.generate_neuroml(standalone_morphology)
        assert self.nml_doc
        assert self.cell

        write_neuroml2_file(self.nml_doc, filename, validate=True)
        logger.info(f"NeuroML file exported to: {filename}")


def convert_swc_to_neuroml(
    swc_file: str,
    neuroml_file: Optional[str] = None,
    standalone_morphology: bool = True,
) -> NeuroMLDocument:
    """Convert an SWC file to NeuroML.

    If `neuroml_file` is provided, will also write to file.

    :param swc_file: SWC input file
    :type swc_file: str
    :param neuroml_file: output NeuroML file (optional)
    :type neuroml_file: str
    :param standalone_morphology: export morphology as standalone object
        (not as part of a Cell object)
    :type standalone_morphology: bool

    :returns: NeuroML document
    :rtype: NeuroMLDocument
    """
    swc_graph = load_swc(swc_file)
    writer = NeuroMLWriter(swc_graph)
    if neuroml_file is not None:
        writer.export_to_nml_file(neuroml_file, standalone_morphology)
    return writer.generate_neuroml(standalone_morphology)


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

    convert_swc_to_neuroml(
        swc_file=a.swc_file,
        neuroml_file=neuroml_file,
        standalone_morphology=a.morph_only,
    )


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

    parser.add_argument(
        "-morphOnly",
        action="store_true",
        help="Export as standalone Morphology, not as a Cell",
        default=False,
    )

    return parser.parse_args()
