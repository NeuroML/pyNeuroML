import os.path
from pyneuroml.lems.LEMSSimulation import LEMSSimulation

import shutil
import os
import logging
from pyneuroml.pynml import read_neuroml2_file
from pyneuroml.utils.plot import get_next_hex_color
import random
import neuroml


logger = logging.getLogger(__name__)


def generate_lems_file_for_neuroml(
    sim_id,
    neuroml_file,
    target,
    duration,
    dt,
    lems_file_name,
    target_dir,
    nml_doc=None,  # Use this if the nml doc has already been loaded (to avoid delay in reload)
    include_extra_files=[],
    gen_plots_for_all_v=True,
    plot_all_segments=False,
    gen_plots_for_quantities={},  # Dict with displays vs lists of quantity paths
    gen_plots_for_only_populations=[],  # List of populations, all pops if=[]
    gen_saves_for_all_v=True,
    save_all_segments=False,
    gen_saves_for_only_populations=[],  # List of populations, all pops if=[]
    gen_saves_for_quantities={},  # Dict with file names vs lists of quantity paths
    gen_spike_saves_for_all_somas=False,
    gen_spike_saves_for_only_populations=[],  # List of populations, all pops if=[]
    gen_spike_saves_for_cells={},  # Dict with file names vs lists of quantity paths
    spike_time_format="ID_TIME",
    copy_neuroml=True,
    report_file_name=None,
    lems_file_generate_seed=None,
    verbose=False,
    simulation_seed=12345,
):

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
