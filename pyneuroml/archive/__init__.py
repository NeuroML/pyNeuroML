"""
Utilities for exporting NeuroML models into archives

File: pyneuroml/archive/__init__.py

Copyright 2023 NeuroML contributors
"""

import argparse
import logging
import os
import pathlib
import shutil
import typing
from zipfile import ZipFile

from pyneuroml.utils import get_model_file_list
from pyneuroml.utils.cli import build_namespace
from pyneuroml.runners import run_jneuroml
from pyneuroml.sedml import validate_sedml_files

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


DEFAULTS = {
    "zipfileName": None,
    "zipfileExtension": None,
    "filelist": [],
}  # type: typing.Dict[str, typing.Any]


def process_args():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=("A script to create a COMBINE archive ")
    )

    parser.add_argument(
        "rootfile",
        type=str,
        metavar="<NeuroML 2/LEMS file/SED-ML file>",
        help="Name of the NeuroML 2/LEMS/SED-ML main file",
    )

    parser.add_argument(
        "-zipfileName",
        type=str,
        metavar="<zip file name>",
        default=DEFAULTS["zipfileName"],
        help="Extension to use for archive.",
    )
    parser.add_argument(
        "-zipfileExtension",
        type=str,
        metavar="<zip file extension>",
        default=DEFAULTS["zipfileExtension"],
        help="Extension to use for archive: .neux by default",
    )
    parser.add_argument(
        "-filelist",
        nargs="*",
        metavar="<explicit list of files to create archive of>",
        default=DEFAULTS["filelist"],
        help="Explicit list of files to create archive of.",
    )
    parser.add_argument(
        "-sedml",
        action="store_true",
        help=("Generate SED-ML file from main LEMS file and use as master file."),
    )

    return parser.parse_args()


def main(args=None):
    """Main runner method"""
    if args is None:
        args = process_args()

    cli(a=args)


def cli(a: typing.Optional[typing.Any] = None, **kwargs: str):
    """Main cli caller method"""
    a = build_namespace(DEFAULTS, a, **kwargs)

    rootfile = a.rootfile
    zipfile_extension = None

    # first generate SED-ML file
    # use .omex as extension
    if (
        a.rootfile.startswith("LEMS") and a.rootfile.endswith(".xml")
    ) and a.sedml is True:
        logger.debug("Generating SED-ML file from LEMS file")
        run_jneuroml("", a.rootfile, "-sedml")

        rootfile = a.rootfile.replace(".xml", ".sedml")
        zipfile_extension = ".omex"

        # validate the generated file
        validate_sedml_files([rootfile])

    # if explicitly given, use that
    if a.zipfile_extension is not None:
        zipfile_extension = a.zipfile_extension

    create_combine_archive(
        zipfile_name=a.zipfile_name,
        rootfile=rootfile,
        zipfile_extension=zipfile_extension,
        filelist=a.filelist,
    )


def create_combine_archive(
    rootfile: str,
    zipfile_name: typing.Optional[str] = None,
    zipfile_extension=".neux",
    filelist: typing.List[str] = [],
    extra_files: typing.List[str] = [],
):
    """Create a combine archive that includes all files referred to (included
    recursively) by the provided rootfile.  If a file list is provided, it will
    attempt to create an archive of the provided files. Note that it is for the
    user to ensure that the paths in the provided file list are correct.

    All file paths must be relative to the provided rootfile.

    For more information, see:

    Bergmann, F.T., Adams, R., Moodie, S. et al. COMBINE archive and OMEX
    format: one file to share all information to reproduce a modeling project.
    BMC Bioinformatics 15, 369 (2014).
    https://doi.org/10.1186/s12859-014-0369-z

    :param zipfile_name: name of zip file without extension: rootfile if not provided
    :type zipfile_name: str
    :param rootfile: full path to main root file (SED-ML/LEMS/NeuroML2)
    :type rootfile: str
    :param zipfile_extension: extension for zip file, starting with ".".
    :type zipfile_extension: str
    :param filelist: explicit list of files to create archive of
        if given, the function will not attempt to list model files itself
    :type filelist: list of strings
    :param extra_files: extra files to include in archive
    :type extra_files: list of strings
    :returns: None
    :raises ValueError: if a root file is not provided
    """
    if not rootfile:
        raise ValueError("Please provide a rootfile.")

    # compute rootdir
    rootdir = None
    if "/" in rootfile:
        logger.debug(f"Calculating rootdir from {rootfile}")
        rootdir = str(pathlib.Path(rootfile).parent)
        rootfile = pathlib.Path(rootfile).name
    else:
        logger.debug("rootdir is '.'")
        rootdir = "."

    # compute zipfile name from rootfile
    if not zipfile_name:
        logger.info(f"No zipfile name provided. Using {rootfile}")
        zipfile_name = rootfile

    lems_def_dir = None
    if len(filelist) == 0:
        lems_def_dir = get_model_file_list(rootfile, filelist, rootdir, lems_def_dir)

    create_combine_archive_manifest(rootfile, filelist + extra_files, rootdir)
    filelist.append("manifest.xml")

    # change to directory of rootfile
    thispath = os.getcwd()
    os.chdir(rootdir)

    with ZipFile(zipfile_name + zipfile_extension, "w") as archive:
        for f in filelist + extra_files:
            archive.write(f)
    os.chdir(thispath)

    if lems_def_dir is not None:
        logger.info(f"Removing LEMS definitions directory {lems_def_dir}")
        shutil.rmtree(lems_def_dir)

    logger.info(
        f"Archive {rootdir}/{zipfile_name}{zipfile_extension} created with manifest file {rootdir}/manifest.xml."
    )


def create_combine_archive_manifest(
    rootfile: str, filelist: typing.List[str], rootdir: str = "."
):
    """Create a combine archive manifest file called manifest.xml

    :param rootfile: the root file for this archive; marked as "master"
    :type rootfile: str
    :param filelist: list of files to be included in the manifest
    :type filelist: list of strings
    :param rootdir: directory where root file lives
    :type rootdir: str
    """
    manifest = rootdir + "/manifest.xml"
    with open(manifest, "w") as mf:
        print('<?xml version="1.0" encoding="utf-8"?>', file=mf)
        print(
            """<omexManifest xmlns="http://identifiers.org/combine.specifications/omex-manifest">""",
            file=mf,
        )

        print(
            """\t<content location="." format="http://identifiers.org/combine.specifications/omex"/>""",
            file=mf,
        )

        for f in filelist:
            format_string = None
            logger.info(f"Processing file: {f}")
            if f.endswith(".xml") and f.startswith("LEMS"):
                # TODO: check what the string for LEMS should be
                format_string = "http://identifiers.org/combine.specifications/neuroml"
            elif f.endswith(".nml"):
                format_string = "http://identifiers.org/combine.specifications/neuroml"
            elif f.endswith(".sedml"):
                format_string = "http://identifiers.org/combine.specifications/sed-ml"
            elif f.endswith(".rdf"):
                format_string = (
                    "http://identifiers.org/combine.specifications/omex-metadata"
                )
            elif f.endswith(".pdf"):
                format_string = "http://purl.org/NET/mediatypes/application/pdf"

            print(
                f"""\t<content location="{f}" {'master="true"' if f == rootfile else ""} {"format=" if format_string else ""}"{format_string}"/>""",
                file=mf,
            )

        print(
            """</omexManifest>""",
            file=mf,
            flush=True,
        )
