"""
Utilities required by the NEURON -> NeuroML exporter.

When changing this file, please ensure that `mview_neuroml2.hoc` is also
updated accordingly.

"""

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    from neuron import h
    from nrn import *
except ImportError:
    logger.warning("Please install optional dependencies to use NEURON features:")
    logger.warning("pip install pyneuroml[neuron]")


def clear_neuron() -> None:
    """Clear NEURON contents."""
    print(" - Clearing NEURON contents...")
    h("forall delete_section()")
    print(" - Cleared NEURON contents...")
    h("topology()")


def replace_brackets(ref: str) -> str:
    """Replace square brackets with underscores"""
    return ref.replace("[", "_").replace("]", "")


def get_cell_name(nrn_section_name: str, cell_index: int = 0) -> str:
    # print("Getting cell name for %s"%nrn_section_name)
    """Return the cell name for a NEURON section

    :param nrn_section_name: name of NEURON section
    :type nrn_section_name: str
    :param cell_index: index of cell
    :type cell_index: int

    :returns: generated cell name
    """
    if "." not in nrn_section_name:
        return "Cell%i" % cell_index
    else:
        return "%s_%i" % (replace_brackets(nrn_section_name.split(".")[0]), cell_index)


def get_cell_file_dir(network_file_name: str) -> str:
    if "/" not in network_file_name:
        return "."
    return network_file_name[: network_file_name.rfind("/")]


def get_segment_group_name(nrn_section_name: str) -> str:
    """Get the name of the segment group from a NEURON section name

    :param nrn_section_name: NEURON section name
    :type nrn_section_name: str

    :returns: name of segment group
    """
    # print("Getting segment group name for %s"%nrn_section_name)
    if "." not in nrn_section_name:
        return replace_brackets(nrn_section_name)
    else:
        return replace_brackets(nrn_section_name.split(".")[1])


mechs_vs_erevs = {}


def set_erev_for_mechanism(mech: str, erev: float) -> None:
    """Set the reversal potential for provided mechanism

    :param mech: mechanism
    :type mech: str
    :param erev: reversal potential value
    :type erev: float
    """
    mechs_vs_erevs[mech] = erev
    print(">> mechs_vs_erevs: %s" % mechs_vs_erevs)


def get_erev_for_mechanism(mech: str) -> float:
    """Get reversal potential for mechanism

    :param mech: mechanism to return reversal potential for
    :type mech: str

    :returns: reversal potential
    """
    # TODO: check if `mech` exists in the dict?
    print(">> mechs_vs_erevs: %s" % mechs_vs_erevs)
    return mechs_vs_erevs[mech]


if __name__ == "__main__":
    tests = ["Soma", "dend[2]", "Mitral[1].secden[8]"]

    for test in tests:
        print(
            "Orig: %s; cell name: %s, segment group name: %s"
            % (test, get_cell_name(test), get_segment_group_name(test))
        )
