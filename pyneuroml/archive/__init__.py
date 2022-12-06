"""
Utilities for exporting NeuroML models into archives

File: pyneuroml/archive/__init__.py

Copyright 2022 NeuroML contributors
Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com>
"""


import os
import typing
import logging
import pathlib
from zipfile import ZipFile
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
    :raises ValueError: if a file that does not have ".xml" or ".nml" as extension is encountered
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


def create_combine_archive(zipfile_name: str, rootfile: str, rootdir: str =
                           ".", zipfile_extension=".neux"):
    """Create a combine archive that includes all files referred to by the
    provided rootfile.

    For more information, see:

    Bergmann, F.T., Adams, R., Moodie, S. et al. COMBINE archive and OMEX
    format: one file to share all information to reproduce a modeling project.
    BMC Bioinformatics 15, 369 (2014).
    https://doi.org/10.1186/s12859-014-0369-z

    :param zipfile_name: name of zip file without extension
    :type zipfile_name: str
    :param rootfile: main root file
    :type rootfile: str
    :param rootdir: directory where root file lives
    :type rootdir: str
    :param zipfile_extension: extension for zip file, starting with ".".
    :type zipfile_extension: str
    :returns: None
    """
    filelist = []  # type: typing.List[str]
    get_model_file_list(rootfile, filelist, rootdir, None)

    create_combine_archive_manifest(rootfile, filelist, rootdir)
    filelist.append("manifest.xml")

    # change to directory of rootfile
    thispath = os.getcwd()
    os.chdir(rootdir)

    with ZipFile(zipfile_name + zipfile_extension, 'w') as archive:
        for f in filelist:
            archive.write(f)
    os.chdir(thispath)

    print(f"{zipfile_name}{zipfile_extension} created in {rootdir}.")


def create_combine_archive_manifest(rootfile: str, filelist: typing.List[str],
                                    rootdir: str = "."):
    """Create a combine archive manifest file called manifest.xml

    :param rootfile: the root file for this archive; marked as "master"
    :type rootfile: str
    :param filelist: list of files to be included in the manifest
    :type filelist: list of strings
    :param rootdir: directory where root file lives
    :type rootdir: str
    """
    manifest = rootdir + "/manifest.xml"
    with open(manifest, 'w') as mf:
        print('<?xml version="1.0" encoding="utf-8"?>', file=mf)
        print(
            """
            <omexManifest
            xmlns="http://identifiers.org/combine.specifications/omex-manifest">
            """, file=mf)

        print(
            """
            <content location="."
                format="http://identifiers.org/combine.specifications/omex"/>
            """, file=mf)

        for f in filelist:
            print(
                f"""
                <content location="{f}"
                    format="http://identifiers.org/combine.specifications/neuroml"/>
                """, file=mf)

        print(
            """
            </omexManifest>
            """, file=mf, flush=True)
