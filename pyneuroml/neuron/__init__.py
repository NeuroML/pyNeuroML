"""

A package of utilities for exporting NEURON models to NeuroML 2 & for analysing/comparing NEURON models to NeuroML versions

Will use some some utilities from https://github.com/OpenSourceBrain/NEURONShowcase

"""

import json
import logging
import math
import os
import pathlib
import pprint
import typing
import warnings

import airspeed
import yaml

from pyneuroml.pynml import validate_neuroml1, validate_neuroml2

pp = pprint.PrettyPrinter(depth=4)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    from neuron import h

    from pyneuroml.neuron.nrn_export_utils import set_erev_for_mechanism
except ImportError:
    logger.warning("Please install optional dependencies to use NEURON features:")
    logger.warning("pip install pyneuroml[neuron]")


def get_utils_hoc() -> pathlib.Path:
    """Get full path of utils.hoc file

    :returns: pathlib.Path object for utils.hoc file

    """
    cwd = pathlib.Path(__file__).parent
    utils_hoc = cwd / pathlib.Path("utils.hoc")
    return utils_hoc


def export_to_neuroml2(
    hoc_or_python_file: str,
    nml2_file_name: str,
    includeBiophysicalProperties: bool = True,
    separateCellFiles: bool = False,
    known_rev_potentials: dict = {},
    validate: bool = True,
) -> None:
    """Export NEURON hoc morphology files to NeuroML2 format.

    Please note that the conversion of NEURON Python scripts is not yet
    implemented.

    :param hoc_or_python_file: NEURON hoc or Python file to convert
    :type hoc_or_python_file: str
    :param nml2_file_name: name of NeuroML2 file to save to
    :type nml2_file_name: str
    :param includeBiophysicalProperties: whether or not to include biophysical properties in the conversion
    :type includeBiophysicalProperties: bool
    :param separateCellFiles: whether cells should be exported to individual files
    :type separateCellFiles:
    :param known_rev_potentials: known reversal potentials
    :type known_rev_potentials: dict with ions as keys, and their reveral potentials
    :param validate: whether the generated files should be validated
    :type validate: bool
    """
    if hoc_or_python_file is not None:
        load_hoc_or_python_file(hoc_or_python_file)
    else:
        logger.info(
            "hoc_or_python_file variable is None; exporting what's currently in memory..."
        )

    for ion in known_rev_potentials.keys():
        set_erev_for_mechanism(ion, known_rev_potentials[ion])

    h.load_file("mview.hoc")

    h("objref mv")
    h("mv = new ModelView(0)")

    h.load_file("%s/mview_neuroml2.hoc" % (os.path.dirname(__file__)))

    h("objref mvnml")
    h("mvnml = new ModelViewNeuroML2(mv)")

    nml2_level = 2 if includeBiophysicalProperties else 1

    h.mvnml.exportNeuroML2(nml2_file_name, nml2_level, int(separateCellFiles))

    if validate:
        validate_neuroml2(nml2_file_name)

    h("mv.destroy()")


def export_to_neuroml1(hoc_file, nml1_file_name, level=1, validate=True):
    """Export to NeuroML1.

    NOTE: NeuroML1 is deprecated and supporting functions will be removed in a
    future release. Please use NeuroML2.
    """
    logger.info("NOTE: NeuroMLv1 is deprecated. Please use NeuroMLv2.")
    warnings.warn(
        "Please note that NeuroMLv1 is deprecated. Functions supporting NeuroMLv1 will be removed in the future.  Please use NeuroMLv2.",
        FutureWarning,
        stacklevel=2,
    )

    if not (level == 1 or level == 2):
        logger.info("Only options for Levels in NeuroMLv1.8.1 are 1 or 2")
        return None

    h.load_file(hoc_file)

    logger.info("Loaded NEURON file: %s" % hoc_file)

    h.load_file("mview.hoc")

    h("objref mv")
    h("mv = new ModelView()")

    h.load_file("%s/mview_neuroml1.hoc" % (os.path.dirname(__file__)))

    h("objref mvnml1")
    h("mvnml1 = new ModelViewNeuroML1(mv)")

    h.mvnml1.exportNeuroML(nml1_file_name, level)

    if validate:
        validate_neuroml1(nml1_file_name)


