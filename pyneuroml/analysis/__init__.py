from pyneuroml import pynml
from pyneuroml.lems.LEMSSimulation import LEMSSimulation
import neuroml as nml

from pyneuroml.pynml import print_comment_v
from pyneuroml.lems import generate_lems_file_for_neuroml


def generate_current_vs_frequency_curve(nml2_file, 
                                        cell_id, 
                                        start_amp_nA, 
                                        end_amp_nA, 
                                        step_nA, 
                                        analysis_duration, 
                                        analysis_delay, 
                                        dt = 0.05,
                                        temperature = "32degC",
                                        spike_threshold_mV=0.,
                                        plot_voltage_traces=False,
                                        plot_if=True,
                                        plot_iv=False,
                                        xlim_if =              None,
                                        ylim_if =              None,
                                        xlim_iv =              None,
                                        ylim_iv =              None,
                                        show_plot_already=True, 
                                        save_if_figure_to=None, 
                                        save_iv_figure_to=None, 
                                        simulator="jNeuroML",
                                        include_included=True):
                                            
                                            
    from pyelectro.analysis import max_min
    from pyelectro.analysis import mean_spike_frequency
    import numpy as np
    
    print_comment_v("Generating FI curve for cell %s in %s using %s (%snA->%snA; %snA steps)"%
        (cell_id, nml2_file, simulator, start_amp_nA, end_amp_nA, step_nA))
    
    sim_id = 'iv_%s'%cell_id
    duration = analysis_duration+analysis_delay
    ls = LEMSSimulation(sim_id, duration, dt)
    
    ls.include_neuroml2_file(nml2_file, include_included=include_included)
    
    stims = []
    amp = start_amp_nA
    while amp<=end_amp_nA : 
        stims.append(amp)
        amp+=step_nA
        
    
    number_cells = len(stims)
    pop = nml.Population(id="population_of_%s"%cell_id,
                        component=cell_id,
                        size=number_cells)
    

    # create network and add populations
    net_id = "network_of_%s"%cell_id
    net = nml.Network(id=net_id, type="networkWithTemperature", temperature=temperature)
    ls.assign_simulation_target(net_id)
    net_doc = nml.NeuroMLDocument(id=net.id)
    net_doc.networks.append(net)
    net.populations.append(pop)
    
    for i in range(number_cells):
        stim_amp = "%snA"%stims[i]
        input_id = ("input_%s"%stim_amp).replace('.','_').replace('-','min')
        pg = nml.PulseGenerator(id=input_id,
                                    delay="0ms",
                                    duration="%sms"%duration,
                                    amplitude=stim_amp)
        net_doc.pulse_generators.append(pg)

        # Add these to cells
        input_list = nml.InputList(id=input_id,
                                 component=pg.id,
                                 populations=pop.id)
        input = nml.Input(id='0', 
                              target="../%s[%i]"%(pop.id, i), 
                              destination="synapses")  
        input_list.input.append(input)
        net.input_lists.append(input_list)
    
    
    net_file_name = '%s.net.nml'%sim_id
    pynml.write_neuroml2_file(net_doc, net_file_name)
    ls.include_neuroml2_file(net_file_name)
    
    disp0 = 'Voltage_display'
    ls.create_display(disp0,"Voltages", "-90", "50")
    of0 = 'Volts_file'
    ls.create_output_file(of0, "%s.v.dat"%sim_id)
    
    for i in range(number_cells):
        ref = "v_cell%i"%i
        quantity = "%s[%i]/v"%(pop.id, i)
        ls.add_line_to_display(disp0, ref, quantity, "1mV", pynml.get_next_hex_color())
    
        ls.add_column_to_output_file(of0, ref, quantity)
    
    lems_file_name = ls.save_to_file()
    
    if simulator == "jNeuroML":
        results = pynml.run_lems_with_jneuroml(lems_file_name, 
                                                nogui=True, 
                                                load_saved_data=True, 
                                                plot=plot_voltage_traces,
                                                show_plot_already=False)
    elif simulator == "jNeuroML_NEURON":
        results = pynml.run_lems_with_jneuroml_neuron(lems_file_name, 
                                                nogui=True, 
                                                load_saved_data=True, 
                                                plot=plot_voltage_traces,
                                                show_plot_already=False)
                                                
    
    #print(results.keys())
    if_results = {}
    iv_results = {}
    for i in range(number_cells):
        t = np.array(results['t'])*1000
        v = np.array(results["%s[%i]/v"%(pop.id, i)])*1000
        
        mm = max_min(v, t, delta=0, peak_threshold=spike_threshold_mV)
        spike_times = mm['maxima_times']
        freq = 0
        if len(spike_times) > 2:
            count = 0
            for s in spike_times:
                if s >= analysis_delay and s < (analysis_duration+analysis_delay):
                    count+=1
            freq = 1000 * count/float(analysis_duration)
                    
        mean_freq = mean_spike_frequency(spike_times) 
        # print("--- %s nA, spike times: %s, mean_spike_frequency: %f, freq (%fms -> %fms): %f"%(stims[i],spike_times, mean_freq, analysis_delay, analysis_duration+analysis_delay, freq))
        if_results[stims[i]] = freq
        
        if freq == 0:
            iv_results[stims[i]] = v[-1]
        
    if plot_if:
        
        stims = sorted(if_results.keys())
        stims_pA = [ii*1000 for ii in stims]
        
        freqs = [if_results[s] for s in stims]
            
        pynml.generate_plot([stims_pA],
                            [freqs], 
                            "Frequency versus injected current for: %s"%nml2_file, 
                            colors = ['k'], 
                            linestyles=['-'],
                            markers=['o'],
                            xaxis = 'Input current (pA)', 
                            yaxis = 'Firing frequency (Hz)',
                            xlim = xlim_if,
                            ylim = ylim_if,
                            grid = True,
                            show_plot_already=False,
                            save_figure_to = save_if_figure_to)
    if plot_iv:
        
        stims = sorted(iv_results.keys())
        stims_pA = [ii*1000 for ii in sorted(iv_results.keys())]
        vs = [iv_results[s] for s in stims]
            
        pynml.generate_plot([stims_pA],
                            [vs], 
                            "Final membrane potential versus injected current for: %s"%nml2_file, 
                            colors = ['k'], 
                            linestyles=['-'],
                            markers=['o'],
                            xaxis = 'Input current (pA)', 
                            yaxis = 'Membrane potential (mV)', 
                            xlim = xlim_iv,
                            ylim = ylim_iv,
                            grid = True,
                            show_plot_already=False,
                            save_figure_to = save_iv_figure_to)
    
    if show_plot_already:
        from matplotlib import pyplot as plt
        plt.show()
        
        
    return if_results


