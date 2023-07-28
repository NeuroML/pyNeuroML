#!/usr/bin/env python3
"""
Module for working with NSG. See https://github.com/OpenSourceBrain/pynsgr

File: pyneuroml/nsgr/__init__.py

Copyright 2023 NeuroML contributors
"""


import logging
import pathlib
import shutil
import time
import typing
from zipfile import ZipFile

from pyneuroml.pynml import run_lems_with
from pyneuroml.utils import get_files_generated_after
from pynsgr.commands.nsgr_submit import nsgr_submit

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def run_on_nsg(
    engine: str,
    lems_file_name: str,
    nsg_sim_config: typing.Dict[typing.Any, typing.Any] = {},
    *engine_args: typing.Any,
    **engine_kwargs: typing.Any,
):
    """Run NeuroML/LEMS simulation on NSG.

    Since the versions of tools on NSG may differ from what you have installed
    locally, this method first generates the simulation engine specific files
    (runner script for NEURON and mod files, for example) for the provided
    engine, zips them up in "nsg_sim.zip", writes the config files, and then
    submits the job to NSG using pynsgr using the PY_EXPANSE configuration.

    Please ensure that you have set up an account and have your NSG
    configuration file populated as noted in pynsgr.

    - https://nsgr.sdsc.edu:8443/restusers/documentation
    - https://nsgr.sdsc.edu:8443/restusers/docs/tools

    Default the nsg_sim_config is, keys provided by the user in nsg_sim_config
    overwrite these:

    .. code:: python

        nsg_sim_config_dict = {
            "number_cores_": "1",
            "number_nodes_": "1",
            "tasks_per_node_": "1",
            "runtime_": "0.5",
            'toolId': "PY_EXPANSE",
            'nrnivmodl_o_': "1"
        }

    :param engine: name of engine: suffixes of the run_lems_with.. functions
    :param lems_file_name: name of LEMS simulation file
    :param nsg_sim_config: dict containing params and values that will be
        printed to testParam.properties
    :param *engine_args: positional args to be passed to the engine runner
        function
    :param **engine_kwargs: keyword args to be be passed to the engine runner
        function
    :returns: TODO
    """
    supported_engines = ["jneuroml_neuron", "jneuroml_netpyne"]
    if engine not in supported_engines:
        print(f"Engine {engine} is not currently supported on NSG")
        print(f"Supported engines are: {supported_engines}")
        return

    logger.debug(f"NSGR: engine is {engine}")

    zipfile_name = lems_file_name.replace(".xml", "") + "_NSG.zip"
    # default dictionary
    nsg_sim_config_dict = {
        "number_cores_": "1",
        "number_nodes_": "1",
        "tasks_per_node_": "1",
        "runtime_": "0.5",
        "toolId": "PY_EXPANSE",
        "nrnivmodl_o_": "1",
    }

    # update dict based on user values
    for key, val in nsg_sim_config.items():
        nsg_sim_config_dict[key] = val

    logger.info("Generating simulator specific files")
    start_time = time.time() - 1.0

    if engine == "jneuroml_neuron":
        run_lems_with(
            engine,
            lems_file_name=lems_file_name,
            compile_mods=False,
            only_generate_scripts=True,
            *engine_args,
            **engine_kwargs,
        )
    elif engine == "jneuroml_netpyne":
        run_lems_with(
            engine,
            lems_file_name=lems_file_name,
            compile_mods=False,
            only_generate_scripts=True,
            *engine_args,
            **engine_kwargs,
        )

    generated_files = get_files_generated_after(
        start_time, ignore_suffixes=["xml", "nml"]
    )
    logger.debug(f"Generated files are: {generated_files}")

    logger.info("Generating zip file")
    runner_file = ""
    # NSG requires that the top level directory exist
    logger.info("Creating directory and moving generated files to it")
    nsg_dir = pathlib.Path(zipfile_name.replace(".zip", ""))

    # remove it if it exists
    if nsg_dir.is_dir():
        shutil.rmtree(str(nsg_dir))
    nsg_dir.mkdir()

    with ZipFile(zipfile_name, "w") as archive:
        for f in generated_files:
            if engine == "jneuroml_neuron":
                if f.endswith("_nrn.py"):
                    runner_file = f
            elif engine == "jneuroml_netpyne":
                if f.endswith("_netpyne.py"):
                    runner_file = f
            fpath = pathlib.Path(f)
            moved_path = fpath.rename(nsg_dir / fpath)
            archive.write(str(moved_path))

    logger.debug("Printing testParam.properties")
    nsg_sim_config_dict["filename_"] = runner_file
    logger.debug(f"NSG sim config is: {nsg_sim_config_dict}")

    with open("testParam.properties", "w") as file:
        for key, val in nsg_sim_config_dict.items():
            print(f"{key}={val}", file=file)

    logger.debug("Printing testInput.properties")
    with open("testInput.properties", "w") as file:
        print(f"infile_=@./{zipfile_name}", file=file)

    print(f"{zipfile_name} generated")
    # uses argv, where the first argument is the script itself, so we must pass
    # something as the 0th index of the list
    if nsgr_submit(["", ".", "validate"]) == 0:
        print("Attempting to submit to NSGR")
        return nsgr_submit(["", ".", "run"])
