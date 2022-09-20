#!/usr/bin/env python3
"""
Utility functions to help build cells in NeuroML
"""


from typing import List, Union, Any, Optional
import neuroml
from neuroml.utils import component_factory

neuro_lex_ids = {
    "axon": "GO:0030424",
    "dend": "GO:0030425",
    "soma": "GO:0043025",
}


def create_cell(cell_id: str, use_convention: bool = True) -> neuroml.Cell:
    """Create a NeuroML Cell.

    Initialises the cell with these properties assigning IDs where applicable:

    - Morphology: "morphology"
    - BiophysicalProperties: "biophys"
    - MembraneProperties
    - IntracellularProperties

    if `use_convention` is True, it also creates some default SegmentGroups for
    convenience:

    - "all", "soma_group", "dendrite_group", "axon_group" which
      are used by other helper functions to include all, soma, dendrite, and
      axon segments respectively.

    Note that since this cell does not currently include a segment in its
    morphology, it is *not* a valid NeuroML construct. Use the `add_segment`
    function to add segments. `add_segment` will also populate the default
    segment groups this creates.

    :param cell_id: id of the cell
    :type cell_id: str
    :param use_convention: whether helper segment groups should be created using the default convention
    :type use_convention: bool
    :returns: created cell object of type neuroml.Cell

    """
    cell = component_factory("Cell", id=cell_id)
    # do not validate yet, because segments are required
    cell.add("Morphology", id="morphology", validate=False)

    membrane_properties = component_factory("MembraneProperties")
    intracellular_properties = component_factory("IntracellularProperties")

    cell.biophysical_properties = component_factory(
        "BiophysicalProperties",
        id="biophys",
        intracellular_properties=intracellular_properties,
        membrane_properties=membrane_properties,
    )

    if use_convention:
        seg_group_all = component_factory("SegmentGroup", id="all")
        seg_group_soma = component_factory(
            "SegmentGroup",
            id="soma_group",
            neuro_lex_id=neuro_lex_ids["soma"],
            notes="Default soma segment group for the cell",
        )
        seg_group_axon = component_factory(
            "SegmentGroup",
            id="axon_group",
            neuro_lex_id=neuro_lex_ids["axon"],
            notes="Default axon segment group for the cell",
        )
        seg_group_dend = component_factory(
            "SegmentGroup",
            id="dendrite_group",
            neuro_lex_id=neuro_lex_ids["dend"],
            notes="Default dendrite segment group for the cell",
        )
        # skip validation: segments etc needed, cell is invalid
        cell.morphology.add(seg_group_all, validate=False)
        cell.morphology.add(seg_group_soma, validate=False)
        cell.morphology.add(seg_group_axon, validate=False)
        cell.morphology.add(seg_group_dend, validate=False)

    return cell


