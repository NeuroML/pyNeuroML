#!/usr/bin/env python3
"""
Utility functions to help build cells in NeuroML

File: CellBuilder.py

Copyright 2021 NeuroML contributors
Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com>
"""


from typing import List
from neuroml import (Cell, Morphology, MembraneProperties,  # noqa
                     IntracellularProperties, BiophysicalProperties, Segment,
                     SegmentGroup, Point3DWithDiam, SegmentParent, Member,
                     InitMembPotential, Resistivity, SpecificCapacitance,
                     NeuroMLDocument, IncludeType, ChannelDensity,
                     )
from pyneuroml.pynml import print_function


neuro_lex_ids = {
    'axon': "GO:0030424",
    'dend': "GO:0030425",
    'soma': "GO:0043025",
}


def create_cell(cell_id):
    # type: (str) -> Cell
    """Create a NeuroML Cell.

    Initialises the cell with these properties assigning IDs where applicable:
    - Morphology: "morphology"
    - BiophysicalProperties: "biophys"
    - MembraneProperties
    - IntracellularProperties
    - SegmentGroups: "all", "soma_group", "dendrite_group", "axon_group" which
      can be used to include all, soma, dendrite, and axon segments
      respectively.

    Note that since this cell does not currently include a segment in its
    morphology, it is *not* a valid NeuroML construct. Use the `add_segment`
    function to add segments. `add_segment` will also populate the default
    segment groups this creates.

    :param cell_id: id of the cell
    :type cell_id: str
    :returns: created cell object of type neuroml.Cell

    """
    cell = Cell(id=cell_id)
    cell.morphology = Morphology(id='morphology')
    membrane_properties = MembraneProperties()
    intracellular_properties = IntracellularProperties()

    cell.biophysical_properties = BiophysicalProperties(
        id="biophys", intracellular_properties=intracellular_properties,
        membrane_properties=membrane_properties)

    seg_group_all = SegmentGroup(id='all')
    seg_group_soma = SegmentGroup(id='soma_group',
                                  neuro_lex_id=neuro_lex_ids["soma"],
                                  notes="Default soma segment group for the cell")
    seg_group_axon = SegmentGroup(id='axon_group',
                                  neuro_lex_id=neuro_lex_ids["axon"],
                                  notes="Default axon segment group for the cell")
    seg_group_dend = SegmentGroup(id='dendrite_group',
                                  neuro_lex_id=neuro_lex_ids["dend"],
                                  notes="Default dendrite segment group for the cell")
    cell.morphology.segment_groups.append(seg_group_all)
    cell.morphology.segment_groups.append(seg_group_soma)
    cell.morphology.segment_groups.append(seg_group_axon)
    cell.morphology.segment_groups.append(seg_group_dend)

    return cell


def add_segment(cell, prox, dist, name=None, parent=None, fraction_along=1.0, group=None):
    # type: (Cell, List[float], List[float], str, SegmentParent, float, SegmentGroup) -> Segment
    """Add a segment to the cell.

    Convention: use axon_, soma_, dend_ prefixes for axon, soma, and dendrite
    segments respectivey. This will allow this function to add the correct
    neurolex IDs to the group.

    The created segment is also added to the default segment groups that were
    created by the `create_cell` function: "all", "dendrite_group",
    "soma_group", "axon_group" if the convention is followed.

    :param cell: cell to add segment to
    :type cell: Cell
    :param prox: proximal segment information
    :type prox: list with 4 float entries: [x, y, z, diameter]
    :param dist: dist segment information
    :type dist: list with 4 float entries: [x, y, z, diameter]
    :param name: name of segment
    :type name: str
    :param parent: parent segment
    :type parent: SegmentParent
    :param fraction_along: where the new segment is connected to the parent (0: distal point, 1: proximal point)
    :type fraction_along: float
    :param group: segment group to add the segment to
    :type group: SegmentGroup
    :returns: the created segment

    """
    try:
        if prox:
            p = Point3DWithDiam(x=prox[0], y=prox[1], z=prox[2], diameter=prox[3])
        else:
            p = None
    except IndexError as e:
        print_function("{}: prox must be a list of 4 elements".format(e))
    try:
        d = Point3DWithDiam(x=dist[0], y=dist[1], z=dist[2], diameter=dist[3])
    except IndexError as e:
        print_function("{}: dist must be a list of 4 elements".format(e))

    segid = len(cell.morphology.segments)

    sp = SegmentParent(segments=parent.id, fraction_along=fraction_along) if parent else None
    segment = Segment(id=segid, proximal=p, distal=d, parent=sp)

    if name:
        segment.name = name

    if group:
        seg_group = None
        seg_group = get_seg_group_by_id(group, cell)
        seg_group_all = get_seg_group_by_id("all", cell)
        seg_group_default = None
        neuro_lex_id = None

        if "axon_" in group:
            neuro_lex_id = neuro_lex_ids["axon"]  # See http://amigo.geneontology.org/amigo/term/GO:0030424
            seg_group_default = get_seg_group_by_id("axon_group", cell)
        if "soma_" in group:
            neuro_lex_id = neuro_lex_ids["soma"]
            seg_group_default = get_seg_group_by_id("soma_group", cell)
        if "dend_" in group:
            neuro_lex_id = neuro_lex_ids["dend"]
            seg_group_default = get_seg_group_by_id("dendrite_group", cell)

        if seg_group is None:
            seg_group = SegmentGroup(id=group, neuro_lex_id=neuro_lex_id)
            cell.morphology.segment_groups.append(seg_group)

        seg_group.members.append(Member(segments=segment.id))
        if seg_group_default:
            seg_group_default.members.append(Member(segments=segment.id))

    seg_group_all.members.append(Member(segments=segment.id))

    cell.morphology.segments.append(segment)
    return segment


