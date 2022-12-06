"""
Utilities for exporting NeuroML models into archives

File: pyneuroml/archive/__init__.py

Copyright 2022 NeuroML contributors
Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com>
"""


import typing
import logging
import pathlib
from neuroml.loaders import read_neuroml2_file
from pyneuroml.pynml import extract_lems_definition_files
from lems.model.model import Model

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


STANDARD_LEMS_FILES = [
    "Cells.xml",
    "Channels.xml",
    "Inputs.xml",
    "Networks.xml",
    "NeuroML2CoreTypes.xml",
    "NeuroMLCoreCompTypes.xml",
    "NeuroMLCoreDimensions.xml",
    "PyNN.xml",
    "Simulation.xml",
    "Synapses.xml",
]


def get_model_file_list(
    rootfile: str,
    filelist: typing.List[str],
    rootdir: str = ".",
    lems_def_dir: str = None,
) -> None:
    """Get the list of files to archive.

    This method will take the rootfile, and recursively resolve all the files
    it uses.

    :param rootfile: main NeuroML or LEMS file to resolve
    :type rootfile: str
    :param filelist: list of file paths to append to
    :type filelist: list of strings
    :param rootdir: directory holding the root file
    :type rootdir: str
    """
    logger.info(f"Processing {rootfile}")

    fullrootdir = pathlib.Path(rootdir).absolute()

    # Only store path of file relative to the rootdir, if it's a descendent of
    # rootdir
    if rootfile.startswith(str(fullrootdir)):
        relrootfile = rootfile.replace(str(fullrootdir), "")
        if relrootfile.startswith("/"):
            relrootfile = relrootfile[1:]
    else:
        relrootfile = rootfile

    if relrootfile in filelist:
        logger.debug(f"Already processed {rootfile}. No op.")
        return

    logger.debug(f"Appending: {relrootfile}")
    filelist.append(relrootfile)

    if rootfile.endswith(".nml"):
        if pathlib.Path(rootfile).is_absolute():
            rootdoc = read_neuroml2_file(rootfile)
        else:
            rootdoc = read_neuroml2_file(rootdir + "/" + rootfile)
        logger.debug(f"Has includes: {rootdoc.includes}")
        for inc in rootdoc.includes:
            get_model_file_list(inc.href, filelist, rootdir)

    elif rootfile.endswith(".xml"):
        # extract the standard NeuroML2 LEMS definitions into a directory
        # so that the LEMS parser can find them
        if lems_def_dir is None:
            lems_def_dir = extract_lems_definition_files()

        if pathlib.Path(rootfile).is_absolute():
            fullrootfilepath = rootfile
        else:
            fullrootfilepath = rootdir + "/" + rootfile

        model = Model(include_includes=True, fail_on_missing_includes=True)
        model.add_include_directory(lems_def_dir)
        model.import_from_file(fullrootfilepath)

        for inc in model.included_files:
            incfile = pathlib.Path(inc).name
            if incfile in STANDARD_LEMS_FILES:
                logger.info(f"Ignoring NeuroML2 standard LEMS file: {inc}")
                continue
            get_model_file_list(inc, filelist, rootdir, lems_def_dir)

    else:
        raise ValueError(f"File must have a .xml or .nml extension. We got: {rootfile}")
