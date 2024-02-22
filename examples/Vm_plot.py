"""

Example showing how to manually create a NeuroML network file which includes an existing NML2 file,
create a population for a cell in the file and add a current input. A LEMS file to run the network,
and plot the voltage of the cell is created. The simulation is then executed.

"""

import sys
import logging

from pyneuroml import pynml
from pyneuroml.lems.LEMSSimulation import LEMSSimulation
import neuroml as nml


logger = logging.getLogger(__name__)


def generate_Vm_vs_time_plot(
    nml2_file,
    cell_id,
    inj_amp_nA=80,
    delay_ms=20,
    inj_dur_ms=60,
    sim_dur_ms=100,
    dt=0.05,
    plot_voltage_traces=False,
    show_plot_already=True,
    simulator="jNeuroML",
    include_included=True,
):
    ref = "Test"
    logger.info(
        "Generating Vm(mV) vs Time(ms) plot for cell %s in %s using %s (Inj %snA / %sms dur after %sms delay)"
        % (cell_id, nml2_file, simulator, inj_amp_nA, inj_dur_ms, delay_ms)
    )

    sim_id = "Vm_%s" % ref
    duration = sim_dur_ms
    ls = LEMSSimulation(sim_id, sim_dur_ms, dt)

    ls.include_neuroml2_file(nml2_file, include_included=include_included)
    ls.assign_simulation_target("network")
    nml_doc = nml.NeuroMLDocument(id=cell_id)

    nml_doc.includes.append(nml.IncludeType(href=nml2_file))

    net = nml.Network(id="network")
    nml_doc.networks.append(net)

    input_id = "input_%s" % str(inj_amp_nA).replace(".", "_")
    pg = nml.PulseGenerator(
        id=input_id,
        delay="%sms" % delay_ms,
        duration="%sms" % inj_dur_ms,
        amplitude="%spA" % inj_amp_nA,
    )
    nml_doc.pulse_generators.append(pg)

    pop_id = "hhpop"
    pop = nml.Population(id=pop_id, component="hhcell", size=1, type="populationList")

    inst = nml.Instance(id=0)
    pop.instances.append(inst)
    inst.location = nml.Location(x=0, y=0, z=0)
    net.populations.append(pop)

    # Add these to cells
    input_list = nml.InputList(
        id="il_%s" % input_id, component=pg.id, populations=pop_id
    )
    input = nml.Input(id="0", target="../hhpop/0/hhcell", destination="synapses")

    input_list.input.append(input)
    net.input_lists.append(input_list)

    sim_file_name = "%s.sim.nml" % sim_id
    pynml.write_neuroml2_file(nml_doc, sim_file_name)
    ls.include_neuroml2_file(sim_file_name)

    disp0 = "Voltage_display"
    ls.create_display(disp0, "Voltages", "-90", "50")
    ls.add_line_to_display(disp0, "V", "hhpop/0/hhcell/v", scale="1mV")

    of0 = "Volts_file"
    ls.create_output_file(of0, "%s.v.dat" % sim_id)
    ls.add_column_to_output_file(of0, "V", "hhpop/0/hhcell/v")

    lems_file_name = ls.save_to_file()

    if simulator == "jNeuroML":
        results = pynml.run_lems_with_jneuroml(
            lems_file_name,
            nogui=True,
            load_saved_data=True,
            plot=plot_voltage_traces,
            show_plot_already=False,
        )
    elif simulator == "jNeuroML_NEURON":
        results = pynml.run_lems_with_jneuroml_neuron(
            lems_file_name,
            nogui=True,
            load_saved_data=True,
            plot=plot_voltage_traces,
            show_plot_already=False,
        )

    if show_plot_already:
        from matplotlib import pyplot as plt

        plt.show()

    return of0


nogui = "-nogui" in sys.argv  # Used to supress GUI in tests for Travis-CI


generate_Vm_vs_time_plot(
    "NML2_SingleCompHHCell.nml", "hhcell", plot_voltage_traces=not nogui
)
