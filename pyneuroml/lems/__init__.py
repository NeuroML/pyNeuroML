import logging
import os
import os.path
import random
import shutil
import typing

import neuroml
from lxml import etree

from pyneuroml.lems.LEMSSimulation import LEMSSimulation
from pyneuroml.pynml import read_neuroml2_file
from pyneuroml.utils.plot import get_next_hex_color

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def generate_lems_file_for_neuroml(
    sim_id: str,
    neuroml_file: str,
    target: str,
    duration: str,
    dt: str,
    lems_file_name: str,
    target_dir: str,
    nml_doc: typing.Optional[neuroml.NeuroMLDocument] = None,
    include_extra_files: typing.List[str] = [],
    gen_plots_for_all_v: bool = True,
    plot_all_segments: bool = False,
    gen_plots_for_quantities: typing.Dict[str, typing.List[str]] = {},
    gen_plots_for_only_populations: typing.List[str] = [],
    gen_saves_for_all_v: bool = True,
    save_all_segments: bool = False,
    gen_saves_for_only_populations: typing.List[str] = [],
    gen_saves_for_quantities: typing.Dict[str, typing.List[str]] = {},
    gen_spike_saves_for_all_somas: bool = False,
    gen_spike_saves_for_only_populations: typing.List[str] = [],
    gen_spike_saves_for_cells: typing.Dict[str, typing.List[str]] = {},
    spike_time_format: str = "ID_TIME",
    copy_neuroml: bool = True,
    report_file_name: typing.Optional[str] = None,
    lems_file_generate_seed: typing.Optional[int] = None,
    verbose: bool = False,
    simulation_seed: int = 12345,
) -> typing.Tuple[typing.List[str], LEMSSimulation]:
    """Generate a LEMS simulation file for a NeuroML model file. This wraps
    around the LEMSSimulation class and provides an easy interface for creating
    the LEMS simulation file.

    :param sim_id: simulation id
    :type sim_id: str
    :param neuroml_file: name/path to NeuroML file
    :type neuroml_file: str
    :param target: target element
    :type target: str
    :param duration: simulation duration
    :type duration: str
    :param dt: integration time step
    :type dt: str
    :param lems_file_name: name of LEMS file
    :type lems_file_name: str
    :param target_dir: directory to place LEMS file in
    :type target_dir: str
    :param nml_doc: NeuroMLDocument object containing model for simulation
        Useful if the NeuroML file has already been loaded as it prevents
        re-loading of the NeuroMLDocument from the file. If this is not
        provided, the provided NeuroML file will be assumed to be a
        NeuroMLDocument and loaded.
    :type nml_doc: neuroml.Document
    :param include_extra_files: list of extra files to include in the LEMS
        simulation file
    :type include_extra_files: list
    :param gen_plots_for_all_v: toggle generation of plots for all membrane
        potentials
    :type gen_plots_for_all_v: bool
    :param plot_all_segments: toggle whether values for all segments should be
        plotted
    :type plot_all_segments: bool
    :param gen_plots_for_quantities: dict of quantities to display
        the key is the "display" and the value will be the list of quantity
        paths
    :type gen_plots_for_quantities: dict
    :param gen_plots_for_only_populations: list of populations to limit
        plotting for, If the list is empty, all populations are considered.
    :type gen_plots_for_only_populations: list
    :param gen_saves_for_all_v: toggle whether data files should be saved for
        all membrane potentials
    :type gen_saves_for_all_v: bool
    :param save_all_segments: toggle whether data files should be saved for all
        segments
    :type save_all_segments: bool
    :param gen_saves_for_only_populations: list of populations to save data
        files for, if list is empty, all populations are considered
    :type gen_saves_for_only_populations: list of populations to save data
    :param gen_saves_for_quantities: dict of quantities to save data files for
        the key is the filename and the value will be the list of quantitiy
        paths to save to it
    :type gen_saves_for_quantities: dict
    :param gen_spike_saves_for_all_somas: toggle if spikes should be saved for
        all somas
    :type gen_spike_saves_for_all_somas: bool
    :param gen_spike_saves_for_only_populations: list of populations spikes
        should be saved in data files for
    :type gen_spike_saves_for_only_populations: list
    :param gen_spike_saves_for_cells: dict of cells to save spikes for
        the key is the name of the file and the value will be the list of
        quantitiy paths
    :type gen_spike_saves_for_cells: dict
    :param spike_time_format: spike time format
    :type spike_time_format: str
    :param copy_neuroml: toggle whether NeuroML files should be copied to
        target directory
    :type copy_neuroml: bool
    :param report_file_name: name of report file
    :type report_file_name: str
    :param lems_file_generate_seed: seed to use for LEMS file generation
    :type lems_file_generate_seed: int
    :param verbose: toggle verbosity
    :type verbose: bool
    :param simulation_seed: simulation seed
    :type simulation_seed: int
    """
    my_random = random.Random()
    if lems_file_generate_seed:
        my_random.seed(
            lems_file_generate_seed
        )  # To ensure same LEMS file (e.g. colours of plots) are generated every time for the same input
    else:
        my_random.seed(
            12345
        )  # To ensure same LEMS file (e.g. colours of plots) are generated every time for the same input

    file_name_full = "%s/%s" % (target_dir, lems_file_name)

    logger.info(
        "Creating LEMS file at: %s for NeuroML 2 file: %s (copy: %s)"
        % (file_name_full, neuroml_file, copy_neuroml)
    )

    ls = LEMSSimulation(sim_id, duration, dt, target, simulation_seed=simulation_seed)

    if nml_doc is None:
        nml_doc = read_neuroml2_file(
            neuroml_file, include_includes=True, verbose=verbose
        )
        nml_doc_inc_not_included = read_neuroml2_file(
            neuroml_file, include_includes=False, verbose=False
        )
    else:
        nml_doc_inc_not_included = nml_doc

    ls.set_report_file(report_file_name)

    quantities_saved = []

    for f in include_extra_files:
        ls.include_neuroml2_file(f, include_included=False)

    if not copy_neuroml:
        rel_nml_file = os.path.relpath(
            os.path.abspath(neuroml_file), os.path.abspath(target_dir)
        )
        logging.info(
            "Including existing NeuroML file (%s) as: %s" % (neuroml_file, rel_nml_file)
        )
        ls.include_neuroml2_file(
            rel_nml_file,
            include_included=True,
            relative_to_dir=os.path.abspath(target_dir),
        )
    else:
        logging.info(
            "Copying a NeuroML file (%s) to: %s (abs path: %s)"
            % (neuroml_file, target_dir, os.path.abspath(target_dir))
        )

        if not os.path.isdir(target_dir):
            raise Exception("Target directory %s does not exist!" % target_dir)

        if os.path.realpath(os.path.dirname(neuroml_file)) != os.path.realpath(
            target_dir
        ):
            shutil.copy(neuroml_file, target_dir)
        else:
            logging.info("No need, same file...")

        neuroml_file_name = os.path.basename(neuroml_file)

        ls.include_neuroml2_file(neuroml_file_name, include_included=False)

        nml_dir = (
            os.path.dirname(neuroml_file)
            if len(os.path.dirname(neuroml_file)) > 0
            else "."
        )

        for include in nml_doc_inc_not_included.includes:
            if nml_dir == "." and os.path.isfile(include.href):
                incl_curr = include.href
            else:
                incl_curr = "%s/%s" % (nml_dir, include.href)

            if os.path.isfile(include.href):
                incl_curr = include.href

            logger.info(
                " - Including %s (located at %s; nml dir: %s), copying to %s"
                % (include.href, incl_curr, nml_dir, target_dir)
            )

            """
            if not os.path.isfile("%s/%s" % (target_dir, os.path.basename(incl_curr))) and \
               not os.path.isfile("%s/%s" % (target_dir, incl_curr)) and \
               not os.path.isfile(incl_curr):
                shutil.copy(incl_curr, target_dir)
            else:
                logger.info("No need to copy...")"""

            f1 = "%s/%s" % (target_dir, os.path.basename(incl_curr))
            f2 = "%s/%s" % (target_dir, incl_curr)
            if os.path.isfile(f1):
                logging.info("No need to copy, file exists: %s..." % f1)
            elif os.path.isfile(f2):
                logging.info("No need to copy, file exists: %s..." % f2)
            else:
                shutil.copy(incl_curr, target_dir)

            ls.include_neuroml2_file(include.href, include_included=False)
            try:
                sub_doc = read_neuroml2_file(incl_curr)
                sub_dir = (
                    os.path.dirname(incl_curr)
                    if len(os.path.dirname(incl_curr)) > 0
                    else "."
                )

                if sub_doc.__class__ == neuroml.nml.nml.NeuroMLDocument:
                    for include in sub_doc.includes:
                        incl_curr = "%s/%s" % (sub_dir, include.href)
                        logger.info(
                            " -- Including %s located at %s" % (include.href, incl_curr)
                        )

                        if not os.path.isfile(
                            "%s/%s" % (target_dir, os.path.basename(incl_curr))
                        ) and not os.path.isfile("%s/%s" % (target_dir, incl_curr)):
                            shutil.copy(incl_curr, target_dir)
                            ls.include_neuroml2_file(
                                include.href, include_included=False
                            )
            except TypeError:
                logging.info(
                    "File: %s is not a NeuroML file, but it may be LEMS, ignoring..."
                    % incl_curr
                )

    if (
        gen_plots_for_all_v
        or gen_saves_for_all_v
        or len(gen_plots_for_only_populations) > 0
        or len(gen_saves_for_only_populations) > 0
        or gen_spike_saves_for_all_somas
        or len(gen_spike_saves_for_only_populations) > 0
    ):
        for network in nml_doc.networks:
            for population in network.populations:
                variable = "v"
                quantity_template_e = "%s[%i]"

                component = population.component
                size = population.size
                cell = None
                segment_ids = []

                for c in nml_doc.spike_generator_poissons:
                    if c.id == component:
                        variable = "tsince"
                for c in nml_doc.SpikeSourcePoisson:
                    if c.id == component:
                        variable = "tsince"

                quantity_template = "%s[%i]/" + variable
                if plot_all_segments or gen_spike_saves_for_all_somas:
                    for c in nml_doc.cells:
                        if c.id == component:
                            cell = c
                            for segment in cell.morphology.segments:
                                segment_ids.append(segment.id)
                            segment_ids.sort()

                if population.type and population.type == "populationList":
                    quantity_template = "%s/%i/" + component + "/" + variable
                    quantity_template_e = "%s/%i/" + component + ""
                    #  Multicompartmental cell
                    #  Needs to be supported in NeuronWriter
                    # if len(segment_ids)>1:
                    #     quantity_template_e = "%s/%i/"+component+"/0"
                    size = len(population.instances)

                if (
                    gen_plots_for_all_v
                    or population.id in gen_plots_for_only_populations
                ):
                    logger.info(
                        "Generating %i plots for %s in population %s"
                        % (size, component, population.id)
                    )

                    disp0 = "DispPop__%s" % population.id
                    ls.create_display(
                        disp0,
                        "Membrane potentials of cells in %s" % population.id,
                        "-90",
                        "50",
                    )

                    for i in range(size):
                        if cell is not None and plot_all_segments:
                            quantity_template_seg = "%s/%i/" + component + "/%i/v"
                            for segment_id in segment_ids:
                                quantity = quantity_template_seg % (
                                    population.id,
                                    i,
                                    segment_id,
                                )
                                ls.add_line_to_display(
                                    disp0,
                                    "%s[%i] seg %i: v" % (population.id, i, segment_id),
                                    quantity,
                                    "1mV",
                                    get_next_hex_color(my_random),
                                )
                        else:
                            quantity = quantity_template % (population.id, i)
                            ls.add_line_to_display(
                                disp0,
                                "%s[%i]: v" % (population.id, i),
                                quantity,
                                "1mV",
                                get_next_hex_color(my_random),
                            )

                if (
                    gen_saves_for_all_v
                    or population.id in gen_saves_for_only_populations
                ):
                    logger.info(
                        "Saving %i values of %s for %s in population %s"
                        % (size, variable, component, population.id)
                    )

                    of0 = "Volts_file__%s" % population.id
                    ls.create_output_file(
                        of0, "%s.%s.%s.dat" % (sim_id, population.id, variable)
                    )
                    for i in range(size):
                        if cell is not None and save_all_segments:
                            quantity_template_seg = "%s/%i/" + component + "/%i/v"
                            for segment_id in segment_ids:
                                quantity = quantity_template_seg % (
                                    population.id,
                                    i,
                                    segment_id,
                                )
                                ls.add_column_to_output_file(
                                    of0, "v_%s" % safe_variable(quantity), quantity
                                )
                                quantities_saved.append(quantity)
                        else:
                            quantity = quantity_template % (population.id, i)
                            ls.add_column_to_output_file(
                                of0, "v_%s" % safe_variable(quantity), quantity
                            )
                            quantities_saved.append(quantity)

                if (
                    gen_spike_saves_for_all_somas
                    or population.id in gen_spike_saves_for_only_populations
                ):
                    logger.info(
                        "Saving spikes in %i somas for %s in population %s"
                        % (size, component, population.id)
                    )

                    eof0 = "Spikes_file__%s" % population.id
                    ls.create_event_output_file(
                        eof0,
                        "%s.%s.spikes" % (sim_id, population.id),
                        format=spike_time_format,
                    )
                    for i in range(size):
                        quantity = quantity_template_e % (population.id, i)
                        ls.add_selection_to_event_output_file(
                            eof0, i, quantity, "spike"
                        )
                        quantities_saved.append(quantity)

    for display in sorted(gen_plots_for_quantities.keys()):
        quantities = gen_plots_for_quantities[display]
        max_ = "1"
        min_ = "-1"
        scale = "1"

        # Check for v ...
        if quantities and len(quantities) > 0 and quantities[0].endswith("/v"):
            max_ = "40"
            min_ = "-80"
            scale = "1mV"

        ls.create_display(display, "Plots of %s" % display, min_, max_)
        for q in quantities:
            ls.add_line_to_display(
                display, safe_variable(q), q, scale, get_next_hex_color(my_random)
            )

    for file_name in sorted(gen_saves_for_quantities.keys()):
        quantities = gen_saves_for_quantities[file_name]
        of_id = safe_variable(file_name)
        ls.create_output_file(of_id, file_name)
        for q in quantities:
            ls.add_column_to_output_file(of_id, safe_variable(q), q)
            quantities_saved.append(q)

    for file_name in sorted(gen_spike_saves_for_cells.keys()):
        quantities = gen_spike_saves_for_cells[file_name]
        of_id = safe_variable(file_name)
        ls.create_event_output_file(of_id, file_name)
        pop_here = None
        for i, quantity in enumerate(quantities):
            pop, index = get_pop_index(quantity)
            if pop_here:
                if pop_here != pop:
                    raise Exception(
                        "Problem with generating LEMS for saving spikes for file %s.\n"
                        % file_name
                        + "Multiple cells from different populations in one file will cause issues with index/spike id."
                    )
            pop_here = pop
            # print('===== Adding to %s (%s) event %i for %s, pop: %s, i: %s' % (file_name, of_id, i, quantity, pop, index))
            ls.add_selection_to_event_output_file(of_id, index, quantity, "spike")
            quantities_saved.append(quantity)

    ls.save_to_file(file_name=file_name_full)
    return quantities_saved, ls