def add_segment(
    cell: neuroml.Cell,
    prox: List[float],
    dist: List[float],
    name: str = None,
    parent: neuroml.SegmentParent = None,
    fraction_along: float = 1.0,
    group: neuroml.SegmentGroup = None,
    use_convention: bool = True,
) -> neuroml.Segment:
    """Add a segment to the cell.

    Suggested convention: use `axon_`, `soma_`, `dend_` prefixes for axon,
    soma, and dendrite segments respectivey. This will allow this function to
    add the correct neurolex IDs to the group.

    If `use_convention` is true, the created segment is also added to the
    default segment groups that were created by the `create_cell` function:
    `all`, `dendrite_group`, `soma_group`, `axon_group`. Note that while it is
    not necessary to use the convention, it is necessary to be consistent.

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
    :param use_convention: whether helper segment groups should be created using the default convention
    :type use_convention: bool
    :returns: the created segment

    """
    try:
        if prox:
            p = component_factory(
                "Point3DWithDiam", x=prox[0], y=prox[1], z=prox[2], diameter=prox[3]
            )
        else:
            p = None
    except IndexError as e:
        print("{}: prox must be a list of 4 elements".format(e))
    try:
        d = component_factory(
            "Point3DWithDiam", x=dist[0], y=dist[1], z=dist[2], diameter=dist[3]
        )
    except IndexError as e:
        print("{}: dist must be a list of 4 elements".format(e))

    segid = len(cell.morphology.segments)

    if segid > 0 and parent is None:
        raise Exception(
            "There are currently more than one segments in the cell, but one is being added without specifying a parent segment"
        )

    sp = (
        component_factory(
            "SegmentParent", segments=parent.id, fraction_along=fraction_along
        )
        if parent
        else None
    )
    segment = component_factory("Segment", id=segid, proximal=p, distal=d, parent=sp)

    if name:
        segment.name = name

    if group:
        seg_group = None
        seg_group_default = None
        neuro_lex_id = None

        # cell.get_segment_group throws an exception of the segment group
        # does not exist
        try:
            seg_group = cell.get_segment_group(group)
        except Exception as e:
            print("Warning: {}".format(e))

        if "axon_" in group:
            neuro_lex_id = neuro_lex_ids[
                "axon"
            ]  # See http://amigo.geneontology.org/amigo/term/GO:0030424
            if use_convention:
                seg_group_default = cell.get_segment_group("axon_group")
        if "soma_" in group:
            neuro_lex_id = neuro_lex_ids["soma"]
            if use_convention:
                seg_group_default = cell.get_segment_group("soma_group")
        if "dend_" in group:
            neuro_lex_id = neuro_lex_ids["dend"]
            if use_convention:
                seg_group_default = cell.get_segment_group("dendrite_group")

        if seg_group is None:
            seg_group = component_factory(
                "SegmentGroup", id=group, neuro_lex_id=neuro_lex_id
            )
            cell.morphology.add(seg_group, validate=False)

        seg_group.add(component_factory("Member", segments=segment.id))
        # Ideally, these higher level segment groups should just include other
        # segment groups using Include, which would result in smaller NML
        # files. However, because these default segment groups are defined
        # first, they are printed in the NML file before the new segments and their
        # groups. The jnml validator does not like this.
        # TODO: clarify if the order of definition is important, or if the jnml
        # validator needs to be updated to manage this use case.
        if use_convention and seg_group_default:
            seg_group_default.add(component_factory("Member", segments=segment.id))

    if use_convention:
        seg_group_all = cell.get_segment_group("all")
        seg_group_all.add(component_factory("Member", segments=segment.id))

    cell.morphology.add(segment)
    return segment


def set_init_memb_potential(cell: neuroml.Cell, v: str, group: str = "all") -> None:
    """Set the initial membrane potential of the cell.

    :param cell: cell to modify
    :type cell: Cell
    :param v: value to set for membrane potential with units
    :type v: str
    :param group: id of segment group to modify
    :type group: str
    """
    cell.biophysical_properties.membrane_properties.add(
        "InitMembPotential", value=v, segment_groups=group
    )


def set_resistivity(cell: neuroml.Cell, resistivity: str, group: str = "all") -> None:
    """Set the resistivity of the cell

    :param cell: cell to modfify
    :param resistivity: value resistivity to set with units
    :type resistivity: str
    :param group: segment group to modify
    :type group: str
    """
    cell.biophysical_properties.intracellular_properties.add(
        "Resistivity", value=resistivity, segment_groups=group
    )


def set_specific_capacitance(
    cell: neuroml.Cell, spec_cap: str, group: str = "all"
) -> None:
    """Set the specific capacitance for the cell.

    :param cell: cell to set specific capacitance for
    :type cell: Cell
    :param spec_cap: value of specific capacitance with units
    :type spec_cap: str
    :param group: segment group to modify
    :type group: str
    """
    cell.biophysical_properties.membrane_properties.add(
        "SpecificCapacitance", value=spec_cap, segment_groups=group
    )