def load_hoc_or_python_file(hoc_or_python_file: str) -> bool:
    """Load a NEURON hoc file or Python script.

    Note: loading Python scripts is not yet supported.

    :param hoc_or_python_file: NEURON hoc or Python file to convert
    :type hoc_or_python_file: str
    :returns: True if file was loaded, False if an error occurred
    """
    if hoc_or_python_file.endswith(".py"):
        logger.info(
            "***************\nImporting Python scripts not yet implemented...\n***************"
        )
        return False
    else:
        if not os.path.isfile(hoc_or_python_file):
            logger.info(
                "***************\nProblem importing file %s (%s)..\n***************"
                % (hoc_or_python_file, os.path.abspath(hoc_or_python_file))
            )
            return False
        resp = h.load_file(
            1, hoc_or_python_file
        )  # Using 1 to force loading of the file, in case file with same name was loaded before...
        # returns 1.0 if loads fine, 0.0 if error
        if int(resp) == 0:
            logger.error(f"Error while loading {hoc_or_python_file}:\n{resp}")
            return False

    logger.info(f"Loaded NEURON file: {hoc_or_python_file}")
    return True


def morphinfohoc(section: typing.Optional[str] = None) -> None:
    """Provides information on the morphology of the currently accessed section.

    Uses the hoc utility function. Please prefer the `morph` function
    instead, which is written in pure Python and provides the output in JSON
    which makes it easier to compare information from different cells.

    :param section: section name, current section if None (default)
    :type section: str or None
    """
    warnings.warn(
        "This function will be removed in a future release. Please prefer the pure python `morph` function",
        FutureWarning,
        stacklevel=2,
    )
    retval = load_hoc_or_python_file(str(get_utils_hoc().absolute()))
    if retval is True:
        if section:
            h(f"access {section}")
        h("morph()")
    else:
        logger.error("Could not run morph(). Error loading utils hoc")


def morphinfo(section: typing.Optional[str] = None, doprint: str = "") -> dict:
    """Provides morphology of the provided section.

    Returns a dictionary, and also prints out the information in yaml or json.

    :param section: section name, current section if None (default)
    :type section: str or None
    :param doprint: toggle printing to std output and its format.
        Use "json" or "yaml" to print in the required format, any other value
        to disable printing.
    :type doprint: str
    :returns: morphology information dict
    """
    if section:
        h(f"access {section}")

    cas = h.cas()
    logger.info(f"Getting information for section: {cas}")

    sectiondict = {
        "name": str(cas),
        "nsegs": cas.nseg,
        "n3d": cas.n3d(),
        "3d points": {},
        "segments": {},
    }

    totalarea = 0
    lastx = lasty = lastz = 0
    for i in range(cas.n3d()):
        delx = cas.x3d(i) - lastx
        dely = cas.y3d(i) - lasty
        delz = cas.z3d(i) - lastz
        length = math.sqrt((delx * delx) + (dely * dely) + (delz * delz))
        if i == 0:
            delx = dely = delz = length = 0

        lastx = cas.x3d(i)
        lasty = cas.y3d(i)
        lastz = cas.z3d(i)

        sectiondict["3d points"][i] = {
            "x": cas.x3d(i),
            "y": cas.y3d(i),
            "z": cas.z3d(i),
            "diam": cas.diam3d(i),
            "delx": delx,
            "dely": dely,
            "delz": delz,
            "length": length,
        }

    for i in range(cas.nseg + 2):
        sectiondict["segments"][float(i / (cas.nseg + 1))] = {
            "diam": cas(i / (cas.nseg + 1)).diam,
            "area": str(h.area(i / (cas.nseg + 1))) + " um^2",
        }
        totalarea = totalarea + h.area(i / (cas.nseg + 1))

    sectiondict["totalarea"] = totalarea

    if doprint == "yaml":
        logger.info(yaml.dump(sectiondict, sort_keys=True, indent=4))
        if doprint:
            print(yaml.dump(sectiondict, sort_keys=True, indent=4))
    elif doprint == "json":
        logger.info(json.dumps(sectiondict, indent=4, sort_keys=True))
        if doprint:
            print(json.dumps(sectiondict, indent=4, sort_keys=True))

    return sectiondict


def cellinfohoc() -> None:
    """Provide information on current cell.

    Uses the hoc utility function. Please prefer the `cellinfo` function
    instead, which is written in pure Python and provides the output in JSON
    which makes it easier to compare information from different cells.
    """
    warnings.warn(
        "This function will be removed in a future release. Please prefer the pure python `cellinfo` function",
        FutureWarning,
        stacklevel=2,
    )
    retval = load_hoc_or_python_file(str(get_utils_hoc().absolute()))
    if retval is True:
        h("cellInfo()")
    else:
        logger.error("Could not run cellInfo(). Error loading utils hoc")


