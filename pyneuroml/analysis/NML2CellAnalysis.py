#!/usr/bin/env python3
"""
Utils to analyse a neuronal cell.

File: pyneuroml/analysis/NML2CellAnalysis.py

Copyright 2022 NeuroML contributors
"""


import typing
import logging

import numpy
import neuroml
from neuroml.utils import component_factory
from pyneuroml.lems import LEMSSimulation
import neuroml.writers as writers
from pyneuroml import pynml


logger = logging.getLogger(__name__)


def compare_point_neurons(
    nml_cells: list[
        typing.Union[
            neuroml.IafTauCell,
            neuroml.IafTauRefCell,
            neuroml.IafCell,
            neuroml.IzhikevichCell,
            neuroml.Izhikevich2007Cell,
            neuroml.AdExIaFCell,
            neuroml.FitzHughNagumo1969Cell,
            neuroml.FitzHughNagumoCell,
            neuroml.PinskyRinzelCA3Cell,
        ]
    ],
    min_amplitude: float = 0.01,
    max_amplitude: float = 0.1,
    num_amplitudes: int = 5,
    duration: float = 2000,
    dt: float = 0.1,
    pulse_duration: float = 1500,
    pulse_delay: float = 200,
    plot: bool = True,
    plot_individuals: bool = False,
) -> dict[str, dict[str, dict[str, list[typing.Any]]]]:
    """Wrapper around `analyse_point_neuron` to compare multiple point neurons.

    For each of the provided cells, we run the `analyse_point_neuron` method,
    collect the data, and plot membrane potential and I-F plots.

    :param nml_cells: cells to analyse/compare
    :type nml_cells: list of abstract single neuron models
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
    :param plot: toggle plotting of collective plots
    :type plot: bool
    :param plot_individuals: toggle plotting of individual cell plots
    :type plot_individuals: bool
    :returns: dict
        { 'cellid': { 'amplitude': { 'v': [[time], [memb potential]], 'spikes': [spike times] }}}

    """
    all_data = {}
    for cell in nml_cells:
        all_data[cell.id] = analyse_point_neuron(
            cell,
            min_amplitude,
            max_amplitude,
            num_amplitudes,
            duration,
            dt,
            pulse_duration,
            pulse_delay,
            plot_individuals,
        )

    if plot:
        labels_frate = []
        x1s = []
        y1s = []
        vs_amps = {}
        for cell_id, data_array in all_data.items():
            labels_frate.append(cell_id)
            xrates = []
            yrates = []
            for amp, data in data_array.items():
                if amp not in vs_amps:
                    vs_amps[amp] = {}

                vs = data["v"]

                try:
                    vs_amps[amp]["x"].append(vs[:, 0])
                except KeyError:
                    vs_amps[amp]["x"] = []
                    vs_amps[amp]["x"].append(vs[:, 0])

                try:
                    vs_amps[amp]["y"].append(vs[:, 1])
                except KeyError:
                    vs_amps[amp]["y"] = []
                    vs_amps[amp]["y"].append(vs[:, 1])

                try:
                    vs_amps[amp]["labels"].append(f"{cell_id}")
                except KeyError:
                    vs_amps[amp]["labels"] = []
                    vs_amps[amp]["labels"].append(f"{cell_id}")

                spikes = data["spikes"]
                firing_rate = 1000 * len(spikes) / pulse_duration
                xrates.append(amp.replace("nA", ""))
                yrates.append(firing_rate)

            x1s.append(xrates)
            y1s.append(yrates)

        for amp, vals in vs_amps.items():
            pynml.generate_plot(
                xvalues=vals["x"],
                yvalues=vals["y"],
                title="Membrane potential",
                labels=vals["labels"],
                show_plot_already=False,
                save_figure_to=f"comparison-{amp}-v.png",
                xaxis="time (s)",
                yaxis="membrane potential (V)",
                legend_position="bottom center",
            )

        pynml.generate_plot(
            xvalues=x1s,
            yvalues=y1s,
            title="F-I curves",
            labels=labels_frate,
            show_plot_already=False,
            save_figure_to="comparison-fi.png",
            xaxis="Input current (nA)",
            yaxis="Firing rate (Hz)",
            legend_position="bottom center",
        )

    return all_data


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
    amplitudes = [f"{amp:.4f}nA" for amp in amps]

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
            sim_id=simulation_id, duration=duration, dt=dt, simulation_seed=123
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
            save_figure_to=f"{nml_cell.id}-v.png",
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
            save_figure_to=f"{nml_cell.id}-fi.png",
            xaxis="Input current (nA)",
            yaxis="Firing rate (Hz)",
        )

    return data_array


