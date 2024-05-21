import math
import os
import logging
import typing
import numpy as np

from pyneuroml import pynml
from pyneuroml.lems.LEMSSimulation import LEMSSimulation
from pyneuroml.lems import generate_lems_file_for_neuroml
from pyneuroml.utils.plot import get_next_hex_color
from pyneuroml.plot import generate_plot
import neuroml as nml

from typing import Optional


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    from pyelectro.analysis import max_min
    from pyelectro.analysis import mean_spike_frequency
except ImportError:
    logger.warning("Please install optional dependencies to use analysis features:")
    logger.warning("pip install pyneuroml[analysis]")


def generate_current_vs_frequency_curve(
    nml2_file: str,
    cell_id: str,
    start_amp_nA: float = -0.1,
    end_amp_nA: float = 0.1,
    step_nA: float = 0.01,
    custom_amps_nA: typing.List[float] = [],
    analysis_duration: float = 1000,
    analysis_delay: float = 0,
    pre_zero_pulse: float = 0,
    post_zero_pulse: float = 0,
    dt: float = 0.05,
    temperature: str = "32degC",
    spike_threshold_mV: float = 0.0,
    plot_voltage_traces: bool = False,
    plot_if: bool = True,
    plot_iv: bool = False,
    xlim_if: Optional[typing.List[float]] = None,
    ylim_if: Optional[typing.List[float]] = None,
    xlim_iv: Optional[typing.List[float]] = None,
    ylim_iv: Optional[typing.List[float]] = None,
    label_xaxis: bool = True,
    label_yaxis: bool = True,
    show_volts_label: bool = True,
    grid: bool = True,
    font_size: int = 12,
    if_iv_color: str = "k",
    linewidth: str = "1",
    bottom_left_spines_only: bool = False,
    show_plot_already: bool = True,
    save_voltage_traces_to: Optional[str] = None,
    save_if_figure_to: Optional[str] = None,
    save_iv_figure_to: Optional[str] = None,
    save_if_data_to: Optional[str] = None,
    save_iv_data_to: Optional[str] = None,
    simulator: str = "jNeuroML",
    num_processors: int = 1,
    include_included: bool = True,
    title_above_plot: bool = False,
    return_axes: bool = False,
    verbose: bool = False,
    segment_id: typing.Optional[str] = None,
    fraction_along: typing.Optional[float] = None,
):
    """Generate current vs firing rate frequency curves for provided cell.

    It runs a number of simulations of the cell with different input currents,
    and generates the following metrics/graphs:

    - sub-threshold potentials for all currents
    - F-I curve for the cell
    - membrane potential traces for each stimulus

    Using the method arguments, these graphs and the data they are generated
    from may be enabled/disabled/saved.

    When the I-F curve plotting is enabled, it also notes the spiking threshold
    current value in a file. Note that this value is simply the lowest input
    stimulus current at which spiking was detected, so should be taken as an
    approximate value. It does not, for example, implement a bisection based
    method to find the accurate spiking threshold current. This is also true
    for the I-F curves: the resolution is constrained by the values of the
    stimulus currents.

    The various plotting related arguments to this method are passed on to
    :py:meth:`pyneuroml.plot.generate_plot`

    :param nml2_file: name of NeuroML file containing cell definition
    :type nml2_file: str
    :param cell_id: id of cell to analyse
    :type cell_id: str
    :param start_amp_nA: min current to use for analysis
    :type start_amp_nA: float
    :param end_amp_nA: max current to use for analysis
    :type end_amp_nA: float
    :param step_nA: step value to use to generate analysis currents between
        `start_amp_nA` and `end_amp_nA`
    :type step_nA: float
    :param custom_amps_nA: list of currents in nA to use. Note that this
        overrides the list created using `start_amp_nA`, `end_amp_nA`, and
        `step_nA`) :type custom_amps_nA: list(float)
    :param analysis_duration: duration of analysis
    :type analysis_duration: float
    :param analysis_delay: delay period before analysis begins
    :type analysis_delay: float
    :param pre_zero_pulse: duration of pre-zero pulse
    :type pre_zero_pulse: float
    :param post_zero_pulse: duration of post-zero pulse
    :type post_zero_pulse: float
    :param dt: integration time step
    :type dt: float
    :param temperature: temperature to use for analysis
    :type temperature: str
    :param spike_threshold_mV: spike threshold potential
    :type spike_threshold_mV: float
    :param plot_voltage_traces: toggle plotting of voltage traces
    :type plot_voltage_traces: bool
    :param plot_if: toggle whether to plot I-F graphs
    :type plot_if: bool
    :param plot_iv: toggle whether to plot I-V graphs
    :type plot_iv: bool
    :param xlim_if: x-limits of I-F curve
    :type xlim_if: [min, max]
    :param ylim_if: y limits of I-F curve
    :type ylim_if: [min, max]
    :param xlim_iv: x limits of I-V curve
    :type xlim_iv: [min, max]
    :param ylim_iv: y limits of I-V curve
    :type ylim_iv: [min, max]
    :param label_xaxis: label for x axis
    :type label_xaxis: str
    :param label_yaxis: label for y axis
    :type label_yaxis: str
    :param show_volts_label: toggle whether voltage traces should have
        corresponding current values labelled in the plot
    :type show_volts_label: bool
    :param grid: toggle whether grid should be shown in plot
    :type grid: bool
    :param font_size: font size for plot
    :type font_size: int
    :param if_iv_color: color to use for I-F and I-V plots
    :type if_iv_color: str
    :param linewidth: line width for plotting
    :type linewidth: str
    :param bottom_left_spines_only:
    :type bottom_left_spines_only:
    :param show_plot_already: toggle whether generated plots should be shown
    :type show_plot_already: bool
    :param save_voltage_traces_to: file to save membrane potential traces to
    :type save_voltage_traces_to: str
    :param save_if_figure_to: file to save I-F plot figure to
    :type save_if_figure_to: str
    :param save_iv_figure_to: file to save I-V plot figure to
    :type save_iv_figure_to: str
    :param save_if_data_to: file to save I-F plot data to
    :type save_if_data_to: str
    :param save_iv_data_to: file to save I-V plot data to
    :type save_iv_data_to: str
    :param simulator: simulator to use
    :type simulator: str
    :param num_processors: number of processors to use for analysis
        This option is only used with NetPyNE which can use MPI for
        parallelising simulations. For other simulators, this is unused.
    :type num_processors: int
    :param include_included: include included files
    :type include_included: bool
    :param title_above_plot: title to show above the plot
    :type title_above_plot: str
    :param return_axes: toggle whether plotting axis should be returned.
        This is useful if one wants to overlay more graphs in the same plot.
    :type return_axes: bool
    :param segment_id: segment id to attach input to
    :type segment_id: str
    :param fraction_along: fraction along on segment to attach to
    :type fraction_along: float
    :param verbose: toggle verbosity
    :type verbose: bool

    """

    logger.info(
        "Running generate_current_vs_frequency_curve() on %s (%s)"
        % (nml2_file, os.path.abspath(nml2_file))
    )
    traces_ax = None
    if_ax = None
    iv_ax = None

    sim_id = "iv_%s" % cell_id
    # total duration of simulation
    total_duration = (
        pre_zero_pulse + analysis_duration + analysis_delay + post_zero_pulse
    )
    # end time of pulse
    pulse_duration = analysis_duration + analysis_delay
    # end time of stimulation
    end_stim = pre_zero_pulse + analysis_duration + analysis_delay
    ls = LEMSSimulation(sim_id, total_duration, dt)
    ls.include_neuroml2_file(nml2_file, include_included=include_included)

    # use custom list of currents if provided
    stims = []
    if len(custom_amps_nA) > 0:
        stims = [float(a) for a in custom_amps_nA]
        stim_info = ["%snA" % float(a) for a in custom_amps_nA]  # type: typing.Union[str, typing.List[str]]
    else:
        # else generate a list using the provided arguments
        amp = start_amp_nA
        while amp <= end_amp_nA:
            stims.append(amp)
            amp += step_nA

        stim_info = "(%snA->%snA; %s steps of %snA; %sms)" % (
            start_amp_nA,
            end_amp_nA,
            len(stims),
            step_nA,
            total_duration,
        )

    logger.info(
        "Generating an IF curve for cell %s in %s using %s %s"
        % (cell_id, nml2_file, simulator, stim_info)
    )

    # create a population of cells, one for each stimulus
    number_cells = len(stims)
    pop = nml.Population(
        id="population_of_%s" % cell_id, component=cell_id, size=number_cells
    )

    # create network and add populations
    net_id = "network_of_%s" % cell_id
    net = nml.Network(id=net_id, type="networkWithTemperature", temperature=temperature)
    ls.assign_simulation_target(net_id)
    net_doc = nml.NeuroMLDocument(id=net.id)
    net_doc.networks.append(net)
    net_doc.includes.append(nml.IncludeType(nml2_file))
    net.populations.append(pop)

    # create stimulus for each cell
    for i in range(number_cells):
        stim_amp = "%snA" % stims[i]
        input_id = ("input_%s" % stim_amp).replace(".", "_").replace("-", "min")
        pg = nml.PulseGenerator(
            id=input_id,
            delay="%sms" % pre_zero_pulse,
            duration="%sms" % pulse_duration,
            amplitude=stim_amp,
        )
        net_doc.pulse_generators.append(pg)

        # Add these to cells
        input_list = nml.InputList(id=input_id, component=pg.id, populations=pop.id)
        aninput = nml.Input(
            id="0",
            target="../%s[%i]" % (pop.id, i),
            destination="synapses",
            segment_id=segment_id,
            fraction_along=fraction_along,
        )
        input_list.input.append(aninput)

        net.input_lists.append(input_list)

    net_file_name = "%s.net.nml" % sim_id
    pynml.write_neuroml2_file(net_doc, net_file_name)
    ls.include_neuroml2_file(net_file_name)

    disp0 = "Voltage_display"
    ls.create_display(disp0, "Voltages", "-90", "50")
    of0 = "Volts_file"
    ls.create_output_file(of0, "%s.v.dat" % sim_id)

    for i in range(number_cells):
        ref = "v_cell%i" % i
        quantity = "%s[%i]/v" % (pop.id, i)
        ls.add_line_to_display(disp0, ref, quantity, "1mV", get_next_hex_color())
        ls.add_column_to_output_file(of0, ref, quantity)

    lems_file_name = ls.save_to_file()

    logger.info(
        "Written LEMS file %s (%s)" % (lems_file_name, os.path.abspath(lems_file_name))
    )

    # run simulation
    if simulator == "jNeuroML":
        results = pynml.run_lems_with_jneuroml(
            lems_file_name,
            nogui=True,
            load_saved_data=True,
            plot=False,
            show_plot_already=False,
            verbose=verbose,
        )
    elif simulator == "jNeuroML_NEURON":
        results = pynml.run_lems_with_jneuroml_neuron(
            lems_file_name,
            nogui=True,
            load_saved_data=True,
            plot=False,
            show_plot_already=False,
            verbose=verbose,
        )
    elif simulator == "jNeuroML_NetPyNE":
        results = pynml.run_lems_with_jneuroml_netpyne(
            lems_file_name,
            nogui=True,
            load_saved_data=True,
            plot=False,
            show_plot_already=False,
            num_processors=num_processors,
            verbose=verbose,
        )
    else:
        raise Exception(
            "Sorry, cannot yet run current vs frequency analysis using simulator %s"
            % simulator
        )

    logger.info(
        "Completed run in simulator %s (results: %s)" % (simulator, results.keys())
    )

    # print(results.keys())
    times_results = []
    volts_results = []
    volts_labels = []
    if_results = {}
    iv_results = {}

    # arbitrarily large value to start with
    spike_threshold_current = float(math.inf)

    for i in range(number_cells):
        t = np.array(results["t"]) * 1000
        v = np.array(results["%s[%i]/v" % (pop.id, i)]) * 1000

        if plot_voltage_traces:
            times_results.append(t)
            volts_results.append(v)
            volts_labels.append("%s nA" % stims[i])

        mm = max_min(v, t, delta=0, peak_threshold=spike_threshold_mV)
        spike_times = mm["maxima_times"]
        freq = 0.0

        if len(spike_times) > 2:
            count = 0
            for s in spike_times:
                if s >= pre_zero_pulse + analysis_delay and s < (
                    pre_zero_pulse + analysis_duration + analysis_delay
                ):
                    count += 1
            freq = 1000 * count / float(analysis_duration)
            if count > 0:
                if stims[i] < spike_threshold_current:
                    spike_threshold_current = stims[i]

        mean_freq = mean_spike_frequency(spike_times)
        logger.debug(
            "--- %s nA, spike times: %s, mean_spike_frequency: %f, freq (%fms -> %fms): %f"
            % (
                stims[i],
                spike_times,
                mean_freq,
                analysis_delay,
                analysis_duration + analysis_delay,
                freq,
            )
        )
        if_results[stims[i]] = freq

        if freq == 0:
            if post_zero_pulse == 0:
                iv_results[stims[i]] = v[-1]
            else:
                v_end = None
                for j in range(len(t)):
                    if v_end is None and t[j] >= end_stim:
                        v_end = v[j]
                iv_results[stims[i]] = v_end

    if plot_voltage_traces:
        traces_ax = generate_plot(
            times_results,
            volts_results,
            "Membrane potential traces for: %s" % nml2_file,
            xaxis="Time (ms)" if label_xaxis else " ",
            yaxis="Membrane potential (mV)" if label_yaxis else "",
            xlim=[total_duration * -0.05, total_duration * 1.05],
            show_xticklabels=label_xaxis,
            font_size=font_size,
            bottom_left_spines_only=bottom_left_spines_only,
            grid=False,
            labels=volts_labels if show_volts_label else [],
            show_plot_already=False,
            save_figure_to=save_voltage_traces_to,
            title_above_plot=title_above_plot,
            verbose=verbose,
        )

    if plot_if:
        stims = sorted(if_results.keys())
        stims_pA = [ii * 1000 for ii in stims]
        freqs = [if_results[s] for s in stims]
        if_ax = generate_plot(
            [stims_pA],
            [freqs],
            "Firing frequency versus injected current for: %s" % nml2_file,
            colors=[if_iv_color],
            linestyles=["-"],
            markers=["o"],
            linewidths=[linewidth],
            xaxis="Input current (pA)" if label_xaxis else " ",
            yaxis="Firing frequency (Hz)" if label_yaxis else "",
            xlim=xlim_if,
            ylim=ylim_if,
            show_xticklabels=label_xaxis,
            show_yticklabels=label_yaxis,
            font_size=font_size,
            bottom_left_spines_only=bottom_left_spines_only,
            grid=grid,
            show_plot_already=False,
            save_figure_to=save_if_figure_to,
            title_above_plot=title_above_plot,
            verbose=verbose,
        )

        if save_if_data_to:
            with open(save_if_data_to, "w") as if_file:
                for i in range(len(stims_pA)):
                    if_file.write("%s\t%s\n" % (stims_pA[i], freqs[i]))
            with open(f"threshold_i_{save_if_data_to}", "w") as if_file:
                print(spike_threshold_current, file=if_file)
    if plot_iv:
        stims = sorted(iv_results.keys())
        stims_pA = [ii * 1000 for ii in sorted(iv_results.keys())]
        vs = [iv_results[s] for s in stims]

        xs = []  # type: typing.List[typing.List[float]]
        ys = []  # type: typing.List[typing.List[float]]
        xs.append([])
        ys.append([])

        for si in range(len(stims)):
            stim = stims[si]
            if (
                len(custom_amps_nA) == 0
                and si > 1
                and (stims[si] - stims[si - 1]) > step_nA * 1.01
            ):
                xs.append([])
                ys.append([])

            xs[-1].append(stim * 1000)
            ys[-1].append(iv_results[stim])

        iv_ax = generate_plot(
            xs,
            ys,
            "V at %sms versus I below threshold for: %s" % (end_stim, nml2_file),
            colors=[if_iv_color for s in xs],
            linestyles=["-" for s in xs],
            markers=["o" for s in xs],
            xaxis="Input current (pA)" if label_xaxis else "",
            yaxis="Membrane potential (mV)" if label_yaxis else "",
            xlim=xlim_iv,
            ylim=ylim_iv,
            show_xticklabels=label_xaxis,
            show_yticklabels=label_yaxis,
            font_size=font_size,
            linewidths=[linewidth for s in xs],
            bottom_left_spines_only=bottom_left_spines_only,
            grid=grid,
            show_plot_already=False,
            save_figure_to=save_iv_figure_to,
            title_above_plot=title_above_plot,
            verbose=verbose,
        )

        if save_iv_data_to:
            with open(save_iv_data_to, "w") as iv_file:
                for i in range(len(stims_pA)):
                    iv_file.write("%s\t%s\n" % (stims_pA[i], vs[i]))

    if show_plot_already:
        from matplotlib import pyplot as plt

        plt.show()

    if return_axes:
        return traces_ax, if_ax, iv_ax

    return if_results


