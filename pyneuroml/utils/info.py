#!/usr/bin/env python3
"""
Utilities for getting information from NeuroML models

File: pyneuroml/utils/info.py

Copyright 2024 NeuroML contributors
"""

import inspect
import logging
import sys
import textwrap
import typing

from neuroml import Cell, NeuroMLDocument
from pyneuroml.io import read_neuroml2_file
from pyneuroml.utils.units import convert_to_units, get_value_in_si

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def quick_summary(nml2_doc: NeuroMLDocument) -> str:
    """Get a quick summary of the NeuroML2 document

    NOTE: You should prefer nml2_doc.summary(show_includes=False)

    :param nml2_doc: NeuroMLDocument to fetch summary for
    :type nml2_doc: NeuroMLDocument
    :returns: summary string
    """
    info = "Contents of NeuroML 2 document: {}\n".format(nml2_doc.id)
    membs = inspect.getmembers(nml2_doc)

    for memb in membs:
        if isinstance(memb[1], list) and len(memb[1]) > 0 and not memb[0].endswith("_"):
            info += "  {}:\n    [".format(memb[0])
            for entry in memb[1]:
                extra = "???"
                extra = entry.name if hasattr(entry, "name") else extra
                extra = entry.href if hasattr(entry, "href") else extra
                extra = entry.id if hasattr(entry, "id") else extra

                info += " {} ({}),".format(entry, extra)

            info += "]\n"
    return info


def summary(
    nml2_doc: typing.Optional[NeuroMLDocument] = None, verbose: bool = False
) -> None:
    """Wrapper around nml_doc.summary() to generate the pynml-summary command
    line tool.

    :param nml2_doc: NeuroMLDocument object or name of NeuroML v2 file to get summary for.
    :type nml2_doc: NeuroMLDocument
    :param verbose: toggle verbosity
    :type verbose: bool
    """

    usage = textwrap.dedent(
        """
        Usage:

        pynml-summary <NeuroML file> [-vh]

        Required arguments:
            NeuroML file: name of file to summarise

        Optional arguments:

            -v/--verbose:  enable verbose mode
            -h/--help:  print this help text and exit
        """
    )

    if len(sys.argv) < 2:
        print("Argument required.")
        print(usage)
        return

    if "-h" in sys.argv or "--help" in sys.argv:
        print(usage)
        return

    if "-v" in sys.argv or "--verbose" in sys.argv:
        verbose = True
        sys.argv.remove("-v")

    if nml2_doc is None:
        nml2_file_name = sys.argv[1]
        nml2_doc = read_neuroml2_file(nml2_file_name, include_includes=verbose, fix_external_morphs_biophys=True)

    info = nml2_doc.summary(show_includes=False)

    if verbose:
        cell_info_str = ""
        for cell in nml2_doc.cells:
            cell_info_str += cell_info(cell) + "*\n"
        lines = info.split("\n")
        info = ""
        still_to_add = False
        for line in lines:
            if "Cell: " in line:
                still_to_add = True
                pass
            elif "Network: " in line:
                still_to_add = False
                if len(cell_info_str) > 0:
                    info += "%s" % cell_info_str
                info += "%s\n" % line
            else:
                if still_to_add and "******" in line:
                    if len(cell_info_str) > 0:
                        info += "%s" % cell_info_str
                info += "%s\n" % line
    print(info)


def cells_info(nml_file_name: str) -> str:
    """Provide information about the cells in a NeuroML file.

    :param nml_file_name: name of NeuroML v2 file
    :type nml_file_name: str
    :returns: information on cells (str)
    """
    from neuroml.loaders import read_neuroml2_file

    nml_doc = read_neuroml2_file(
        nml_file_name, include_includes=True, verbose=False, optimized=True
    )

    info = ""
    info += "Extracting information on %i cells in %s" % (
        len(nml_doc.cells),
        nml_file_name,
    )

    for cell in nml_doc.cells:
        info += cell_info(cell)
    return info


