#!/usr/bin/env python3
"""
Utilities for analysis of simulation generated data.

File: pyneuroml/utils/simdata.py

Copyright 2025 NeuroML contributors
Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com>
"""

import logging
import os
import typing
from datetime import datetime

import numpy
from lxml import etree

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


def load_traces_from_data_file(
    data_file_names: typing.Union[str, typing.List[str]],
    columns: typing.Optional[typing.List[int]] = None,
) -> typing.Dict[str, typing.Dict]:
    """Load traces from a data file.

    :param data_file_names: one or more names of data files
    :type data_file_names: str or list(str)
    :param columns: column indices to plot
    :type columns: list of ints: [1, 2, 3]
    :returns: TODO

    """
    if isinstance(data_file_names, str):
        data_file_names = [data_file_names]

    all_traces = {}
    for f in data_file_names:
        traces = {}
        logger.info(f"Processing: {f}")

        data_array = numpy.loadtxt(f)
        traces["t"] = data_array[:, 0]
        num_cols = numpy.shape(data_array)[1]
        for i in range(1, num_cols, 1):
            if columns and len(columns) > 0:
                if i not in columns:
                    logger.warning(f"Skipping column {i}")
                    continue

            traces[f"{f}_{i}"] = data_array[:, i]

        all_traces[f] = traces

    return all_traces


