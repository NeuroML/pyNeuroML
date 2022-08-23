"""

A package of utilities for exporting NEURON models to NeuroML 2 & for analysing/comparing NEURON models to NeuroML versions

Will use some some utilities from https://github.com/OpenSourceBrain/NEURONShowcase

"""

import os
import logging
import warnings
import typing
import pathlib
import json
import math


import yaml
try:
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Dumper

from pyneuroml.pynml import validate_neuroml1
from pyneuroml.pynml import validate_neuroml2

from pyneuroml.neuron.nrn_export_utils import set_erev_for_mechanism
from neuron import h


logger = logging.getLogger(__name__)


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


def load_hoc_or_python_file(
    hoc_or_python_file: str
) -> bool:
    """Load a NEURON hoc file or Python script.

    Note: loading Python scripts is not yet supported.

    :param hoc_or_python_file: NEURON hoc or Python file to convert
    :type hoc_or_python_file: str
    :returns: 0 if file was loaded, 1 if an error occurred
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


def morphhoc(section: typing.Optional[str] = None) -> None:
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
            h(f'access {section}')
        h("morph()")
    else:
        logger.error("Could not run morph(). Error loading utils hoc")


def morph(section: typing.Optional[str] = None, doprint: str = "") -> dict:
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
        h(f'access {section}')

    logger.info(f"Getting information for section: {section}")
    totalarea = 0
    cas = h.cas()

    sectiondict = {
        'name': str(cas),
        'nsegs': cas.nseg,
        'n3d': cas.n3d(),
        '3d points': {
        },
        'segments': {
        }
    }

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

        sectiondict['3d points'][i] = {
            'x': cas.x3d(i),
            'y': cas.y3d(i),
            'z': cas.z3d(i),
            'diam': cas.diam3d(i),
            'delx': delx,
            'dely': dely,
            'delz': delz,
            'length': length
        }

    for i in range(cas.nseg + 2):
        sectiondict['segments'][float(i / (cas.nseg + 1))] = {
            'diam': cas(i / (cas.nseg + 1)).diam,
            'area': str(h.area(i / (cas.nseg + 1))) + " um^2",
        }
        totalarea = totalarea + h.area(i / (cas.nseg + 1))

    sectiondict['totalarea'] = totalarea

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

    """
    # initialise metrics
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

    cas = h.cas()
    ccell = cas.cell()
    seclist = ccell.all

    for sec in seclist:
        totalDiam = totalDiam + sec.diam
        totalNseg = totalNseg + sec.nseg
        totalRa = totalRa + sec.Ra
        totalCm = totalCm + sec.cm

        totalL = totalL + sec.L
        numSections = numSections + 1

        if (h.ismembrane("k_ion", sec=sec)):
            numEk = numEk + 1
            totEk = totEk + sec.ek
            totko = totko + sec.ko
            totki = totki + sec.ki
        if (h.ismembrane("na_ion", sec=sec)):
            numEna = numEna + 1
            totEna = totEna + sec.ena
            totnao = totnao + sec.nao
            totnai = totnai + sec.nai
        if (h.ismembrane("ca_ion", sec=sec)):
            numEca = numEca + 1
            totEca = totEca + sec.eca
            totcai = totcai + sec.cai
            totcao = totcao + sec.cao

    # construct dict to return, so far:
    cellinfo = {
        'temperature': h.celsius,
        'total_diam': totalDiam,
        'total_nseg': totalNseg,
        'total_L': totalL,
        'total_Ra': totalRa,
        'total_Cm': totalCm,
        'num_sections': numSections,
        'k_ion': {
            'nsecs': numEk,
            'avg_rev_pot': (totEk / numEk),
            'int_conc': (totki / numEk),
            'ext_conc': (totko / numEk),
        },
        'na_ion': {
            'nsecs': numEna,
            'avg_rev_pot': (totEna / numEna),
            'int_conc': (totnai / numEna),
            'ext_conc': (totnao / numEna),
        },
        'ca_ion': {
            'nsecs': numEca,
            'avg_rev_pot': (totEca / numEca),
            'int_conc': (totcai / numEca),
            'ext_conc': (totcao / numEca),
        },
        'mechanisms': {
        },
    }

    # https://neuronsimulator.github.io/nrn/python/modelspec/programmatic/mechtype.html#MechanismType
    mt = h.MechanismType(0)
    mname = h.ref('')
    pname = h.ref('')

    for i in range(mt.count()):
        mt.select(i)
        mt.selected(mname)
        ms = h.MechanismStandard(mname, 1)
        numParams = ms.count()
        numPresent = 0

        totParamVal = {}
        for j in range(numParams):
            totParamVal[j] = 0

        for sec in seclist:
            if (h.ismembrane(mname, sec=sec)):
                numPresent += 1
                ms._in(sec=sec)
                for j in range(numParams):
                    ms.name(pname, j)
                    totParamVal[j] += ms.get(pname)

        mt_dict = {
            'present_on': numPresent,
            'num_params': numParams,
            'parameters': {
            }
        }

        for j in range(numParams):
            ms.name(pname, j)
            try:
                param_dict = {
                    'ave_all_sections': totParamVal[j] / numPresent
                }
            except ZeroDivisionError:
                param_dict = {
                    'ave_all_sections': 'NA'
                }

            mt_dict['parameters'][pname[0]] = param_dict
        cellinfo['mechanisms'][mname[0]] = mt_dict

    if doprint == "yaml":
        logger.info(yaml.dump(cellinfo, sort_keys=True, indent=4))
        if doprint:
            print(yaml.dump(cellinfo, sort_keys=True, indent=4))
    elif doprint == "json":
        logger.info(json.dumps(cellinfo, indent=4, sort_keys=True))
        if doprint:
            print(json.dumps(cellinfo, indent=4, sort_keys=True))

    return cellinfo


def secinfo() -> None:
    """Provide information on current section, like an expanded `psection()`."""
    retval = load_hoc_or_python_file(str(get_utils_hoc().absolute()))
    if retval is True:
        h("secinfo()")
    else:
        logger.error("Could not run secinfo(). Error loading utils hoc")


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