def cellinfo(doprint: str = "") -> dict:
    """Provide summary information on the current cell.

    Returns a dictionary, and also prints out the information in yaml or json.

    :param doprint: toggle printing to std output and its format.
        Use "json" or "yaml" to print in the required format, any other value
        to disable printing.
    :type doprint: str
    :returns: cellinfo dict
    """
    # initialise metrics
    cas = h.cas()
    ccell = cas.cell()

    # check of the section is part of a cell
    if ccell is None:
        logger.error("Could not find a cell for this section. Exiting.")
        return {}

    seclist = ccell.all
    return getinfo(seclist, doprint)


def getinfo(seclist: list, doprint: str = "", listall: bool = False):
    """Provide detailed information on the provided section list.

    Returns a dictionary, and also prints out the information in yaml or json.

    :param doprint: toggle printing to std output and its format.
        Use "json" or "yaml" to print in the required format, any other value
        to disable printing.
    :type doprint: str
    :param listall: also list mechs that are not present on any sections
    :type listall: bool
    :returns: dict
    """
    totalDiam = 0
    totalNseg = 0
    totalL = 0
    totalRa = 0
    totalCm = 0
    numSections = 0
    totEk = 0
    totko = 0
    totki = 0
    numEk = 0
    totEna = 0
    totnao = 0
    totnai = 0
    numEna = 0
    totEca = 0
    totcai = 0
    totcao = 0
    numEca = 0

    for sec in seclist:
        totalDiam = totalDiam + sec.diam
        totalNseg = totalNseg + sec.nseg
        totalRa = totalRa + sec.Ra
        totalCm = totalCm + sec.cm

        totalL = totalL + sec.L
        numSections = numSections + 1

        if h.ismembrane("k_ion", sec=sec):
            numEk = numEk + 1
            totEk = totEk + sec.ek
            totko = totko + sec.ko
            totki = totki + sec.ki
        if h.ismembrane("na_ion", sec=sec):
            numEna = numEna + 1
            totEna = totEna + sec.ena
            totnao = totnao + sec.nao
            totnai = totnai + sec.nai
        if h.ismembrane("ca_ion", sec=sec):
            numEca = numEca + 1
            totEca = totEca + sec.eca
            totcai = totcai + sec.cai
            totcao = totcao + sec.cao

    # construct dict to return, so far:
    infodict = {
        "temperature": h.celsius,
        "total_diam": totalDiam,
        "total_nseg": totalNseg,
        "total_L": totalL,
        "total_Ra": totalRa,
        "total_Cm": totalCm,
        "num_sections": numSections,
        "mechanisms": {},
    }

    if numEk > 0:
        infodict["k_ion"] = {
            "nsecs": numEk,
            "avg_rev_pot": (totEk / numEk),
            "int_conc": (totki / numEk),
            "ext_conc": (totko / numEk),
        }
    else:
        infodict["k_ion"] = {
            "nsecs": numEk,
            "avg_rev_pot": "NA",
            "int_conc": "NA",
            "ext_conc": "NA",
        }

    if numEna > 0:
        infodict["na_ion"] = {
            "nsecs": numEna,
            "avg_rev_pot": (totEna / numEna),
            "int_conc": (totnai / numEna),
            "ext_conc": (totnao / numEna),
        }
    else:
        infodict["na_ion"] = {
            "nsecs": numEna,
            "avg_rev_pot": "NA",
            "int_conc": "NA",
            "ext_conc": "NA",
        }

    if numEca > 0:
        infodict["ca_ion"] = {
            "nsecs": numEca,
            "avg_rev_pot": (totEca / numEca),
            "int_conc": (totcai / numEca),
            "ext_conc": (totcao / numEca),
        }
    else:
        infodict["ca_ion"] = {
            "nsecs": numEca,
            "avg_rev_pot": "NA",
            "int_conc": "NA",
            "ext_conc": "NA",
        }

    # https://neuronsimulator.github.io/nrn/python/modelspec/programmatic/mechtype.html#MechanismType
    mt = h.MechanismType(0)
    mname = h.ref("")
    pname = h.ref("")

    for i in range(mt.count()):
        mt.select(i)
        mt.selected(mname)
        # provide storage for mechanism
        # https://neuronsimulator.github.io/nrn/python/programming/mechstan.html#MechanismStandard
        ms = h.MechanismStandard(mname, 1)
        numParams = ms.count()

        # construct empty dicts to hold information
        totParamVal = {}
        paramsectiondict = {}  # type: dict[typing.Any, typing.Any]
        for j in range(numParams):
            # assign pname the name of the jth parameter
            ms.name(pname, j)
            totParamVal[j] = 0
            paramsectiondict[rm_NML_str(pname[0])] = {}

        numSecPresent = 0
        numSegsPresent = 0
        for sec in seclist:
            if h.ismembrane(mname, sec=sec):
                numSecPresent += 1
                numSegsPresent += sec.nseg
                # segment information is provided as a fraction of the total
                # section length, not the segment list
                seginfo = {}  # type: dict[typing.Any, typing.Any]
                for seg in range(1, sec.nseg + 1):
                    seginfo[seg] = {}
                    mid_pt = get_seg_midpoint(seg, sec.nseg)
                    logger.debug(f"section {sec}: {seg}/{sec.nseg}: {mid_pt}")
                    ms._in(mid_pt, sec=sec)
                    for j in range(numParams):
                        ms.name(pname, j)
                        totParamVal[j] += ms.get(pname)
                        if (
                            replace_brackets(str(sec))
                            not in paramsectiondict[rm_NML_str(pname[0])].keys()
                        ):
                            paramsectiondict[rm_NML_str(pname[0])][
                                replace_brackets(str(sec))
                            ] = {
                                "id": str(sec),
                            }
                        if rm_NML_str(pname[0]) in seginfo[seg]:
                            logger.warning(f"{pname[0]} already exists in {seg}")
                        seginfo[seg][rm_NML_str(pname[0])] = ms.get(pname)

                for j in range(numParams):
                    ms.name(pname, j)
                    newseginfo = {}
                    for seg, value in seginfo.items():
                        if rm_NML_str(pname[0]) in value:
                            newseginfo[seg] = value[rm_NML_str(pname[0])]
                            logger.debug(f"{seg}: {value[rm_NML_str(pname[0])]}")

                    values = list(newseginfo.values())
                    unique_values = list(set(values))
                    # if all values are the same, only print them once as '*'
                    if len(unique_values) == 1:
                        paramsectiondict[rm_NML_str(pname[0])][
                            replace_brackets(str(sec))
                        ].update({"nseg": sec.nseg, "values": {"*": unique_values[0]}})
                    else:
                        paramsectiondict[rm_NML_str(pname[0])][
                            replace_brackets(str(sec))
                        ].update({"nseg": sec.nseg, "values": newseginfo})

        if listall or numSecPresent > 0:
            mt_dict = {
                "present_on_secs": numSecPresent,
                "num_params": numParams,
                "parameters": {},
            }

            for j in range(numParams):
                ms.name(pname, j)
                try:
                    param_dict = {
                        "ave_all_segs": totParamVal[j] / numSegsPresent,
                        "values": paramsectiondict[rm_NML_str(pname[0])],
                    }
                except ZeroDivisionError:
                    param_dict = {"ave_all_sections": "NA", "values": "NA"}

                mt_dict["parameters"][rm_NML_str(pname[0])] = param_dict
            infodict["mechanisms"][rm_NML_str(mname[0])] = mt_dict

    if doprint == "yaml":
        logger.info(yaml.dump(infodict, sort_keys=True, indent=4))
        if doprint:
            print(yaml.dump(infodict, sort_keys=True, indent=4))
    elif doprint == "json":
        logger.info(json.dumps(infodict, indent=4, sort_keys=True))
        if doprint:
            print(json.dumps(infodict, indent=4, sort_keys=True))

    return infodict