def cell_info(cell: Cell) -> str:
    """Provide information on a NeuroML Cell instance:

    - morphological information:

      - Segment information:

        - parent segments
        - segment location, extents, diameter
        - segment length
        - segment surface area
        - segment volume

      - Segment group information:

        - included segments

    - biophysical properties:

      - channel densities
      - specific capacitances

    :param cell: cell object to investigate
    :type cell: Cell
    :returns: string of cell information
    """
    info = ""
    prefix = "*  "
    info += prefix + "Cell: %s\n" % cell.id
    tot_length = 0
    tot_area = 0
    for seg in cell.morphology.segments:
        info += prefix + "  %s\n" % seg
        dist = seg.distal
        prox = seg.proximal
        parent_id = seg.parent.segments if seg.parent else "None (root segment)"
        length = cell.get_segment_length(seg.id)
        info += prefix + "    Parent segment: %s\n" % (parent_id)
        info += prefix + "    %s -> %s; seg length: %s um\n" % (prox, dist, length)

        tot_length += length
        area = cell.get_segment_surface_area(seg.id)
        volume = cell.get_segment_volume(seg.id)
        tot_area += area
        info += prefix + "    Surface area: %s um2, volume: %s um3\n" % (area, volume)
    numseg = len(cell.morphology.segments)
    info += prefix + "  Total length of %i segment%s: %s um; total area: %s um2\n" % (
        numseg,
        "s" if numseg > 1 else "",
        tot_length,
        tot_area,
    )

    info += prefix + "\n"

    for sg in cell.morphology.segment_groups:
        segs = cell.get_all_segments_in_group(sg.id)
        info += prefix + "  %s;\tcontains %i segment%s\n" % (
            str(sg).replace(", ", ",\t"),
            len(segs),
            ", id: %s" % segs[0] if len(segs) == 1 else "s in total",
        )

    if len(cell.morphology.segment_groups) > 0:
        info += prefix + "\n"

    seg_info = cell.get_segment_ids_vs_segments()
    if cell.biophysical_properties:
        for cd in cell.biophysical_properties.membrane_properties.channel_densities:
            # print dir(cd)
            group = cd.segment_groups if cd.segment_groups else "all"
            info += (
                prefix
                + "  Channel density: %s on %s;\tconductance of %s through ion chan %s with ion %s, erev: %s\n"
                % (cd.id, group, cd.cond_density, cd.ion_channel, cd.ion, cd.erev)
            )
            segs = cell.get_all_segments_in_group(group)
            for seg_id in segs:
                seg = seg_info[seg_id]

                cond_dens_si = get_value_in_si(cd.cond_density)
                surface_area_si = get_value_in_si(
                    "%s um2" % cell.get_segment_surface_area(seg_id)
                )
                cond_si = cond_dens_si * surface_area_si
                cond_pS = convert_to_units("%sS" % cond_si, "pS")
                info += (
                    prefix
                    + "    Channel is on %s,\ttotal conductance: %s S_per_m2 x %s m2 = %s S (%s pS)\n"
                    % (seg, cond_dens_si, surface_area_si, cond_si, cond_pS)
                )

        if len(cell.biophysical_properties.membrane_properties.channel_densities) > 0:
            info += prefix + "\n"

        for sc in cell.biophysical_properties.membrane_properties.specific_capacitances:
            group = sc.segment_groups if sc.segment_groups else "all"
            info += prefix + "  Specific capacitance on %s: %s\n" % (group, sc.value)
            segs = cell.get_all_segments_in_group(group)
            for seg_id in segs:
                seg = seg_info[seg_id]
                spec_cap_si = get_value_in_si(sc.value)
                surface_area_si = get_value_in_si(
                    "%s um2" % cell.get_segment_surface_area(seg_id)
                )
                cap_si = spec_cap_si * surface_area_si
                cap_pF = convert_to_units("%sF" % cap_si, "pF")
                info += (
                    prefix
                    + "    Capacitance of %s,\ttotal capacitance: %s F_per_m2 x %s m2 = %s F (%s pF)\n"
                    % (seg, spec_cap_si, surface_area_si, cap_si, cap_pF)
                )

    return info