def set_init_memb_potential(cell, v, group="all"):
    # type (Cell, str, str)
    """Set the initial membrane potential of the cell.

    :param cell: cell to modify
    :type cell: Cell
    :param v: value to set for membrane potential with units
    :type v: str
    :param group: id of segment group to modify
    :type group: str
    """
    cell.biophysical_properties.membrane_properties.init_memb_potentials = \
        [InitMembPotential(value=v, segment_groups=group)]


def set_resistivity(cell, resistivity, group="all"):
    # type (Cell, str, str)
    """Set the resistivity of the cell

    :param cell: cell to modfify
    :param resistivity: value resistivity to set with units
    :type resistivity: str
    :param group: segment group to modify
    :type group: str
    """
    cell.biophysical_properties.intracellular_properties.resistivities = [Resistivity(value=resistivity, segment_groups=group)]


def set_specific_capacitance(cell, spec_cap, group="all"):
    # type (Cell, str, str)
    """Set the specific capacitance for the cell.

    :param cell: cell to set specific capacitance for
    :type cell: Cell
    :param spec_cap: value of specific capacitance with units
    :type spec_cap: str
    :param group: segment group to modify
    :type group: str
    """
    cell.biophysical_properties.membrane_properties.specific_capacitances.append(SpecificCapacitance(value=spec_cap, segment_groups=group))


def add_channel_density(cell, nml_cell_doc, cd_id, cond_density, ion_channel, ion_chan_def_file="", erev="0.0 mV", ion="non_specific", group="all"):
    # type (Cell, NeuroMLDocument, str, str, str, str, str, str, str)
    """Add channel density.

    :param cell: cell to be modified
    :type cell: Cell
    :param nml_cell_doc: cell NeuroML document to which channel density is to be added
    :type nml_cell_doc: NeuroMLDocument
    :param cd_id: id for channel density
    :type cd_id: str
    :param cond_density: value of conductance density with units
    :type cond_density: str
    :param ion_channel: name of ion channel
    :type ion_channel: str
    :param ion_chan_def_file: path to NeuroML2 file defining the ion channel, if empty, it assumes the channel is defined in the same file
    :type ion_chan_def_file: str
    :param erev: value of reversal potential with units
    :type erev: str
    :param ion: name of ion
    :type ion: str
    :param group: segment groups to add to
    :type group: str
    """
    cd = ChannelDensity(id=cd_id,
                        segment_groups=group,
                        ion=ion,
                        ion_channel=ion_channel,
                        erev=erev,
                        cond_density=cond_density)

    cell.biophysical_properties.membrane_properties.channel_densities.append(cd)

    if len(ion_chan_def_file) > 0:
        if IncludeType(ion_chan_def_file) not in nml_cell_doc.includes:
            nml_cell_doc.includes.append(IncludeType(ion_chan_def_file))


def get_seg_group_by_id(sg_id, cell):
    # (str, Cell) -> SegmentGroup
    """Return the SegmentGroup object for the specified segment group id.

    :param sg_id: id of segment group to find
    :type sg_id: str
    :param cell: cell to look for segment group in
    :type cell: Cell
    :returns: SegmentGroup object of specified ID or None if not found

    """
    if not sg_id or not cell:
        print_function("Please specify both a segment group id and a Cell")
        return None

    for sg in cell.morphology.segment_groups:
        if sg.id == sg_id:
            return sg

    return None


def get_seg_group_by_id_substring(sg_id_substring, cell):
    """Return segment groups that include the specified substring.

    :param sg_id_substring: substring to match
    :type sg_id_substring: str
    :param cell: cell to look for segment group in
    :type cell: Cell
    :returns: list of SegmentGroups whose IDs include the given substring

    """
    sg_group_list = []
    if not sg_id_substring or not cell:
        print_function("Please specify both a segment group id and a Cell")
        return None
    for sg in cell.morphology.segment_groups:
        if sg_id_substring in sg.id:
            sg_group_list.append(sg)
    return sg_group_list
