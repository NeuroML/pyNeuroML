#!/usr/bin/env python3
"""
Functions related to Biosimulations.org

File: pyneuroml/biosimulations.py

Copyright 2024 NeuroML contributors
"""

import logging
import typing
from datetime import datetime

import requests

from pyneuroml import __version__
from pyneuroml.annotations import create_annotation
from pyneuroml.archive import create_combine_archive
from pyneuroml.runners import run_jneuroml

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

try:
    from pydantic import BaseModel
    from requests_toolbelt.multipart.encoder import MultipartEncoder
except ImportError:
    logger.warning(
        "Please install optional dependencies to use Biosimulation.org features:"
    )
    logger.warning("pip install pyneuroml[combine]")


biosimulators_api_url = "https://api.biosimulators.org"
biosimulations_api_url = "https://api.biosimulations.org"


class _SimulationRunApiRequest(BaseModel):
    """class for runSimulation data

    Based on
    https://github.com/biosimulations/biosimulations-runutils/blob/dev/biosimulations_runutils/biosim_pipeline/biosim_api.py

    Once biosimulations-runutils is published, we will use their API instead
    of replicating it ourselves.
    """

    name: str
    simulator: str
    simulatorVersion: str
    maxTime: int
    cpus: typing.Optional[int] = None
    memory: typing.Optional[int] = None
    purpose: typing.Optional[str] = "academic"
    email: typing.Optional[str] = None
    envVars: typing.Optional[typing.List[str]] = []


def get_simulator_versions(
    simulators: typing.Union[str, typing.List[str]] = [
        "neuron",
        "netpyne",
        "tellurium",
        "pyneuroml",
        "pyneuroml",
        "xpp",
        "brian2",
        "copasi",
    ],
) -> typing.Dict[str, typing.List[str]]:
    """Get simulator list from biosimulators.

    .. versionadded:: 1.2.10

    :param simulators: a simulator or list of simulators to get versions for
    :type simulators: str or list(str)
    :returns: json response from API
    :rtype: str
    """
    if isinstance(simulators, str):
        simulators = [simulators]
    all_siminfo = {}  # type: typing.Dict[str, typing.List[str]]
    for sim in simulators:
        resp = requests.get(f"{biosimulators_api_url}/simulators/{sim}")
        siminfo = resp.json()
        for s in siminfo:
            try:
                all_siminfo[s["id"]].append(s["version"])
            except KeyError:
                all_siminfo[s["id"]] = [s["version"]]

    return all_siminfo


def submit_simulation(
    rootfile: str,
    metadata_file: typing.Optional[str] = None,
    sim_dict: typing.Dict[
        str, typing.Optional[typing.Union[int, str, typing.List[typing.Any]]]
    ] = {},
    dry_run: bool = True,
):
    """Submit a simulation to Biosimulations using its REST API

    .. versionadded:: 1.2.10

    :param rootfile: main LEMS or SEDML simulation file
        If it is a LEMS file, a SEDML file will be generated for it
    :type rootfile: str
    :param metadata_file: path to a RDF metadata file to be included in the
        OMEX archive.  If not provided, a generic one with a title and
        description will be generated.
    :type metadata_file: str
    :param sim_dict: dictionary holding parameters required to send the
        simulation to biosimulations

        .. code-block:: json

            {
              "name": "Kockout of gene A",
              "simulator": "tellurium",
              "simulatorVersion": "2.2.1",
              "cpus": 1,
              "memory": 8,
              "maxTime": 20,
              "envVars": [],
              "purpose": "academic",
              "email": "info@biosimulations.org",
            }

        Here, the "name", "simulator", and "simulatorVersion" fields are
        required. You can use the py::func`get_simulator_versions` function to
        query Biosimulations or visit https://biosimulators.org/simulators

        See also: "SimulationRun" on this page (at the bottom)
        https://api.biosimulations.org/#/Simulations/SimulationRunController_createRun

    :type sim_dict: dict

    :returns: the requests.post response object from the submission, or True if dry_run

    """
    if metadata_file is None:
        logger.info("No metadata file given, generating one.")
        metadata_file = "metadata.rdf"
        with open(metadata_file, "w") as f:
            annotation = create_annotation(
                rootfile + ".omex",
                title=f"Biosimulation of {rootfile} created using PyNeuroML version {__version__}",
                description=f"Biosimulation of {rootfile} created using PyNeuroML version {__version__}",
                creation_date=datetime.now().strftime("%Y-%m-%d"),
            )
            print(annotation, file=f)

    if rootfile.startswith("LEMS") and rootfile.endswith(".xml"):
        logger.info("Generating SED-ML file from LEMS file")
        run_jneuroml("", rootfile, "-sedml")
        rootfile = rootfile.replace(".xml", ".sedml")

    create_combine_archive(
        rootfile, zipfile_extension=".omex", extra_files=[metadata_file]
    )

    return submit_simulation_archive(f"{rootfile}.omex", sim_dict, dry_run=dry_run)


