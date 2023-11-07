#!/usr/bin/env python3
"""
Connectivity plotting methods

File: pyneuroml/plot/Connectivity.py

Copyright 2023 NeuroML contributors
"""

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def plot_connectivity_matrix(filename, level):
    """Plot a connectivity matrix

    :param filename: name of NeuroML file
    :type filename: str
    :param level: level at which to plot
    :type level: int
    """
    from neuromllite.MatrixHandler import MatrixHandler
    from neuroml.hdf5.NeuroMLXMLParser import NeuroMLXMLParser

    logger.info("Converting %s to matrix form, level %i" % (filename, level))

    handler = MatrixHandler(level=level, nl_network=None)

    currParser = NeuroMLXMLParser(handler)
    currParser.parse(filename)
    handler.finalise_document()

    logger.info("Done with MatrixHandler...")


def plot_chord_diagram(filename):
    """Plot a chord connectivity diagram

    :param filename: name of NeuroML file
    :type filename: str
    """
    pass