def secinfohoc(section: str = "") -> None:
    """Provide information on current section, like an expanded `psection()`.
    Uses the hoc utility function. Please prefer the `cellinfo` function
    instead, which is written in pure Python and provides the output in JSON
    which makes it easier to compare information from different cells.
    """
    warnings.warn(
        "This function will be removed in a future release. Please prefer the pure python `secinfo` function",
        FutureWarning,
        stacklevel=2,
    )
    retval = load_hoc_or_python_file(str(get_utils_hoc().absolute()))
    if retval is True:
        if section:
            h(f"access {section}")
        h("secinfo()")
    else:
        logger.error("Could not run secinfo(). Error loading utils hoc")


def secinfo(section: str = "", doprint: str = "json"):
    """Print summary information on provided section, like an expanded
    `psection()`:

    - number of segments in the section,
    - voltage of the section
    - total area
    - total ri
    - information in each segment
      - start
      - end
      - area
      - ri

    Returns a dictionary, and also prints out the information in yaml or json.

    :param section: section to investigate, or current section if ""
    :type section: str
    :param doprint: toggle printing to std output and its format.
        Use "json" or "yaml" to print in the required format, any other value
        to disable printing.
    :type doprint: str
    :returns: section information dict

    """
    if section:
        h(f"access {section}")

    cas = h.cas()
    logger.info(f"Getting information for section: {cas}")

    sectiondict = {
        "name": str(cas),
        "nsegs": cas.nseg,
        "voltage": cas.v,
        "segments": {},
    }

    total_area = 0
    total_ri = 0
    for i in range(1, cas.nseg + 2):
        this_point = i / (cas.nseg + 1)
        next_point = (i + 1) / (cas.nseg + 1)
        half_point = this_point

        area_here = h.area(half_point)
        ri_here = h.ri(half_point)

        total_area += area_here
        total_ri += ri_here

        sectiondict["segments"][i] = {
            "section start": this_point,
            "section end": next_point,
            "area": area_here,
            "ri": str(ri_here * 1e3) + " ohm",
        }

    sectiondict["total area"] = total_area
    sectiondict["total ri"] = str(total_ri * 1e3) + " ohm"

    if doprint == "yaml":
        logger.info(yaml.dump(sectiondict, sort_keys=True, indent=4))
        if doprint:
            print(yaml.dump(sectiondict, sort_keys=True, indent=4))
    elif doprint == "json":
        logger.info(json.dumps(sectiondict, indent=4, sort_keys=True))
        if doprint:
            print(json.dumps(sectiondict, indent=4, sort_keys=True))

    return sectiondict


