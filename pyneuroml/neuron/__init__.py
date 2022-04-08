"""

A package of utilities for exporting NEURON models to NeuroML 2 & for analysing/comparing NEURON models to NeuroML versions

Will use some some utilities from https://github.com/OpenSourceBrain/NEURONShowcase

"""

import os
import logging
import warnings

from pyneuroml.pynml import validate_neuroml1
from pyneuroml.pynml import validate_neuroml2

from pyneuroml.neuron.nrn_export_utils import set_erev_for_mechanism
from neuron import h

logger = logging.getLogger(__name__)


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
        if hoc_or_python_file.endswith(".py"):
            logger.info(
                "***************\nImporting Python scripts not yet implemented...\n***************"
            )
        else:
            if not os.path.isfile(hoc_or_python_file):
                logger.info(
                    "***************\nProblem importing file %s (%s)..\n***************"
                    % (hoc_or_python_file, os.path.abspath(hoc_or_python_file))
                )
            h.load_file(
                1, hoc_or_python_file
            )  # Using 1 to force loading of the file, in case file with same name was loaded before...
    else:
        logger.info(
            "hoc_or_python_file variable is None; exporting what's currently in memory..."
        )

    for ion in known_rev_potentials.keys():
        set_erev_for_mechanism(ion, known_rev_potentials[ion])

    logger.info("Loaded NEURON file: %s" % hoc_or_python_file)

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
