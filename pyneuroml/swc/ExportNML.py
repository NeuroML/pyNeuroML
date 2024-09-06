"""
Module for exporting NeuroML from SWC files.

.. versionadded:: 1.3.9

Copyright 2024 NeuroML contributors
"""

import argparse
import logging
import time
from typing import Dict, Optional, Set

from neuroml import (
    Cell,
    NeuroMLDocument,
)
from neuroml.utils import component_factory

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
        # all nodes
        self.points = swc_graph.nodes
        # soma nodes
        self.soma_points = self.swc_graph.get_nodes_by_type(SWCNode.SOMA)
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

        # Set of points that are used to create segments during the processing
        # of other points, for example, after a type change when the current
        # point is used as the proximal and the next point is used as distal.
        # The trees from these points do need to be parsed, but they are not
        # used for creating segments again.
        self.unprocessed_but_in_segment_nodes: Set[int] = set()

        # root segment id
        self.root_segment_id = -1

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
        self.cell = component_factory("Cell", id=cell_name, notes=notes)
        self.cell.setup_nml_cell(
            default_groups=["all", "soma_group", "dendrite_group", "axon_group"]
        )

        # clear biophysical properties
        self.cell.biophysical_properties = None

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
            and this_point.id not in self.unprocessed_but_in_segment_nodes
        ):
            logger.debug(f"Point {this_point.id} already processed, skipping")
            return

        logger.debug(f"Parsing tree: Point {this_point.id}, Type {this_point.type}")

        # All soma points will be used for segment creation the first time a
        # soma point is encountered, but they can all be roots of sub-trees so
        # their trees do need to be parsed again below.
        if this_point.type == SWCNode.SOMA:
            self.__handle_soma(parent_point, this_point)
        else:
            # do not create a segment, but do parse the tree from this point
            if this_point.id not in self.unprocessed_but_in_segment_nodes:
                self.__create_segment(parent_point, this_point)
            else:
                logger.debug(
                    f"Point {this_point.id} processed as second point for a segment, skipping"
                )

        # mark point as processed
        # only done here, not anywhere else
        self.processed_nodes.add(this_point.id)

        for child_point in this_point.children:
            if child_point.id not in self.processed_nodes:
                self.__parse_tree(this_point, child_point)

        logger.debug(f"Processed nodes are: {self.processed_nodes}")

    def __handle_soma(
        self,
        parent_point: SWCNode,
        this_point: SWCNode,
    ) -> None:
        """

        Handle the creation of soma segments based on different soma
        representation cases.  This method implements the soma representation
        guidelines as described in:

        "Soma format representation in NeuroMorpho.Org as of version 5.3".  For
        full details, see:
        https://github.com/NeuroML/Cvapp-NeuroMorpho.org/blob/master/caseExamples/SomaFormat-NMOv5.3.pdf

        In summary, NeuroMorpho makes the following conversions to standardise
        the SWC representation:
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

        This method handles the standardised NeuroMorpho SWC representation:


        1. Single point soma: a spherical segment is created

        2. Three point soma: two segments with the "middle" point in the center

        3. All other cases: multiple cylinders (as a cable)


        Note that this function only marks the current point as "processed"
        even if it does use other points to create the segments. This is
        because even if other points are part of the soma segments, they may
        still be the roots of subtrees where other segments are attached to
        them. So, they still need to be parsed by :py:func:`__parse_tree`
        recursively.

        :param parent_point: The parent point of the current soma point.
        :type parent_point: SWCNode
        :param this_point: The current soma point being processed.
        :type this_point: SWCNode
        """
        logger.debug(f"Handling soma point: {this_point.id}")

        assert self.cell

        if this_point.id in self.processed_nodes:
            logger.debug(f"Soma point {this_point.id} already processed, skipping")
            return

        if len(self.soma_points) == 1:
            logger.debug("Processing single-point soma")
            first_seg = self.cell.add_segment(
                prox=[
                    this_point.x,
                    this_point.y,
                    this_point.z,
                    2 * this_point.radius,
                ],
                dist=[
                    this_point.x,
                    this_point.y,
                    this_point.z,
                    2 * this_point.radius,
                ],
                seg_id=self.next_segment_id,
                name=f"soma_Seg_{self.next_segment_id}",
                parent=None,
                fraction_along=1.0,
                use_convention=True,
                reorder_segment_groups=False,
                optimise_segment_groups=False,
                seg_type="soma",
            )
            self.root_segment_id = first_seg.id
            self.point_indices_vs_seg_ids[this_point.id] = self.next_segment_id
            self.next_segment_id += 1

        elif len(self.soma_points) == 3:
            if this_point.id == self.soma_points[0].id:
                logger.debug("Processing 3-point soma: point 1")
                middle_point = self.soma_points[1]
                end_point = self.soma_points[2]

                first_seg = self.cell.add_segment(
                    prox=[
                        middle_point.x,
                        middle_point.y,
                        middle_point.z,
                        2 * middle_point.radius,
                    ],
                    dist=[
                        this_point.x,
                        this_point.y,
                        this_point.z,
                        2 * this_point.radius,
                    ],
                    seg_id=self.next_segment_id,
                    name=f"soma_Seg_{self.next_segment_id}",
                    parent=None,
                    fraction_along=1.0,
                    use_convention=True,
                    reorder_segment_groups=False,
                    optimise_segment_groups=False,
                    seg_type="soma",
                )
                logger.debug(
                    f"First segment: {first_seg} ({first_seg.proximal} -> {first_seg.distal})"
                )
                self.root_segment_id = first_seg.id

                self.point_indices_vs_seg_ids[this_point.id] = self.next_segment_id
                self.point_indices_vs_seg_ids[middle_point.id] = self.next_segment_id

                self.next_segment_id += 1

                second_seg = self.cell.add_segment(
                    prox=None,
                    dist=[
                        end_point.x,
                        end_point.y,
                        end_point.z,
                        2 * end_point.radius,
                    ],
                    seg_id=self.next_segment_id,
                    name=f"soma_Seg_{self.next_segment_id}",
                    parent=first_seg,
                    fraction_along=1.0,
                    use_convention=True,
                    reorder_segment_groups=False,
                    optimise_segment_groups=False,
                    seg_type="soma",
                )
                logger.debug(
                    f"Second segment: {second_seg} ({second_seg.proximal} -> {second_seg.distal})"
                )

                self.point_indices_vs_seg_ids[end_point.id] = self.next_segment_id

                self.next_segment_id += 1

            # ignore the other points when the method is called with them
            # because they have already been used in segment creation
            else:
                logger.debug("Processing (ignoring) 3-point soma: point 2/3")
                pass

        # all other cases
        else:
            logger.debug(
                f"Processing multi-point soma with {len(self.soma_points)} points"
            )

            if this_point == self.soma_points[0]:
                logger.debug("Processing multi-point soma")

                for i in range(len(self.soma_points) - 1):
                    segment = None
                    proximal_point = self.soma_points[i]
                    distal_point = self.soma_points[i + 1]

                    # first point, no parent, so set a proximal
                    if i == 0:
                        first_point = proximal_point
                        prox = [
                            first_point.x,
                            first_point.y,
                            first_point.z,
                            2 * first_point.radius,
                        ]

                        parent = None

                        # record the first point
                        self.point_indices_vs_seg_ids[first_point.id] = (
                            self.next_segment_id
                        )

                    # Not first point, don't set proximal at all, instead set
                    # the correct parent relationship
                    else:
                        prox = None
                        parent_id = distal_point.parent_id
                        parent_seg_id = self.point_indices_vs_seg_ids.get(
                            parent_id, None
                        )
                        parent = self.cell.get_segment(parent_seg_id)

                    distal = [
                        distal_point.x,
                        distal_point.y,
                        distal_point.z,
                        2 * distal_point.radius,
                    ]

                    segment = self.cell.add_segment(
                        prox=prox,
                        dist=distal,
                        seg_id=self.next_segment_id,
                        name=f"soma_Seg_{self.next_segment_id}",
                        parent=parent,
                        fraction_along=1.0,
                        use_convention=True,
                        reorder_segment_groups=False,
                        optimise_segment_groups=False,
                        seg_type="soma",
                    )

                    if i == 0:
                        self.root_segment_id = segment.id

                    self.point_indices_vs_seg_ids[distal_point.id] = (
                        self.next_segment_id
                    )

                    self.next_segment_id += 1
                self.point_indices_vs_seg_ids[self.soma_points[-1].id] = (
                    self.next_segment_id - 1
                )

            else:
                logger.debug(
                    f"Point {this_point} already processed as part of multi-point soma."
                )
                pass

        logger.debug(f"Finished handling soma point: {this_point.id}")

    def __create_segment(
        self,
        parent_point: SWCNode,
        this_point: SWCNode,
    ) -> None:
        """
        Create a NeuroML segment from an non-soma SWC point. Soma points are
        handled by py:meth:`__handle_soma`.


        Cases:

        #. somatic points are handled by py:func:`__handle_soma`.

           If there is no soma, we create the first segment as having both
           proximal and distal points as the first points.

           This is to replicate CVApp behaviour (but the logic is unclear to me
           at the time of writing this).

        #. if a point's parent is a soma point, but the point itself is not, we
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


        #. if the parent and child are of different types, but the parent is
           not of a soma type, treat it like any other segment (below: 3)

        #. create new segment for all other cases with current point as distal
           and the parent's distal assumed to be proximal (which does not need to
           be specified)


        :param parent_point: The parent point of the current point.
        :type parent_point: SWCNode
        :param this_point: The current point being processed.
        :type this_point: SWCNode
        """

        # cell cannot be None at this point
        assert self.cell

        # no point being processed here can be a soma
        logger.debug(
            f"Processing non-soma point segment: Point {this_point.id}, Type {this_point.type}, Parent {parent_point.id}"
        )
        seg_id = self.next_segment_id

        # get the segment type
        try:
            segment_type = self.section_types[this_point.type]
        except IndexError:
            segment_type = f"type_{this_point.type}"

        # is first point: only possible, once if there's no soma at all, since
        # this function only deals with non-soma points
        is_first_point = parent_point == this_point
        # is the point type changing?
        is_type_change = this_point.type != parent_point.type
        # is the parent a soma: special case
        is_parent_soma = parent_point.type == SWCNode.SOMA

        if this_point.type >= 5:
            logger.warning(
                f"Point is of type: {SWCNode.TYPE_NAMES[this_point.type]}, treating as dendrite"
            )
            seg_type = "dendrite"
        else:
            # "Apical Dendrite" -> "apical_dendrite" and so on
            seg_type = SWCNode.TYPE_NAMES[this_point.type].lower().replace(" ", "_")

        # if it's in the standard groups, do not add to another group
        if seg_type in ["axon", "dendrite", "soma"]:
            group_id = None
        else:
            group_id = seg_type

        logger.debug(f"Adding segment of type {seg_type} to group: {group_id}")

        # Case 1
        # first point, but is non-soma
        if is_first_point:
            logger.debug(f"First point and non-soma: {this_point}")
            self.cell.add_segment(
                prox=[this_point.x, this_point.y, this_point.z, 2 * this_point.radius],
                dist=[this_point.x, this_point.y, this_point.z, 2 * this_point.radius],
                seg_id=seg_id,
                name=f"{segment_type.replace(' ', '_')}_Seg_{seg_id}",
                parent=None,
                fraction_along=1.0,
                use_convention=True,
                reorder_segment_groups=False,
                optimise_segment_groups=False,
                seg_type="dendrite" if "dendrite" in seg_type else seg_type,
                group_id=group_id,
            )
            self.point_indices_vs_seg_ids[this_point.id] = seg_id

        else:
            # Case 2
            # Parent is soma, but point is not
            if is_parent_soma and is_type_change:
                logger.debug(f"Type change and parent is soma: {this_point}")

                # there must be a second point, otherwise it should error
                second_point = this_point.children[0]

                # parent segment
                parent = None
                if not is_first_point:
                    parent_seg_id = self.point_indices_vs_seg_ids.get(
                        parent_point.id, None
                    )

                    if parent_seg_id is not None:
                        parent = self.cell.get_segment(parent_seg_id)
                    else:
                        raise ValueError(f"Parent not found for {this_point}")

                self.cell.add_segment(
                    prox=[
                        this_point.x,
                        this_point.y,
                        this_point.z,
                        2 * this_point.radius,
                    ],
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
                    use_convention=True,
                    reorder_segment_groups=False,
                    optimise_segment_groups=False,
                    seg_type="dendrite" if "dendrite" in seg_type else seg_type,
                    group_id=group_id,
                )

                self.point_indices_vs_seg_ids[this_point.id] = seg_id
                self.point_indices_vs_seg_ids[second_point.id] = seg_id
                self.unprocessed_but_in_segment_nodes.add(second_point.id)

            # Cases 3, 4
            # All other cases ("normal" segment creation with parent as
            # proximal and current point as distal)
            else:
                # segment parent id
                parent_seg_id = self.point_indices_vs_seg_ids.get(parent_point.id, None)

                if parent_seg_id is not None:
                    parent = self.cell.get_segment(parent_seg_id)
                else:
                    raise ValueError(f"Parent not found for {this_point}")

                self.cell.add_segment(
                    prox=None,
                    dist=[
                        this_point.x,
                        this_point.y,
                        this_point.z,
                        2 * this_point.radius,
                    ],
                    seg_id=seg_id,
                    name=f"{segment_type.replace(' ', '_')}_Seg_{seg_id}",
                    parent=parent,
                    fraction_along=1.0,
                    use_convention=True,
                    reorder_segment_groups=False,
                    optimise_segment_groups=False,
                    seg_type="dendrite" if "dendrite" in seg_type else seg_type,
                    group_id=group_id,
                )
                self.point_indices_vs_seg_ids[this_point.id] = seg_id

        self.next_segment_id += 1

        logger.debug(f"Created segment {seg_id} for point {this_point.id}")

    def generate_neuroml(
        self, standalone_morphology: bool = True, unbranched_segment_groups: bool = True
    ) -> NeuroMLDocument:
        """Generate NeuroML representation.

        Main worker function

        :param standalone_morphology: export morphology as standalone object
            (not as part of a Cell object)
        :type standalone_morphology: bool
        :param unbranched_segment_groups: toggle creation of unbranched segment groups
        :type unbranched_segment_groups: bool
        :returns: the NeuroML document
        :rtype: NeuroMLDocument
        """
        if self.nml_doc is not None:
            return self.nml_doc

        start_time = time.time()
        logger.info("Starting NeuroML generation")
        if len(self.points) < 2:
            ValueError("SWC has fewer than two points. Cannot convert.")

        logger.info(f"Total points: {len(self.points)}")
        logger.debug(f"Total soma points: {len(self.soma_points)}")

        self.__create_cell()
        assert self.cell

        start_point = self.swc_graph.root
        assert start_point

        logger.debug(f"Start point: {start_point}")

        # create all the segments
        self.__parse_tree(start_point, start_point)

        parse_time = time.time()
        logger.info(f"Parsing SWC took {parse_time - start_time} seconds")

        if unbranched_segment_groups:
            # create unbranched segment groups
            if len(self.cell.morphology.segments) == 0:
                logger.warning(
                    "No segments were created. Skipping segment group creation."
                )
                return

            # if root segment id has not changed, we assume the first segment is
            # the root
            if self.root_segment_id == -1:
                self.root_segment_id = 0

            # Note that this adds a proximal point to the root segment of each
            # unbranched segment group. If a proximal point is not specified, it
            # will get one using `get_actual_proximal` and insert it into the
            # segment.
            self.cell.create_unbranched_segment_group_branches(
                self.root_segment_id,
                use_convention=True,
                reorder_segment_groups=True,
                optimise_segment_groups=True,
            )

            segment_group_time = time.time()
            logger.info(
                f"Creating unbranched segment groups took {segment_group_time - parse_time} seconds"
            )
        else:
            self.cell.reorder_segment_groups()
            self.cell.optimise_segment_groups()

        self.nml_doc = NeuroMLDocument(id=self.cell.id)

        if standalone_morphology:
            self.nml_doc.morphology.append(self.cell.morphology)
        else:
            self.nml_doc.cells.append(self.cell)

        end_time = time.time()
        logger.debug("NeuroML generation completed")
        logger.info(f"NeuroML generation took {end_time - start_time} seconds")

        return self.nml_doc

    def export_to_nml_file(
        self,
        filename: str,
        standalone_morphology: bool = True,
        unbranched_segment_groups: bool = True,
    ) -> None:
        """
        Export the NeuroML representation to a file.

        :param filename: The name of the file to export to.
        :type filename: str
        :param standalone_morphology: export morphology as standalone object
            (not as part of a Cell object)
        :type standalone_morphology: bool
        :param unbranched_segment_groups: toggle creation of unbranched segment groups
        :type unbranched_segment_groups: bool
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
    unbranched_segment_groups: bool = True,
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
        writer.export_to_nml_file(
            neuroml_file, standalone_morphology, unbranched_segment_groups
        )
    return writer.generate_neuroml(standalone_morphology, unbranched_segment_groups)


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
