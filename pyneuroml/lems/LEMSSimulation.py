#!/usr/bin/env python
"""
Helper class for generating LEMS xml files for simulations
"""

import logging
import os
import os.path
import random
import typing
from typing import Optional

import airspeed
from neuroml import __version__ as libnml_ver

from pyneuroml import __version__ as pynml_ver
from pyneuroml.pynml import read_lems_file, read_neuroml2_file
from pyneuroml.utils.plot import get_next_hex_color
from pyneuroml.utils.units import convert_to_units

logger = logging.getLogger(__name__)


class LEMSSimulation:
    """
    Helper class for creating LEMS Simulations for running NeuroML2 models.
    """

    TEMPLATE_FILE = "%s/LEMS_TEMPLATE.xml" % (os.path.dirname(__file__))

    lems_info = {}  # type: dict[str, typing.Any]
    my_random = random.Random()

    def __init__(
        self,
        sim_id: str,
        duration: typing.Union[float, str],
        dt: typing.Union[float, str],
        target: typing.Optional[str] = None,
        comment: str = "\n\n        This LEMS file has been automatically generated using PyNeuroML v%s (libNeuroML v%s)\n\n    "
        % (pynml_ver, libnml_ver),
        lems_file_generate_seed: Optional[typing.Any] = None,
        simulation_seed: int = 12345,
        meta: typing.Optional[typing.Dict[str, str]] = None,
    ) -> None:
        """Init a new LEMSSimulation object.

        :param sim_id: id for simulation
        :type sim_id: str
        :param duration: duration of simulation. This can be:
            - a float of the magnitude in ms
            - a string of the magnitude in ms
            - a string of the value using any time units (that will be
              converted to ms)
        :type duration: float or str
        :param dt: simulation time step. This can be:
            - a float of the magnitude in ms
            - a string of the magnitude in ms
            - a string of the value using any time units (that will be
              converted to ms)
        :type dt: float or str
        :param target: id of target component (usually the network)
        :type target: str
        :param comment: comment to add to simulation file
        :type comment: str
        :param lems_file_generate_seed: a value to set for random number
            generation. This is used for things like setting random colours in
            plots. Setting the same value here ensures that all simulations
            with the same seed will use the same colours.

            This is not the seed to be used in the simulation. See
            `simulation_seed` for that.
        :type lems_file_generate_seed:
        :param simulation_seed: simulation seed to set to
        :type simulation_seed: int or str
        :param meta: dictionary to set Meta options.

            Currently, only supported for the Neuron simulator to use the CVODE
            solver. A dict needs to be passed:
            {
                "for": "neuron",
                "method": "cvode",
                "abs_tolerance" = "0.001",
                "rel_tolerance": "0.001"
            }

        :type meta: dict
        """

        if isinstance(duration, str):
            # is this just the magnitude in the string?
            try:
                duration_mag_ms = float(duration)
            except ValueError:
                duration_mag_ms = convert_to_units(duration, "ms")
        else:
            duration_mag_ms = float(duration)

        if isinstance(dt, str):
            # is this just the magnitude in the string?
            try:
                dt_mag_ms = float(dt)
            except ValueError:
                dt_mag_ms = convert_to_units(dt, "ms")
        else:
            dt_mag_ms = float(dt)

        self.lems_info["sim_id"] = sim_id
        self.lems_info["duration"] = duration_mag_ms
        self.lems_info["dt"] = dt_mag_ms
        self.lems_info["comment"] = comment
        self.lems_info["seed"] = int(simulation_seed)
        self.lems_info["report"] = ""

        self.lems_info["include_files"] = []
        self.lems_info["displays"] = []
        self.lems_info["output_files"] = []
        self.lems_info["event_output_files"] = []
        self.lems_info["meta"] = meta

        if target:
            self.lems_info["target"] = target

        if lems_file_generate_seed:
            self.my_random.seed(
                lems_file_generate_seed
            )  # To ensure same LEMS file (e.g. colours of plots) are generated every time for the same input
        else:
            self.my_random.seed(12345)

    def __setattr__(self, attr: typing.Any, value: typing.Any) -> None:
        """Set an attribute value.

        :param attr: attribute to set value of
        :type attr: Any
        :param value: value to set
        :type value: Any
        :returns: None
        :raises AttributeError: if provided attribute is not found in LEMSSimulation.
        """
        if attr in self.lems_info.keys():
            self.lems_info[attr] = value
        else:
            raise AttributeError("There is not a field: %s in LEMSSimulation" % attr)

    def assign_simulation_target(self, target: str) -> None:
        """Assign a simulation target.

        :param target: id of target component
        :type target: str
        :returns: None
        """
        self.lems_info["target"] = target

    def set_report_file(self, report_file_name: str) -> None:
        """Set a report file.

        The report file is a short file saved after simulation with run time, simulator version etc.

        :param report_file_name: name of report file
        :type report_file_name: str
        :returns: None
        """
        if report_file_name is not None:
            self.lems_info["report"] = ' reportFile="%s"' % report_file_name

    def include_neuroml2_file(
        self,
        nml2_file_name: str,
        include_included: bool = True,
        relative_to_dir: str = ".",
    ) -> None:
        """Include additional NeuroML2 file.

        This will only add the provided file if it has not already been
        included.

        :param nml2_file_name: name of NeuroML2 file to include
        :type nml2_file_name: str
        :param include_included: toggle to include any files included in the
            provided file
        :type include_included: bool
        :param relative_to_dir: directory relative to which the provided
            nml2_file_name is being provided
        :type relative_to_dir: str
        :returns: None
        """
        full_path = os.path.abspath(relative_to_dir + "/" + nml2_file_name)
        base_path = os.path.dirname(full_path)
        # logger.info_v("Including in generated LEMS file: %s (%s)"%(nml2_file_name, full_path))
        if nml2_file_name not in self.lems_info["include_files"]:
            self.lems_info["include_files"].append(nml2_file_name)

        if include_included:
            cell = read_neuroml2_file(full_path)
            for include in cell.includes:
                self.include_neuroml2_file(
                    include.href, include_included=True, relative_to_dir=base_path
                )

    def include_lems_file(
        self, lems_file_name: str, include_included: bool = True
    ) -> None:
        """Include additional LEMS file in the simulation.

        :param lems_file_name: name of LEMS file to include
        :type lems_file_name: str
        :param include_included: toggle to include files included by provided
            LEMS file
        :type include_included: bool
        :returns: None
        """
        if lems_file_name not in self.lems_info["include_files"]:
            self.lems_info["include_files"].append(lems_file_name)

        if include_included:
            model = read_lems_file(lems_file_name)
            for inc in model.included_files:
                self.lems_info["include_files"].append(inc)

    def create_display(
        self, id: str, title: str, ymin: str, ymax: str, timeScale: str = "1ms"
    ) -> None:
        """Create a new display

        :param id: id of display
        :type id: str
        :param title: title of display
        :type title: str
        :param ymin: min y value of display
        :type ymin: str
        :param ymax: max y value of display
        :type ymax: str
        :param timeScale: time scale of display
        :type timeScale: str
        :returns: None
        """
        disp = {}  # type: dict[str, typing.Any]
        self.lems_info["displays"].append(disp)
        disp["id"] = id
        disp["title"] = title
        disp["ymin"] = ymin
        disp["ymax"] = ymax
        disp["time_scale"] = timeScale
        disp["lines"] = []

    def create_output_file(self, id: str, file_name: str):
        """Create a new output file for storing values recorded for a
        simulation.

        For storing events, such as spikes, please see
        `create_event_output_file`.

        :param id: id of output file
        :type id: str
        :param file_name: name of output file
        :type file_name: str
        :returns: None
        """
        of = {}  # type: dict[str, typing.Any]
        self.lems_info["output_files"].append(of)
        of["id"] = id
        of["file_name"] = file_name
        of["columns"] = []

    def create_event_output_file(self, id, file_name, format="ID_TIME"):
        """Create a new output file for storing events recorded from
        simulations.

        For storing other outputs (not events), please see `create_output_file`
        instead.

        TODO: list what formats are available

        :param id: id of output file
        :type id: str
        :param file_name: name of output file
        :type file_name: str
        :param format: format of file
        :type format: str
        :returns: None
        """
        eof = {}
        self.lems_info["event_output_files"].append(eof)
        eof["id"] = id
        eof["file_name"] = file_name
        eof["format"] = format
        eof["selections"] = []

    def add_line_to_display(
        self,
        display_id: str,
        line_id: str,
        quantity: str,
        scale: str = "1",
        color: typing.Optional[str] = None,
        timeScale: str = "1ms",
    ) -> None:
        """Add a new line to the display

        :param display_id: id of display
        :type display_id: str
        :param line_id: id of line
        :type line_id: str
        :param quantity: name of quantity being represented
        :type quantitiy: str
        :param scale: scale of line
        :type scale: str
        :param color: color of line, randomly chosen if None
        :type color: str
        :param timeScale: scale of time axis
        :type timeScale: str
        :returns: None
        :raises ValueError: if provided `display_id` has not been created yet.
        """
        disp = None
        for d in self.lems_info["displays"]:
            if d["id"] == display_id:
                disp = d
        if not disp:
            raise ValueError(
                f"Display with id {display_id} not found. Please check the provided display_id, or create it first."
            )

        line = {}  # type: dict[str, typing.Any]
        disp["lines"].append(line)
        line["id"] = line_id
        line["quantity"] = quantity
        line["scale"] = scale
        line["color"] = color if color else get_next_hex_color(self.my_random)
        line["time_scale"] = timeScale

    def add_column_to_output_file(
        self, output_file_id: str, column_id: str, quantity: str
    ) -> None:
        """Add a column to the output file with id `output_file_id`

        :param output_file_id: id of output file (must be created first using
            `create_output_file`)
        :type output_file_id: str
        :param column_id: id of column to add
        :type column_id: str
        :param quantity: quantity to add
        :type quantity: str
        :returns: None
        :raises ValueError: if provided `output_file_id` has not been created yet.
        """
        of = None
        for o in self.lems_info["output_files"]:
            if o["id"] == output_file_id:
                of = o

        if not of:
            raise ValueError(
                f"Output file with id {output_file_id} not found.  Please check the provided output_file_id, or create it first."
            )

        column = {}  # type: dict[str, typing.Any]
        of["columns"].append(column)
        column["id"] = column_id
        column["quantity"] = quantity

    def add_selection_to_event_output_file(
        self, event_output_file_id: str, event_id: str, select: str, event_port: str
    ) -> None:
        """Add a column to the event output file with id
        `event_output_file_id`.

        :param event_output_file_id: id of output file (must be created first
            using `create_output_file`)
        :type event_output_file_id: str
        :param event_id: id of event to add
        :type event_id: str
        :param select: selection to add
        :type select: str
        :param event_port: event port to add
        :type event_port: str
        :returns: None
        :raises ValueError: if provided `event_output_file_id` has not been created yet.
        """
        eof = None
        for o in self.lems_info["event_output_files"]:
            if o["id"] == event_output_file_id:
                eof = o
        if not eof:
            raise ValueError(
                f"Output file with id {event_output_file_id} not found.  Please check the provided event_output_file_id, or create it first."
            )

        selection = {}  # type: dict[str, typing.Any]
        eof["selections"].append(selection)
        selection["id"] = event_id
        selection["select"] = select
        selection["event_port"] = event_port

    def to_xml(self) -> str:
        """Export simulation to XML.

        :returns: XML representation
        :rtype: str
        """
        templfile = self.TEMPLATE_FILE
        if not os.path.isfile(templfile):
            templfile = "." + templfile
        with open(templfile) as f:
            templ = airspeed.Template(f.read())
        return templ.merge(self.lems_info)

    def save_to_file(self, file_name: typing.Optional[str] = None):
        """Save LEMSSimulation to a file.

        :param file_name: name of file to store to.
            `LEMS_<some id string>.xml` is the suggested format. Leave empty
            to use `LEMS_<sim_id>.xml`
        :type file_name: str
        :returns: name of file
        :rtype: str
        """

        if file_name is None:
            file_name = "LEMS_%s.xml" % self.lems_info["sim_id"]

        logger.info(
            "Writing LEMS Simulation %s to file: %s..."
            % (self.lems_info["sim_id"], file_name)
        )
        with open(file_name, "w") as lems_file:
            lems_file.write(self.to_xml())
            lems_file.flush()
            os.fsync(lems_file.fileno())

        logger.info(
            "Written LEMS Simulation %s to file: %s"
            % (self.lems_info["sim_id"], file_name)
        )

        return file_name


# main method example moved to examples/create_new_lems_file.py