def analyse_spiketime_vs_dt(nml2_file, 
                            target,
                            duration,
                            simulator,
                            cell_v_path,
                            dts,
                            verbose=False,
                            spike_threshold_mV = 0,
                            show_plot_already=True):
                                
    from pyelectro.analysis import max_min
    
    all_results = {}
    
    for dt in dts:
        if verbose:
            print_comment_v(" == Generating simulation for dt = %s ms"%dt)
        ref = str("Sim_dt_%s"%dt).replace('.','_')
        lems_file_name = "LEMS_%s.xml"%ref
        generate_lems_file_for_neuroml(ref, 
                                   nml2_file, 
                                   target, 
                                   duration, 
                                   dt, 
                                   lems_file_name,
                                   '.',
                                   gen_plots_for_all_v = True,
                                   gen_saves_for_all_v = True,
                                   copy_neuroml = False,
                                   seed=None)
                                   
        if simulator == 'jNeuroML':
             results = pynml.run_lems_with_jneuroml(lems_file_name, nogui=True, load_saved_data=True, plot=False, verbose=verbose)
        if simulator == 'jNeuroML_NEURON':
             results = pynml.run_lems_with_jneuroml_neuron(lems_file_name, nogui=True, load_saved_data=True, plot=False, verbose=verbose)
             
        print("Results reloaded: %s"%results.keys())
             
        all_results[dt] = results
        

    xs = []
    ys = []
    labels = []
    
    spxs = []
    spys = []
    linestyles = []
    markers = []
    
    for dt in dts:
        t = all_results[dt]['t']
        v = all_results[dt][cell_v_path]
        xs.append(t)
        ys.append(v)
        labels.append(dt)
        
        mm = max_min(v, t, delta=0, peak_threshold=spike_threshold_mV)
        spike_times = mm['maxima_times']
        

        spxs_ = []
        spys_ = []
        for s in spike_times:
            spys_.append(s)
            spxs_.append(dt)
        
        spys.append(spys_)
        spxs.append(spxs_)
        linestyles.append('')
        markers.append('x')
        
    pynml.generate_plot(spxs, 
          spys, 
          "Spike times vs dt",
          linestyles = linestyles,
          markers = markers,
          show_plot_already=show_plot_already) 

        
    if verbose:
        pynml.generate_plot(xs, 
                  ys, 
                  "Membrane potentials in %s for %s"%(simulator,dts),
                  labels = labels,
                  show_plot_already=show_plot_already) 