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

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


DEFAULTS = {
    "zipfileName": None,
    "zipfileExtension": ".neux",
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
        metavar="<NeuroML 2/LEMS file>",
        help="Name of the NeuroML 2/LEMS main file",
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
        help="Extension to use for archive.",
    )
    parser.add_argument(
        "-filelist",
        nargs="*",
        metavar="<explicit list of files to create archive of>",
        default=DEFAULTS["filelist"],
        help="Explicit list of files to create archive of.",
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
    create_combine_archive(
        zipfile_name=a.zipfile_name,
        rootfile=a.rootfile,
        zipfile_extension=a.zipfile_extension,
        filelist=a.filelist,
    )


def create_combine_archive(
    rootfile: str,
    zipfile_name: typing.Optional[str] = None,
    zipfile_extension=".neux",
    filelist: typing.List[str] = [],
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
    :param rootfile: full path to main root file
    :type rootfile: str
    :param zipfile_extension: extension for zip file, starting with ".".
    :type zipfile_extension: str
    :param filelist: explicit list of files to create archive of
    :type filelist: list of strings
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

    create_combine_archive_manifest(rootfile, filelist, rootdir)
    filelist.append("manifest.xml")

    # change to directory of rootfile
    thispath = os.getcwd()
    os.chdir(rootdir)

    with ZipFile(zipfile_name + zipfile_extension, "w") as archive:
        for f in filelist:
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
            """
            <omexManifest
            xmlns="http://identifiers.org/combine.specifications/omex-manifest">
            """,
            file=mf,
        )

        print(
            """
            <content location="."
                format="http://identifiers.org/combine.specifications/omex"/>
            """,
            file=mf,
        )

        for f in filelist:
            if f == rootfile:
                print(
                    f"""
                    <content location="{f}" master="true"
                        format="http://identifiers.org/combine.specifications/neuroml"/>
                    """,
                    file=mf,
                )
            else:
                print(
                    f"""
                    <content location="{f}"
                        format="http://identifiers.org/combine.specifications/neuroml"/>
                    """,
                    file=mf,
                )

        print(
            """
            </omexManifest>
            """,
            file=mf,
            flush=True,
        )
