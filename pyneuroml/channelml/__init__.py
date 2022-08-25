#!/usr/bin/env python3
"""
ChannelML related functions

Initial implementation at
https://sourceforge.net/p/neuroml/code/HEAD/tree/NeuroML2/ChannelMLConvert/

File: pyneuroml/channelml/__init__.py

Copyright 2022 NeuroML contributors
"""


import sys
import logging
import typing
import pathlib
from lxml.etree import parse, XSLT, tostring


logger = logging.getLogger(__name__)


def channelml2nml(
    channelmlfile: str, xsltfile: str = None
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
    except:
        logger.error(f"Cannot parse channelml file: {channelmlfile}")
        return None
    if not xsltfile:
        cwd = pathlib.Path(__file__).parent
        xsltfile = str(cwd / pathlib.Path("ChannelML2NeuroML2.xsl"))

    try:
        xslt = parse(xsltfile)
    except:
        logger.error(f"Cannot parse XSL: {xsltfile}")
        return None

    transform = XSLT(xslt)
    newdom = transform(dom)

    converted_string = (tostring(newdom, pretty_print=True)).decode()
    logger.debug(f"{converted_string}")
    return converted_string
