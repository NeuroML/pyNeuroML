#!/usr/bin/env python3
"""
Utilities for recording from NeuroML models

File: recording.py

Copyright 2023 NeuroML contributors
"""


import typing
import logging

from pyneuroml.lems import LEMSSimulation


logger = logging.getLogger(__name__)


def record_exposure_from_segments(
    cell_path: str,
    simulation: LEMSSimulation,
    output_file_id: str,
    segment_ids: typing.List[str],
    recordables: typing.List[str]
) -> None:
    """Helper method to record `recordables` from provided `segments` in a cell.

    This method will iterate over the cell, and for every segment provided in
    the list, it will add a new column to the output file in the provided
    simulation object.

    See also: `LEMSSimulation.add_column_to_output_file`.
    See also: `neuroml.Cell.get_all_segments_in_group`

    :param cell_path: path to cell, usually on the lines of `population_id/instance_id/cell_id/`
    :type cell_path: str
    :param simulation: simulation object
    :type simulation: LEMSSimulation
    :param output_file_id: id of output file
    :type output_file_id: str
    :param segment_ids: segments to record from
    :type segment_ids: list of ids (strings)
    :param recordables: recordables (exposures)
    :type recordables: list of exposures (strings)
    :returns: None

    """
    for seg in segment_ids:
        for rec in recordables:
            fullpath = cell_path + ("/" if cell_path[-1] != "/" else "") + seg
            simulation.add_column_to_output_file(
                output_file_id,
                f"{fullpath.replace('/', '_')}_{rec}",
                rec
            )
            logging.debug(f"Added {fullpath} recording to {simulation.lems_info['sim_id']}")