def add_intracellular_property(
    property_name: str, cell: neuroml.Cell, **kwargs: Any
) -> None:
    """Generic function to add an intracellular property to the cell.

    For a full list of membrane properties, see:
    https://docs.neuroml.org/Userdocs/Schemas/Cells.html?#intracellularproperties

    :param property_name: name of intracellular property to add
    :type property_name: str
    :param cell: cell to be modified
    :type cell: Cell
    :param kwargs: named arguments for intracellular property to be added
    :type kwargs: Any
    :returns: None

    """
    cell.biophysical_properties.intracellular_properties.add(property_name, **kwargs)


def add_membrane_property(
    property_name: str, cell: neuroml.Cell, **kwargs: Any
) -> None:
    """Generic function to add a membrane property to the cell.

    For a full list of membrane properties, see:
    https://docs.neuroml.org/Userdocs/Schemas/Cells.html?#membraneproperties

    Please also see specific functions in this module, which are designed to be
    easier to use than this generic function.

    :param property_name: name of membrane to add
    :type property_name: str
    :param cell: cell to be modified
    :type cell: Cell
    :param kwargs: named arguments for membrane property to be added
    :type kwargs: Any
    :returns: None

    """
    cell.biophysical_properties.membrane_properties.add(property_name, **kwargs)


def add_channel_density_v(
    channel_density_type: str,
    cell: neuroml.Cell,
    nml_cell_doc: neuroml.NeuroMLDocument,
    ion_chan_def_file: str = "",
    **kwargs: Any
) -> None:
    """Generic function to add channel density components to a Cell.

    :param channel_density_type: type of channel density to add.
        See https://docs.neuroml.org/Userdocs/Schemas/Cells.html for the
        complete list.
    :type channel_density_type: str
    :param cell: cell to be modified
    :type cell: Cell
    :param nml_cell_doc: cell NeuroML document to which channel density is to be added
    :type nml_cell_doc: NeuroMLDocument
    :param ion_chan_def_file: path to NeuroML2 file defining the ion channel, if empty, it assumes the channel is defined in the same file
    :type ion_chan_def_file: str
    :param kwargs: named arguments for required channel density type
    :type kwargs: Any
    :returns: None
    """

    add_membrane_property(channel_density_type, cell, **kwargs)

    if len(ion_chan_def_file) > 0:
        if (
            component_factory("IncludeType", ion_chan_def_file)
            not in nml_cell_doc.includes
        ):
            nml_cell_doc.add("IncludeType", ion_chan_def_file)


def add_channel_density(
    cell: neuroml.Cell,
    nml_cell_doc: neuroml.NeuroMLDocument,
    cd_id: str,
    ion_channel: str,
    cond_density: str,
    erev: str = "0.0 mV",
    group: str = "all",
    ion: str = "non_specific",
    ion_chan_def_file: str = "",
) -> None:
    """Add channel density.

    :param cell: cell to be modified
    :type cell: Cell
    :param nml_cell_doc: cell NeuroML document to which channel density is to be added
    :type nml_cell_doc: NeuroMLDocument
    :param cd_id: id for channel density
    :type cd_id: str
    :param ion_channel: name of ion channel
    :type ion_channel: str
    :param cond_density: value of conductance density with units
    :type cond_density: str
    :param erev: value of reversal potential with units
    :type erev: str
    :param group: segment groups to add to
    :type group: str
    :param ion: name of ion
    :type ion: str
    :param ion_chan_def_file: path to NeuroML2 file defining the ion channel, if empty, it assumes the channel is defined in the same file
    :type ion_chan_def_file: str
    """
    cd = cell.biophysical_properties.membrane_properties.add(
        "ChannelDensity",
        id=cd_id,
        segment_groups=group,
        ion=ion,
        ion_channel=ion_channel,
        erev=erev,
        cond_density=cond_density,
    )

    if len(ion_chan_def_file) > 0:
        if (
            component_factory("IncludeType", ion_chan_def_file)
            not in nml_cell_doc.includes
        ):
            nml_cell_doc.add("IncludeType", ion_chan_def_file)
