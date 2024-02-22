#!/usr/bin/env python3
"""
Methods related to generating graphical representations of NeuroML models

File: pyneuroml/modelgraphs.py

Copyright 2024 NeuroML contributors
"""

import logging

from pyneuroml import DEFAULTS
from pyneuroml.runners import run_jneuroml

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def generate_nmlgraph(
    nml2_file_name: str, level: int = 1, engine: str = "dot", **kwargs
) -> None:
    """Generate NeuroML graph.

    :param nml2_file_name: NML file to parse
    :type nml2_file_name: str
    :param level: level of graph to generate (default: '1')
    :type level: int
    :param engine: graph engine to use (default: 'dot')
    :type engine: str
    :param kwargs: other key word agruments to pass to GraphVizHandler
        See the GraphVizHandler in NeuroMLlite for information on permissible
        arguments:
        https://github.com/NeuroML/NeuroMLlite/blob/master/neuromllite/GraphVizHandler.py


    """
    from neuroml.hdf5.NeuroMLXMLParser import NeuroMLXMLParser
    from neuromllite.GraphVizHandler import GraphVizHandler

    logger.info(
        "Converting %s to graphical form, level %i, engine %s"
        % (nml2_file_name, level, engine)
    )

    handler = GraphVizHandler(level=level, engine=engine, nl_network=None, **kwargs)
    currParser = NeuroMLXMLParser(handler)
    currParser.parse(nml2_file_name)
    handler.finalise_document()

    logger.info("Done with GraphViz...")


def generate_lemsgraph(lems_file_name: str, verbose_generate: bool = True) -> bool:
    """Generate LEMS graph using jNeuroML

    :param lems_file_name: LEMS file to parse
    :type lems_file_name: str
    :param verbose_generate: whether or not jnml should be run with verbosity output
    :type verbose_generate: bool
    :returns bool: True of jnml ran without errors, exits without a return if jnml fails
    """
    pre_args = ""
    post_args = "-lems-graph"

    return run_jneuroml(
        pre_args,
        lems_file_name,
        post_args,
        verbose=verbose_generate,
        report_jnml_output=verbose_generate,
        exit_on_fail=True,
        return_string=False,
    )


def nml2_to_svg(
    nml2_file_name: str,
    max_memory: str = DEFAULTS["default_java_max_memory"],
    verbose: bool = True,
) -> None:
    """Generate the SVG representation of a NeuroML model using jnml

    :param nml2_file_name: name of NeuroML2 file to generate SVG for
    :type nml2_file_name: str
    :param max_memory: maximum memory allowed for use by the JVM
    :type max_memory: str
    :param verbose: toggle whether jnml should print verbose information
    :type verbose: bool
    """
    logger.info("Converting NeuroML2 file: {} to SVG".format(nml2_file_name))

    post_args = "-svg"

    run_jneuroml("", nml2_file_name, post_args, max_memory=max_memory, verbose=verbose)


def nml2_to_png(
    nml2_file_name: str,
    max_memory: str = DEFAULTS["default_java_max_memory"],
    verbose: bool = True,
) -> None:
    """Generate the PNG representation of a NeuroML model using jnml

    :param nml2_file_name: name of NeuroML2 file to generate PNG for
    :type nml2_file_name: str
    :param max_memory: maximum memory allowed for use by the JVM
    :type max_memory: str
    :param verbose: toggle whether jnml should print verbose information
    :type verbose: bool
    """
    logger.info("Converting NeuroML2 file: %s to PNG" % nml2_file_name)

    post_args = "-png"

    run_jneuroml("", nml2_file_name, post_args, max_memory=max_memory, verbose=verbose)