def areainfo() -> None:
    """Provide information on the area of the cell.

    Iterates over all sections of the current cell providing:

    - x, y, z, diameter information for each segment in the section
    - total area of the section
    - summary metrics for the whole cell

    """
    retval = load_hoc_or_python_file(str(get_utils_hoc().absolute()))
    if retval is True:
        h("areainfo()")
    else:
        logger.error("Could not run areainfo(). Error loading utils hoc")


def allv() -> None:
    """Prints voltage of all compartments (segments)."""
    retval = load_hoc_or_python_file(str(get_utils_hoc().absolute()))
    if retval is True:
        h("allv()")
    else:
        logger.error("Could not run allv(). Error loading utils hoc")


def allca() -> None:
    """Prints Ca conc of all compartments (segments)."""
    retval = load_hoc_or_python_file(str(get_utils_hoc().absolute()))
    if retval is True:
        h("allca()")
    else:
        logger.error("Could not run allca(). Error loading utils hoc")


def allsyns(var: str) -> None:
    """Prints information on network connections for all cells stored in the
    variable `var`

    :param var: name of NEURON variable holding cells to get information for
    :type var: str
    """
    retval = load_hoc_or_python_file(str(get_utils_hoc().absolute()))
    if retval is True:
        h(f"allCells = {var}")
        h("allsyns()")
    else:
        logger.error("Could not run allsyns(). Error loading utils hoc")


def allcells(var: str) -> None:
    """Prints information on all cells stored in the variable `var`.

    :param var: name of NEURON variable holding cells to get information for
    :type var: str
    """
    retval = load_hoc_or_python_file(str(get_utils_hoc().absolute()))
    if retval is True:
        h(f"allCells = {var}")
        h("allcells()")
    else:
        logger.error("Could not run allcells(). Error loading utils hoc")


def get_seg_midpoint(seg: int, nseg: int) -> float:
    """Get mid point of segment

    The total section is from 0 -> 1.

    :param seg: segment to get mid point of
    :type seg: int
    :param nseg: total number of segments
    :type nseg: int
    :returns: location of mid point of segment in (0, 1)
    """
    return (2.0 * seg - 1.0) / (2.0 * nseg)


def replace_brackets(astring: str) -> str:
    """Replaces the [] in strings with _.
    if ] is the last char, just skips it.

    :param astring: id to convert
    :type astring: str
    :returns: converted id

    """
    if astring[-1] == "]":
        astring = astring[:-1]
    return astring.replace("[", "_").replace("]", "_")