def submit_simulation_archive(
    archive_file: str,
    sim_dict: typing.Dict[str, typing.Union[int, str, typing.List[str]]] = {},
    dry_run: bool = False,
) -> object:
    """Submit an OMEX archive to biosimulations using the provided simulation run dictionary

    .. versionadded:: 1.2.10

    Note that this function does not validate either the OMEX archive nor the
    simulation dictionary. It simply submits it to the API.

    :param archive_file: OMEX archive file to submit
    :type archive_file: str
    :param sim_dict: dictionary holding parameters required to send the
        simulation to biosimulations

        .. code-block:: json

            {
              "name": "Kockout of gene A",
              "simulator": "tellurium",
              "simulatorVersion": "2.2.1",
              "cpus": 1,
              "memory": 8,
              "maxTime": 20,
              "envVars": [],
              "purpose": "academic",
              "email": "info@biosimulations.org",
            }

        Here, the "name", "simulator", and "simulatorVersion" fields are
        required. You can use the py::func`get_simulator_versions` function to
        query Biosimulations or visit https://biosimulators.org/simulators

        See also: "SimulationRun" on this page (at the bottom)
        https://api.biosimulations.org/#/Simulations/SimulationRunController_createRun

    :type sim_dict: dict
    :returns: the requests.post response object, or True if dry_run

    """
    api_url = f"{biosimulations_api_url}/runs"
    logger.debug(f"Sim dict is: {sim_dict}")

    simulation_run_request = _SimulationRunApiRequest(**sim_dict)
    logger.debug(
        f"simulation_run_request is {simulation_run_request.model_dump_json()}"
    )

    with open(archive_file, "rb") as archive_file_handle:
        multipart_form_data: dict[
            str,
            typing.Union[typing.Tuple[str, typing.BinaryIO], typing.Tuple[None, str]],
        ] = {
            "file": (archive_file, archive_file_handle),
            "simulationRun": (None, simulation_run_request.model_dump_json()),
        }

        logger.debug(f"data is:\n{multipart_form_data}")

        m = MultipartEncoder(fields=multipart_form_data)

        logger.info(f"multipart encoded data is {m}")
        logger.info(f"with content type: {m.content_type}")

        if dry_run is False:
            logger.info("Submitting archive to biosimulations")
            response = requests.post(
                api_url, data=m, headers={"Content-Type": m.content_type}
            )  # type: requests.Response
            if response.status_code != requests.codes.CREATED:
                response.raise_for_status()
            else:
                serv_response = response.json()
                print(
                    f"Submitted {archive_file} successfully with id: {serv_response['id']}"
                )
                print(f"View: {biosimulations_api_url}/runs/{serv_response['id']}")
                print(
                    f"Downloads: {biosimulations_api_url}/results/{serv_response['id']}/download"
                )
                print(
                    f"Logs: {biosimulations_api_url}/logs/{serv_response['id']}?includeOutput=true"
                )
        else:
            response = True
            print("Dry run, not submitting")
            print(f"Simulation dictionary: {sim_dict}")

    return response