def analyse_spiketime_vs_dt(
    nml2_file,
    target,
    duration,
    simulator,
    cell_v_path,
    dts,
    verbose=False,
    spike_threshold_mV=0,
    show_plot_already=True,
    save_figure_to=None,
    num_of_last_spikes=None,
):
    from pyelectro.analysis import max_min
    import numpy as np

    all_results = {}

    dts = list(np.sort(dts))

    for dt in dts:
        logger.info(" == Generating simulation for dt = %s ms" % dt)
        ref = str("Sim_dt_%s" % dt).replace(".", "_")
        lems_file_name = "LEMS_%s.xml" % ref
        generate_lems_file_for_neuroml(
            ref,
            nml2_file,
            target,
            duration,
            dt,
            lems_file_name,
            ".",
            gen_plots_for_all_v=True,
            gen_saves_for_all_v=True,
            copy_neuroml=False,
        )

        if simulator == "jNeuroML":
            results = pynml.run_lems_with_jneuroml(
                lems_file_name,
                nogui=True,
                load_saved_data=True,
                plot=False,
                verbose=verbose,
            )
        if simulator == "jNeuroML_NEURON":
            results = pynml.run_lems_with_jneuroml_neuron(
                lems_file_name,
                nogui=True,
                load_saved_data=True,
                plot=False,
                verbose=verbose,
            )

        logger.info("Results reloaded: %s" % results.keys())
        all_results[dt] = results

    xs = []
    ys = []
    labels = []

    spxs = []
    spys = []
    linestyles = []
    markers = []
    colors = []
    spike_times_final = []
    array_of_num_of_spikes = []

    for dt in dts:
        t = all_results[dt]["t"]
        v = all_results[dt][cell_v_path]
        xs.append(t)
        ys.append(v)
        labels.append(dt)

        mm = max_min(v, t, delta=0, peak_threshold=spike_threshold_mV)
        spike_times = mm["maxima_times"]
        spike_times_final.append(spike_times)
        array_of_num_of_spikes.append(len(spike_times))

    max_num_of_spikes = max(array_of_num_of_spikes)
    min_dt_spikes = spike_times_final[0]
    bound_dts = [math.log(dts[0]), math.log(dts[-1])]

    if num_of_last_spikes is None:
        num_of_spikes = len(min_dt_spikes)
    else:
        if len(min_dt_spikes) >= num_of_last_spikes:
            num_of_spikes = num_of_last_spikes
        else:
            num_of_spikes = len(min_dt_spikes)

    spike_indices = [(-1) * ind for ind in range(1, num_of_spikes + 1)]

    if len(min_dt_spikes) > abs(spike_indices[-1]):
        earliest_spike_time = min_dt_spikes[spike_indices[-1] - 1]
    else:
        earliest_spike_time = min_dt_spikes[spike_indices[-1]]

    for spike_ind in range(0, max_num_of_spikes):
        spike_time_values = []
        dt_values = []
        for dt in range(0, len(dts)):
            if spike_times_final[dt] != []:
                if len(spike_times_final[dt]) >= spike_ind + 1:
                    if spike_times_final[dt][spike_ind] >= earliest_spike_time:
                        spike_time_values.append(spike_times_final[dt][spike_ind])
                        dt_values.append(math.log(dts[dt]))

        linestyles.append("")
        markers.append("o")
        colors.append("g")
        spxs.append(dt_values)
        spys.append(spike_time_values)

    for last_spike_index in spike_indices:
        vertical_line = [
            min_dt_spikes[last_spike_index],
            min_dt_spikes[last_spike_index],
        ]
        spxs.append(bound_dts)
        spys.append(vertical_line)
        linestyles.append("--")
        markers.append("")
        colors.append("k")

    generate_plot(
        spxs,
        spys,
        "Spike times vs dt",
        colors=colors,
        linestyles=linestyles,
        markers=markers,
        xaxis="ln ( dt (ms) )",
        yaxis="Spike times (s)",
        show_plot_already=show_plot_already,
        save_figure_to=save_figure_to,
    )

    if verbose:
        generate_plot(
            xs,
            ys,
            "Membrane potentials in %s for %s" % (simulator, dts),
            labels=labels,
            show_plot_already=show_plot_already,
            save_figure_to=save_figure_to,
        )
