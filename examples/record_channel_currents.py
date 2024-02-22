"""

Example to create a LEMS file for running a NML2 model & recording all channel currents

"""

from pyneuroml.lems import generate_lems_file_for_neuroml
from pyneuroml.pynml import read_neuroml2_file
from pyneuroml.pynml import get_value_in_si
import neuroml
import neuroml.writers as writers
import pprint

pp = pprint.PrettyPrinter(depth=6)


if __name__ == "__main__":
    root_dir = "test_data/ca1"
    cell_file = "cells/olm.cell.nml"
    cell_comp = "olmcell"
    reference = "TestOLMChannels"

    nml_doc = neuroml.NeuroMLDocument(id=reference)

    incl = neuroml.IncludeType(cell_file)
    nml_doc.includes.append(incl)

    net = neuroml.Network(id=reference)
    net.notes = "A test network model: %s" % reference
    net.temperature = "35degC"

    nml_doc.networks.append(net)

    pop = neuroml.Population(
        id="%sPop" % cell_comp, component=cell_comp, size=1, type="populationList"
    )

    inst = neuroml.Instance(id=0)
    pop.instances.append(inst)
    inst.location = neuroml.Location(x=0, y=0, z=0)

    net.populations.append(pop)

    pg = neuroml.PulseGenerator(
        id="pulseGen0", delay="100ms", duration="800ms", amplitude="28 pA"
    )

    nml_doc.pulse_generators.append(pg)

    input_list = neuroml.InputList(id="il", component=pg.id, populations=pop.id)

    input = neuroml.Input(
        id=0,
        target="../%s/%i/%s" % (pop.id, 0, cell_comp),
        segment_id=3,  # dend tip...
        destination="synapses",
    )

    input_list.input.append(input)
    net.input_lists.append(input_list)

    nml_file = "%s/%s.net.nml" % (root_dir, reference)
    writers.NeuroMLWriter.write(nml_doc, nml_file)

    print("Written network file to: " + nml_file)

    ############################################
    #  Create the LEMS file with helper method
    sim_id = "Sim%s" % reference
    target = net.id
    duration = 1000
    dt = 0.025
    lems_file_name = "LEMS_%s.xml" % sim_id
    target_dir = root_dir

    cell = read_neuroml2_file("%s/%s" % (root_dir, cell_file)).cells[0]
    print("Extracting channel info from %s" % cell.id)
    gen_plots_for_quantities = {}
    gen_saves_for_quantities = {}

    vs = "MembranePotentials"
    v_dat = "MembranePotentials.dat"

    all_vs = []
    gen_plots_for_quantities[vs] = all_vs
    gen_saves_for_quantities[v_dat] = all_vs

    for seg in cell.morphology.segments:
        v_quantity = "%s/0/%s/%s/v" % (pop.id, cell_comp, seg.id)
        all_vs.append(v_quantity)

    if isinstance(cell, neuroml.Cell2CaPools):
        cds = (
            cell.biophysical_properties2_ca_pools.membrane_properties2_ca_pools.channel_densities
            + cell.biophysical_properties2_ca_pools.membrane_properties2_ca_pools.channel_density_nernsts
        )
    elif isinstance(cell, neuroml.Cell):
        cds = (
            cell.biophysical_properties.membrane_properties.channel_densities
            + cell.biophysical_properties.membrane_properties.channel_density_nernsts
        )

    all_currents = []
    gen_plots_for_quantities["Allcurrents"] = all_currents

    for cd in cds:
        dens_si = get_value_in_si(cd.cond_density)
        group = cd.segment_groups if cd.segment_groups else "all"
        segs_here = cell.get_all_segments_in_group(group)
        print(
            "cd: %s, ion_channel: %s, ion: %s, density: %s (SI: %s), segs: %s"
            % (cd.id, cd.ion_channel, cd.ion, cd.cond_density, dens_si, segs_here)
        )
        for seg_id in segs_here:
            quantity = "%s/0/%s/%s/biophys/membraneProperties/%s/iDensity" % (
                pop.id,
                cell_comp,
                seg_id,
                cd.id,
            )
            all_currents.append(quantity)
            chan_curr_file = "%s_%s_seg%s.dat" % (cd.id, cd.ion, seg_id)
            gen_saves_for_quantities[chan_curr_file] = [quantity]

    generate_lems_file_for_neuroml(
        sim_id,
        nml_file,
        target,
        duration,
        dt,
        lems_file_name,
        target_dir,
        include_extra_files=[],
        gen_plots_for_all_v=False,
        plot_all_segments=False,
        gen_plots_for_quantities=gen_plots_for_quantities,  # Dict with displays vs lists of quantity paths
        gen_plots_for_only_populations=[],  # List of populations, all pops if = []
        gen_saves_for_all_v=False,
        save_all_segments=False,
        gen_saves_for_only_populations=[],  # List of populations, all pops if = []
        gen_saves_for_quantities=gen_saves_for_quantities,  # Dict with file names vs lists of quantity paths
        gen_spike_saves_for_all_somas=False,
        report_file_name="report.txt",
        copy_neuroml=False,
        verbose=False,
    )