# Mainly for NEURON etc.
def safe_variable(quantity):
    """Make a variable safe.

    It replaces `[`, `]`, `/`, `.` with `_`.

    :param quantity: quantitiy to make safe
    :param quantity: str
    :returns: quantity after it was made safe
    :rtype: str
    """
    return (
        quantity.replace(" ", "_")
        .replace("[", "_")
        .replace("]", "_")
        .replace("/", "_")
        .replace(".", "_")
    )


def get_pop_index(quantity):
    if "[" in quantity:
        s = quantity.split("[")
        pop = s[0]
        index = int(s[1][:-1])
        return pop, index
    else:
        s = quantity.split("/")
        pop = s[0]
        index = int(s[1])
        return pop, index


def load_sim_data_from_lems_file(
    lems_file_name: str,
    base_dir: str = ".",
    get_events: bool = True,
    get_traces: bool = True,
) -> typing.Optional[typing.Union[typing.Tuple[typing.Dict, typing.Dict], typing.Dict]]:
    """Load simulation outputs using the LEMS simulation file

    .. versionadded:: 1.2.2

    :param lems_file_name: name of LEMS file that was used to generate the data
    :type lems_file_name: str
    :param base_dir: directory to run in
    :type base_dir: str
    :returns: if both `get_events` and `get_traces` are selected, a tuple with
        two dictionaries, one for traces, one for events, is returned.

        Otherwise one dictionary for whichever was selected.

        The events dictionary has the following format:

        .. code-block:: python

            {
                '<value of select attribute>': { 'cell id': [<events>] }
            }

        The traces dictionary has the following format:

        .. code-block:: python

            {
                't': [<values>],
                'col 1': [<values>]
                'col 2': [<values>]
            }

    :raises ValueError: if neither traces nor events are selected for loading
    :raises ValueError: if no traces are found
    :raises ValueError: if no events are found

    """
    if not os.path.isfile(lems_file_name):
        real_lems_file = os.path.realpath(os.path.join(base_dir, lems_file_name))
    else:
        real_lems_file = os.path.realpath(lems_file_name)

    if not get_events and not get_traces:
        raise ValueError("One of events or traces must be True")

    logger.debug(
        "Reloading data specified in LEMS file: %s (%s), base_dir: %s, cwd: %s;"
        % (lems_file_name, real_lems_file, base_dir, os.getcwd())
    )

    # Could use pylems to parse all this...
    traces = {}  # type: dict
    events = {}  # type: dict

    base_lems_file_path = os.path.dirname(os.path.realpath(lems_file_name))
    tree = etree.parse(real_lems_file)

    sim = tree.getroot().find("Simulation")
    ns_prefix = ""

    possible_prefixes = ["{http://www.neuroml.org/lems/0.7.2}"]
    if sim is None:
        for pre in possible_prefixes:
            for comp in tree.getroot().findall(pre + "Component"):
                if comp.attrib["type"] == "Simulation":
                    ns_prefix = pre
                    sim = comp

    if get_events:
        event_output_files = sim.findall(ns_prefix + "EventOutputFile")
        for i, of in enumerate(event_output_files):
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
                raise OSError(
                    ("Could not find simulation output " "file %s" % file_name)
                )
            format_ = of.attrib["format"]
            logger.info(
                "Loading saved events from %s (format: %s)" % (file_name, format_)
            )
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
                    if id_ in selections:
                        logger.debug(
                            "Found a event in cell %s (%s) at t = %s"
                            % (id_, selections[id_], t)
                        )
                        events[selections[id_]].append(t)

                    else:
                        logger.warning("ID %s not found in selections dictionary" % id_)
                        continue  # skip this event

    if get_traces:
        output_files = sim.findall(ns_prefix + "OutputFile")

        for i, of in enumerate(output_files):
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
                raise OSError(
                    ("Could not find simulation output " "file %s" % file_name)
                )

            logger.info("Loading traces from %s" % (file_name))
            cols = []
            cols.append("t")
            for col in of.findall(ns_prefix + "OutputColumn"):
                quantity = col.attrib["quantity"]
                traces[quantity] = []
                cols.append(quantity)

            # TODO: could be quicker using numpy etc?
            with open(file_name) as f:
                for line in f:
                    values = line.split()
                    for vi in range(len(values)):
                        traces[cols[vi]].append(float(values[vi]))

    if get_events is True and get_traces is True:
        if len(events) == 0:
            raise ValueError("No events found")
        if len(traces) == 0:
            raise ValueError("No traces found")
        logger.debug("Returning both traces and events")
        return traces, events
    else:
        if get_events is True:
            if len(events) == 0:
                raise ValueError("No events found")
            logger.debug("Returning events")
            return events
        elif get_traces is True:
            if len(traces) == 0:
                raise ValueError("No traces found")
            logger.debug("Returning traces")
            return traces
    return None