def load_sim_data_from_lems_file(
    lems_file_name: str,
    base_dir: str = ".",
    get_events: bool = False,
    get_traces: bool = True,
    t_run: datetime = datetime(1900, 1, 1),
    remove_dat_files_after_load: bool = False,
):
    """Load simulation outputs from LEMS simulation run.

    .. versionadded:: 1.2.2

    :param lems_file_name: name of LEMS file that was used to generate the data
    :type lems_file_name: str
    :param base_dir: directory to run in
    :type base_dir: str
    :param t_run: time of run
    :type t_run: datetime
    :param get_events: toggle whether events should be loaded
    :type get_events: bool
    :param get_traces: toggle whether traces should be loaded
    :type get_traces: bool
    :param remove_dat_files_after_load: toggle if data files should be deleted after they've been loaded
    :type remove_dat_files_after_load: bool

    :returns: if both `get_events` and `get_traces` are selected, a tuple with
        two dictionaries of dictionaries, one for traces, one for events, is
        returned:

        .. code-block:: python

            all_traces, all_events

        Otherwise one dictionary of dictionaries for whichever was selected is
        returned.

        The events dictionary has the following format:

        .. code-block:: python

            {
                "outputfile":
                    {
                        '<value of select attribute>': { 'cell id': [<events>] }
                    }
            }

        The traces dictionary has the following format:

        .. code-block:: python

            {
                "outputfile":
                    {
                        't': [<values>],
                        'col 1': [<values>]
                        'col 2': [<values>]
                    }
            }

        Each list has multiple dictionaries, one each for each output file in
        the LEMS file.

    :raises ValueError: if neither traces nor events are selected for loading
    :raises OSError: if simulation output data file could not be found
    :raises Exception: if the output file has not been modified since the
        simulation was run (given as `t_run`)
    """
    if not get_events and not get_traces:
        raise ValueError("One of get_events or get_traces must be True")

    all_traces: typing.Dict[str, typing.Dict] = {}
    all_events: typing.Dict[str, typing.Dict] = {}

    if not os.path.isfile(lems_file_name):
        real_lems_file = os.path.realpath(os.path.join(base_dir, lems_file_name))
    else:
        real_lems_file = os.path.realpath(lems_file_name)

    logger.debug(
        f"Reloading data specified in LEMS file: {lems_file_name} ({real_lems_file}), base_dir: {base_dir}, cwd: {os.getcwd()}"
    )

    base_lems_file_path = os.path.dirname(os.path.realpath(lems_file_name))
    tree = etree.parse(real_lems_file)

    sim = tree.getroot().find("Simulation")
    ns_prefix = ""

    possible_prefixes = ["{http://www.neuroml.org/lems/0.7.2}"]
    if sim is None:
        # print(tree.getroot().nsmap)
        # print(tree.getroot().getchildren())
        for pre in possible_prefixes:
            for comp in tree.getroot().findall(pre + "Component"):
                if comp.attrib["type"] == "Simulation":
                    ns_prefix = pre
                    sim = comp

    if get_events:
        event_output_files = sim.findall(ns_prefix + "EventOutputFile")
        for i, of in enumerate(event_output_files):
            events: typing.Dict = {}

            name = of.attrib["fileName"]
            file_name = os.path.join(base_dir, name)
            if not os.path.isfile(file_name):  # If not relative to the LEMS file...
                file_name = os.path.join(base_lems_file_path, name)

            # if not os.path.isfile(file_name): # If not relative to the LEMS file...
            #    file_name = os.path.join(os.getcwd(),name)
            # ... try relative to cwd.
            # if not os.path.isfile(file_name): # If not relative to the LEMS file...
            #    file_name = os.path.join(os.getcwd(),'NeuroML2','results',name)
            # ... try relative to cwd in NeuroML2/results subdir.
            if not os.path.isfile(file_name):  # If not relative to the base dir...
                raise OSError(f"Could not find simulation output file {file_name}")

            format_ = of.attrib["format"]
            logger.info(f"Loading saved events from {file_name} (format: {format_})")

            selections = {}
            for col in of.findall(ns_prefix + "EventSelection"):
                id_ = int(col.attrib["id"])
                select = col.attrib["select"]
                events[select] = []
                selections[id_] = select

            with open(file_name) as f:
                for line in f:
                    values = line.split()
                    if format_ == "TIME_ID":
                        t = float(values[0])
                        id_ = int(values[1])
                    elif format_ == "ID_TIME":
                        id_ = int(values[0])
                        t = float(values[1])
                    logger.debug(
                        f"Found a event in cell {id_} ({selections[id_]}) at t = {t}"
                    )
                    events[selections[id_]].append(t)

            if remove_dat_files_after_load:
                logger.warning(
                    f"Removing file {file_name} after having loading its data!"
                )
                os.remove(file_name)
            all_events[name] = events

    if get_traces:
        output_files = sim.findall(ns_prefix + "OutputFile")
        for i, of in enumerate(output_files):
            traces: typing.Dict = {}
            traces["t"] = []
            name = of.attrib["fileName"]
            file_name = os.path.join(base_dir, name)

            if not os.path.isfile(file_name):  # If not relative to the LEMS file...
                file_name = os.path.join(base_lems_file_path, name)

            if not os.path.isfile(file_name):  # If not relative to the LEMS file...
                file_name = os.path.join(os.getcwd(), name)

                # ... try relative to cwd.
            if not os.path.isfile(file_name):  # If not relative to the LEMS file...
                file_name = os.path.join(os.getcwd(), "NeuroML2", "results", name)
                # ... try relative to cwd in NeuroML2/results subdir.
            if not os.path.isfile(file_name):  # If not relative to the LEMS file...
                raise OSError(f"Could not find simulation output file {file_name}")

            t_file_mod = datetime.fromtimestamp(os.path.getmtime(file_name))
            if t_file_mod < t_run:
                raise Exception(
                    f"Expected output file {file_name}s has not been modified since "
                    f"{t_file_mod} but the simulation was run later at {t_run}."
                )

            cols = []
            cols.append("t")
            for col in of.findall(ns_prefix + "OutputColumn"):
                quantity = col.attrib["quantity"]
                traces[quantity] = []
                cols.append(quantity)

            with open(file_name) as f:
                for line in f:
                    values = line.split()
                    for vi in range(len(values)):
                        traces[cols[vi]].append(float(values[vi]))

            if remove_dat_files_after_load:
                logger.warning(
                    f"Removing file {file_name}s after having loading its data!"
                )
                os.remove(file_name)

            all_traces[name] = traces

    if get_events and get_traces:
        return all_traces, all_events
    elif get_traces:
        return all_traces
    else:
        return all_events
