#!/usr/bin/env python3
"""
ChannelML related functions

Initial implementation at
https://sourceforge.net/p/neuroml/code/HEAD/tree/NeuroML2/ChannelMLConvert/

For converting Channelpedia XML files in the BlueBrain format, please refer to
https://github.com/OpenSourceBrain/BlueBrainProjectShowcase/blob/master/Channelpedia/ChannelpediaToNeuroML2.py

File: pyneuroml/channelml/__init__.py

Copyright 2023 NeuroML contributors
"""

import argparse
import logging
import pathlib
import typing
from typing import Optional

from lxml.etree import XSLT, parse, tostring

from pyneuroml.utils.cli import build_namespace

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULTS = {
    "saveToFile": None,
    "xsltfile": None,
}


def channelml2nml(
    channelmlfile: str, xsltfile: Optional[str] = None
) -> typing.Optional[str]:
    """Convert a ChannelML file to NeuroMLv2.

    The second argument is optional, and if not set, the XSL file provided by
    pyNeuroML will be used. This is recommended.

    :param channelmlfile: ChannelML file to convert
    :type channelmlfile: str
    :param xsltfile: XSL file to use for conversion (default: None, to use XSLT
        provided in pyNeuroML)
    :type xsltfile: str
    :returns: converted string
    :rtype: str

    """
    try:
        dom = parse(channelmlfile)
    except Exception:
        logger.error(f"Cannot parse channelml file: {channelmlfile}")
        return None
    if not xsltfile:
        cwd = pathlib.Path(__file__).parent
        xsltfile = str(cwd / pathlib.Path("ChannelML2NeuroML2beta.xsl"))

    try:
        xslt = parse(xsltfile)
    except Exception:
        logger.error(f"Cannot parse XSL: {xsltfile}")
        return None

    transform = XSLT(xslt)
    newdom = transform(dom)

    converted_string = (tostring(newdom, pretty_print=True)).decode()
    logger.debug(f"{converted_string}")
    return converted_string


def process_args():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=("A script to convert ChannelML files to NeuroML2")
    )

    parser.add_argument(
        "channelmlfile",
        type=str,
        metavar="<ChannelML file>",
        help="Path of the ChannelML file",
    )

    parser.add_argument(
        "-xsltfile",
        type=str,
        metavar="<XSLT file>",
        help="Path to the XSLT file",
        default=None,
    )

    parser.add_argument(
        "-saveToFile",
        type=str,
        metavar="<Output file name>",
        default=None,
        help="Name of the outputfile file",
    )

    return parser.parse_args()


def main(args=None):
    """Main runner for entrypoint"""
    if args is None:
        args = process_args()

    a = build_namespace(DEFAULTS, args)
    retval = channelml2nml(a.channelmlfile, a.xsltfile)
    print(retval)
    if a.save_to_file:
        with open(a.save_to_file, "w") as f:
            print(retval, file=f, flush=True)
            logger.info(f"Output saved to {a.save_to_file}")


if __name__ == "__main__":
    main()