def analyse_multi_compartmental_neuron(
    nml_cell: typing.Union[neuroml.Cell, neuroml.Cell2CaPools],
    input_segment_id: str = None,
    output_segment_ids: list[str] = None,
    includes: list[neuroml.Include] = None,
    min_amplitude: float = 0.01,
    max_amplitude: float = 0.1,
    num_amplitudes: int = 5,
    duration: float = 2000,
    dt: float = 0.1,
    pulse_duration: float = 1500,
    pulse_delay: float = 200,
    plot: bool = True,
):
    """Analyse a NeuroML multi-compartmental cell model.

    This method adds the cell to a network, and simulates it with a range of
    input currents to get its input-firing rate response profile.

    Note that the cell needs to be complete, and the user must provide the ids
    of segments to be used to provide the stimulation to the cell, and ids of
    segments to record from.

    This uses the NEURON simulator to simulate the test models.

    :param nml_cell: cell to analyse
    :type nml_cell: neuroml.Cell or neuroml.Cell2CaPools
    :param input_segment_id: segment id to provide stimuluation to
    :type input_segment_id: str
    :param output_segment_ids: list of segments ids to record membrane potentials from
    :type output_segment_ids: list
    :param includes: extra includes, for example ion channel definition files
    :type includes: list
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
    amplitudes = [f"{amp:.4f}nA" for amp in amps]

    for amp in amplitudes:
        data_array[amp] = {}
        nml_doc = component_factory(neuroml.NeuroMLDocument, id="Test")
        nml_doc.add(nml_cell)

        net = nml_doc.add(neuroml.Network, id="TestNet", validate=False)
        pop = net.add(
            neuroml.Population,
            id="TestPop",
            type="populationList",
            component=nml_cell.id,
            size="1",
            validate=False,
        )
        pop.add("Instance", id=0, location=component_factory("Location", x=0, y=0, z=0))

        pg = nml_doc.add(
            "PulseGenerator",
            id="pulseGen_0",
            delay=f"{pulse_delay} ms",
            duration=f"{pulse_duration} ms",
            amplitude=amp,
        )
        if input_segment_id is None:
            net.add("ExplicitInput", target=f"{pop.id}/0", input=pg.id)
        else:
            net.add(
                "ExplicitInput",
                target=f"{pop.id}/0/{nml_cell.id}/{input_segment_id}",
                input=pg.id,
            )

        nml_doc.includes.extend(includes)
        nml_doc.validate(recursive=True)

        nml_file = f"cell_test_{amp}.nml"
        writers.NeuroMLWriter.write(nml_doc, nml_file)

        simulation_id = f"cell_test_{amp}"
        simulation = LEMSSimulation(
            sim_id=simulation_id, duration=duration, dt=dt, simulation_seed=123
        )
        simulation.assign_simulation_target(net.id)
        simulation.include_neuroml2_file(nml_file)

        # membrane potential
        simulation.create_output_file("output0", f"{simulation_id}.v.dat")

        if output_segment_ids is not None:
            for o in output_segment_ids:
                simulation.add_column_to_output_file(
                    "output0", f"{o}", f"TestPop/0/{nml_cell.id}/{o}/v"
                )
        else:
            raise ValueError("Please provide the list of output segment ids")

        # spikes
        simulation.create_event_output_file(
            "output1", f"{simulation_id}.spikes.dat", format="ID_TIME"
        )
        simulation.add_selection_to_event_output_file(
            "output1", "0", "TestPop/0", "spike"
        )
        lems_simulation_file = simulation.save_to_file()

        pynml.run_lems_with_jneuroml_neuron(
            lems_simulation_file, max_memory="2G", nogui=True, plot=False
        )

        # load data
        data_array[amp]["v"] = numpy.loadtxt(f"{simulation_id}.v.dat")
        data_array[amp]["spikes"] = numpy.loadtxt(f"{simulation_id}.spikes.dat")

    if plot:
        xs = []
        ys = {}
        labels = []
        firing_rates = {}  # type: dict[str, float]
        for amp, data in data_array.items():
            vs = data["v"]
            spikes = data["spikes"]

            firing_rate = 1000 * len(spikes) / pulse_duration
            firing_rates[amp] = firing_rate

            xs.append(vs[:, 0])
            labels.append(amp)

            # get vs for each segment recorded from
            for col in range(0, len(output_segment_ids)):
                try:
                    ys[output_segment_ids[col]].append(vs[:, col + 1])
                except KeyError:
                    ys[output_segment_ids[col]] = []
                    ys[output_segment_ids[col]].append(vs[:, col + 1])

        for col, vals in ys.items():
            pynml.generate_plot(
                xvalues=xs,
                yvalues=vals,
                title="Membrane potential",
                labels=labels,
                show_plot_already=False,
                save_figure_to=f"{nml_cell.id}-{col}-v.png",
                xaxis="time (s)",
                yaxis="membrane potential (V)",
                legend_position="bottom center"
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
            save_figure_to=f"{nml_cell.id}-fi.png",
            xaxis="Input current (nA)",
            yaxis="Firing rate (Hz)",
            legend_position="bottom center"
        )

    return data_array


def compare_multi_compartmental_neurons(
    nml_cells: list[typing.Union[neuroml.Cell, neuroml.Cell2CaPools]],
    input_segment_id: list[str] = None,
    output_segment_ids: list[list[str]] = None,
    includes: list[list[neuroml.Include]] = None,
    min_amplitude: float = 0.01,
    max_amplitude: float = 0.1,
    num_amplitudes: int = 5,
    duration: float = 2000,
    dt: float = 0.1,
    pulse_duration: float = 1500,
    pulse_delay: float = 200,
    plot: bool = True,
    plot_individuals: bool = False,
):
    """Wrapper around `analyse_multi_compartmental_neuron` to compare multiple
    multi-compartmental neurons.

    For each of the provided cells, we run the
    `analyse_multi_compartmental_neuron` method, collect the data, and plot
    membrane potential and I-F plots.

    :param nml_cells: cells to analyse/compare
    :type nml_cells: list of neuron models
    :param input_segment_ids: list of segment ids to provide stimuluation to,
        one for each neuron
    :type input_segment_id: list
    :param output_segment_ids: list of list of segments ids to record membrane
        potentials from, one list for each neuron
    :type output_segment_ids: list of lists
    :param includes: list of list of extra includes, for example ion channel
        definition files, one list for each neuron
    :type includes: list of list
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
    :param plot_individuals: toggle plotting of individual cell plots
    :type plot_individuals: bool

    :returns: dict
        { 'cellid': { 'amplitude': { 'v': [[time], [memb potential]], 'spikes': [spike times] }}}

    """
    all_data = {}
    cells = len(nml_cells)
    for i in range(0, cells):
        all_data[nml_cells[i].id] = analyse_multi_compartmental_neuron(
            nml_cells[i],
            input_segment_id[i],
            output_segment_ids[i],
            includes[i],
            min_amplitude,
            max_amplitude,
            num_amplitudes,
            duration,
            dt,
            pulse_duration,
            pulse_delay,
            plot_individuals,
        )
