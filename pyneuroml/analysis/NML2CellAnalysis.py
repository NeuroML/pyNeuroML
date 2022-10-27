#!/usr/bin/env python3
"""
Utils to analyse a neuronal cell.

File: pyneuroml/analysis/NML2CellAnalysis.py

Copyright 2022 NeuroML contributors
"""


import typing
import numpy
import neuroml
from neuroml.utils import component_factory
from pyneuroml.lems import LEMSSimulation
import neuroml.writers as writers
from pyneuroml import pynml


def analyse_point_neuron(
    nml_cell: typing.Union[
        neuroml.IafTauCell,
        neuroml.IafTauRefCell,
        neuroml.IafCell,
        neuroml.IzhikevichCell,
        neuroml.Izhikevich2007Cell,
        neuroml.AdExIaFCell,
        neuroml.FitzHughNagumo1969Cell,
        neuroml.FitzHughNagumoCell,
        neuroml.PinskyRinzelCA3Cell,
    ],
    min_amplitude: float = 0.01,
    max_amplitude: float = 0.1,
    num_amplitudes: int = 5,
    duration: float = 2000,
    dt: float = 0.1,
    pulse_duration: float = 1500,
    pulse_delay: float = 200,
    plot: bool = True,
):
    """Analyse a NeuroML point neuron model.

    This method adds the cell to a network, and simulates it with a range of
    input currents to get its input-firing rate response profile.

    Note that the cell needs to be complete.

    This uses the reference jLEMS simulator to simulate the test models.

    :param nml_cell: cell to analyse
    :type nml_cell: abstract single neuron models
    :param min_amplitude: minimum current amplitude value in nA
    :type min_amplitude: float
    :param max_amplitude: maximum current amplitude in nA
    :type max_amplitude: float
    :param num_amplitudes: number of amplitude points
    :type num_amplitudes: int
    :param duration: duration of test simulations in ms
    :type duration: float
    :param dt: dt to use, in ms
    :type dt: float
    :param pulse_duration: duration of pulse, in ms
    :type pulse_duration: float
    :param pulse_delay: delay for pulse, in ms
    :type pulse_delay: float
    :param plot: toggle plotting
    :type plot: bool
    :returns: dict
        { 'amplitude': { 'v': [[time], [memb potential]], 'spikes': [spike times] }}
    """
    data_array = {}  # type: dict[str, dict[str, typing.Any]]
    amps = numpy.linspace(min_amplitude, max_amplitude, num_amplitudes)
    nml_cell.validate(recursive=True)
    amplitudes = [f"{amp}nA" for amp in amps]

    for amp in amplitudes:
        data_array[amp] = {}
        nml_doc = component_factory(neuroml.NeuroMLDocument, id="Test")
        nml_doc.add(nml_cell)

        net = nml_doc.add(neuroml.Network, id="TestNet", validate=False)
        pop = net.add(neuroml.Population, id="TestPop", component=nml_cell.id, size="1")

        pg = nml_doc.add(
            "PulseGenerator",
            id="pulseGen_0",
            delay=f"{pulse_delay} ms",
            duration=f"{pulse_duration} ms",
            amplitude=amp,
        )
        net.add("ExplicitInput", target="%s[%i]" % (pop.id, 0), input=pg.id)

        nml_doc.validate(recursive=True)

        nml_file = f"cell_test_{amp}.nml"
        writers.NeuroMLWriter.write(nml_doc, nml_file)

        simulation_id = f"cell_test_{amp}"
        simulation = LEMSSimulation(
            sim_id=simulation_id, duration=1000, dt=0.1, simulation_seed=123
        )
        simulation.assign_simulation_target(net.id)
        simulation.include_neuroml2_file(nml_file)

        # membrane potential
        simulation.create_output_file("output0", f"{simulation_id}.v.dat")
        simulation.add_column_to_output_file("output0", "TestPop[0]", "TestPop[0]/v")

        # spikes
        simulation.create_event_output_file(
            "output1", f"{simulation_id}.spikes.dat", format="ID_TIME"
        )
        simulation.add_selection_to_event_output_file(
            "output1", "0", "TestPop[0]", "spike"
        )
        lems_simulation_file = simulation.save_to_file()

        pynml.run_lems_with_jneuroml(
            lems_simulation_file, max_memory="2G", nogui=True, plot=False
        )

        # load data
        data_array[amp]["v"] = numpy.loadtxt(f"{simulation_id}.v.dat")
        data_array[amp]["spikes"] = numpy.loadtxt(f"{simulation_id}.spikes.dat")

    if plot:
        xs = []
        ys = []
        labels = []
        firing_rates = {}  # type: dict[str, float]
        for amp, data in data_array.items():
            vs = data["v"]
            spikes = data["spikes"]
            xs.append(vs[:, 0])
            ys.append(vs[:, 1])
            labels.append(amp)

            firing_rate = 1000 * len(spikes) / pulse_duration
            firing_rates[amp] = firing_rate

        pynml.generate_plot(
            xvalues=xs,
            yvalues=ys,
            title="Membrane potential",
            labels=labels,
            show_plot_already=False,
            save_figure_to="%s-v.png" % "test",
            xaxis="time (s)",
            yaxis="membrane potential (V)",
        )

        xlist = list(firing_rates.keys())
        xs1 = [float(x.replace("nA", "")) for x in xlist]
        ys1 = list(firing_rates.values())
        pynml.generate_plot(
            xvalues=[xs1],
            yvalues=[ys1],
            title="F-I curve",
            labels=None,
            show_plot_already=False,
            save_figure_to="%s-fi.png" % "test",
            xaxis="Input current (nA)",
            yaxis="Firing rate (Hz)",
        )

    return data_array
