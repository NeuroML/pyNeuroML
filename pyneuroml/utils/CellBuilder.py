#!/usr/bin/env python3
"""
Utility functions to help build cells in NeuroML

File: CellBuilder.py

Copyright 2021 NeuroML contributors
Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com>
"""


from neuroml import (Cell, Morphology, MembraneProperties,
                     IntracellularProperties, BiophysicalProperties, Segment,
                     SegmentGroup, Point3DWithDiam, SegmentParent, Member,
                     InitMembPotential, Resistivity, SpecificCapacitance,
                     NeuroMLDocument, IncludeType, ChannelDensity,
                     )
from pyneuroml.pynml import print_function


def create_cell(cell_id: str) -> Cell:
    """Create a NeuroML Cell.

    Initialises the cell with these properties assigning IDs where applicable:
    - Morphology: "morphology"
    - BiophysicalProperties: "biophys"
    - MembraneProperties
    - IntracellularProperties
    - SegmentGroup: "all"

    Note that since this cell does not currently include a segment in its
    morphology, it is *not* a valid NeuroML construct. Use the `add_segment`
    function to add segments.

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
    cell.morphology.segment_groups.append(seg_group_all)

    return cell


def add_segment(cell: Cell, prox: list[float], dist: list[float], name:
                str = None, parent: SegmentParent = None, group: SegmentGroup = None) -> Segment:
    """TODO: Docstring for add_segment.

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
    :param group: segment group to add the segment to
    :type group: SegmentGroup
    :returns: the created segment

    """
    try:
        p = Point3DWithDiam(x=prox[0], y=prox[1], z=prox[2], diameter=prox[3])
    except IndexError as e:
        print_function(f"{e}: prox must be a list of 4 elements")
    try:
        d = Point3DWithDiam(x=dist[0], y=dist[1], z=dist[2], diameter=dist[3])
    except IndexError as e:
        print_function(f"{e}: dist must be a list of 4 elements")

    segid = len(cell.morphology.segments)

    sp = SegmentParent(segments=parent.id) if parent else None
    segment = Segment(id=segid, proximal=p, distal=d, parent=sp)

    if name:
        segment.name = name

    if group:
        seg_group = None
        for sg in cell.morphology.segment_groups:
            if sg.id == group:
                seg_group = sg
            if sg.id == 'all':
                seg_group_all = sg

        if seg_group is None:
            neuro_lex_id = None
            if group == "axon_group":
                neuro_lex_id = "GO:0030424"  # See http://amigo.geneontology.org/amigo/term/GO:0030424
            if group == "soma_group":
                neuro_lex_id = "GO:0043025"
            if group == "dendrite_group":
                neuro_lex_id = "GO:0030425"

            seg_group = SegmentGroup(id=group, neuro_lex_id=neuro_lex_id)
            cell.morphology.segment_groups.append(seg_group)

        seg_group.members.append(Member(segments=segment.id))

    seg_group_all.members.append(Member(segments=segment.id))

    cell.morphology.segments.append(segment)
    return segment


def set_init_memb_potential(cell: Cell, v: str, group: str = "all"):
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


def set_resistivity(cell: Cell, resistivity: str, group: str = "all"):
    """Set the resistivity of the cell

    :param cell: cell to modfify
    :param resistivity: value resistivity to set with units
    :type resistivity: str
    :param group: segment group to modify
    :type group: str
    :returns: TODO

    """
    cell.biophysical_properties.intracellular_properties.resistivities = [Resistivity(value=resistivity, segment_groups=group)]


def set_specific_capacitance(cell: Cell, spec_cap: str, group: str = "all"):
    """Set the specific capacitance for the cell.

    :param cell: cell to set specific capacitance for
    :type cell: Cell
    :param spec_cap: value of specific capacitance with units
    :type spec_cap: str
    :param group: segment group to modify
    :type group: str
    """
    cell.biophysical_properties.membrane_properties.specific_capacitances.append(SpecificCapacitance(value=spec_cap, segment_groups=group))


def add_channel_density(cell: Cell, nml_cell_doc: NeuroMLDocument, cd_id: str,
                        cond_density: str, ion_channel: str, ion_chan_def_file:
                        str = "", erev: str = "0.0 mV", ion: str = "non_specific", group: str =
                        "all"):
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
        nml_cell_doc.includes.append(IncludeType(ion_chan_def_file))