def rm_NML_str(astring: str) -> str:
    """Replaces the _NML2 suffix from names to ease comparison

    :param astring: string to modify
    :type astring: str
    :returns: new string
    """
    # inform the user of this change
    if "_NML2" in astring:
        logger.info(f"Removing '_NML2' string from {astring} to ease comparison")
    return astring.replace("_NML2", "")


def export_mod_to_neuroml2(mod_file: str):
    """Helper function to export a mod file describing an ion channel to
    NeuroML2 format.

    Note that these exports usually require more manual work before they are
    the converstion is complete. This method tries to take as much information
    as it can from the mod file to convert it into a NeuroML2 channel file.

    Please use `pynml-channelanalysis` and `pynml-modchannelanalysis` commands
    to generate steady state etc. plots for the two implementations to compare
    them.

    See also: https://docs.neuroml.org/Userdocs/CreatingNeuroMLModels.html#b-convert-channels-to-neuroml

    :param mod_file: full path to mod file
    :type mod_file: str
    """
    logger.info("Generating NeuroML2 representation for mod file: " + mod_file)

    blocks = {}  # type: typing.Dict[typing.Any, typing.Any]
    info = {}
    lines = [(str(ll.strip())).replace("\t", " ") for ll in open(mod_file)]
    line_num = 0
    while line_num < len(lines):
        aline = lines[line_num]
        if len(aline) > 0:
            logger.info(">>> %i > %s" % (line_num, aline))
            # @type l str
            if aline.startswith("TITLE"):
                blocks["TITLE"] = aline[6:].strip()
            if "{" in aline:
                block_name = aline[: aline.index("{")].strip()
                blocks[block_name] = []

                li = aline[aline.index("{") + 1 :]
                bracket_depth = __check_brackets(li, 1)
                while bracket_depth > 0:
                    if len(li) > 0:
                        blocks[block_name].append(li)
                        logger.info("        > %s > %s" % (block_name, li))
                    line_num += 1
                    li = lines[line_num]

                    bracket_depth = __check_brackets(li, bracket_depth)

                rem = li[:-1].strip()
                if len(rem) > 0:
                    blocks[block_name].append(rem)

        line_num += 1

    for line in blocks["STATE"]:
        if " " in line or "\t" in line:
            blocks["STATE"].remove(line)
            for s in line.split():
                blocks["STATE"].append(s)

    for line in blocks["NEURON"]:
        if line.startswith("SUFFIX"):
            info["id"] = line[7:].strip()
        if line.startswith("USEION") and "WRITE" in line:
            info["species"] = line.split()[1]

    gates = []
    for s in blocks["STATE"]:
        gate = {}
        gate["id"] = s
        gate["type"] = "???"
        gate["instances"] = "???"
        gates.append(gate)

    info["type"] = "ionChannelHH"
    info["gates"] = gates

    info["notes"] = (
        "NeuroML2 file automatically generated from NMODL file: %s" % mod_file
    )

    pp.pprint(blocks)

    chan_file_name = "%s.channel.nml" % info["id"]
    chan_file = open(chan_file_name, "w")
    chan_file.write(__merge_with_template(info))
    chan_file.close()


def __check_brackets(line, bracket_depth):
    """Check matching brackets

    :param line: line to check
    :type line: str
    :param bracket_depth: current depth/level of brackets
    :type bracket_depth: int
    :returns: new bracket depth
    :rtype: int
    """
    if len(line) > 0:
        bracket_depth0 = bracket_depth
        for c in line:
            if c == "{":
                bracket_depth += 1
            elif c == "}":
                bracket_depth -= 1
        if bracket_depth0 != bracket_depth:
            logger.info(
                "       <%s> moved bracket %i -> %i"
                % (line, bracket_depth0, bracket_depth)
            )
    return bracket_depth


def __merge_with_template(info):
    """Merge information with the airspeed template file

    :param info: information to fill in the template
    :type info:
    :returns: filled template
    :rtype: str
    """
    templfile = "TEMPLATE.channel.nml"
    if not os.path.isfile(templfile):
        templfile = os.path.join(os.path.dirname(__file__), templfile)
    logger.info("Merging with template %s" % templfile)
    with open(templfile) as f:
        templ = airspeed.Template(f.read())
    return templ.merge(info)
