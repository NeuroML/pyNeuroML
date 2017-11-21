from pyneuroml import pynml
from pyneuroml.lems.LEMSSimulation import LEMSSimulation
import neuroml as nml

from pyneuroml.pynml import print_comment_v, print_comment
from pyneuroml.lems import generate_lems_file_for_neuroml
import math
import os


def generate_current_vs_frequency_curve(nml2_file, 
                                        cell_id, 
                                        start_amp_nA =          -0.1, 
                                        end_amp_nA =            0.1,
                                        step_nA =               0.01, 
                                        custom_amps_nA =        [], 
                                        analysis_duration =     1000, 
                                        analysis_delay =        0, 
                                        pre_zero_pulse =        0,
                                        post_zero_pulse =       0,
                                        dt =                    0.05,
                                        temperature =           "32degC",
                                        spike_threshold_mV =    0.,
                                        plot_voltage_traces =   False,
                                        plot_if =               True,
                                        plot_iv =               False,
                                        xlim_if =               None,
                                        ylim_if =               None,
                                        xlim_iv =               None,
                                        ylim_iv =               None,
                                        label_xaxis =           True,
                                        label_yaxis =           True,
                                        show_volts_label =      True,
                                        grid =                  True,
                                        font_size =             12,
                                        if_iv_color =           'k',
                                        linewidth =             1,
                                        bottom_left_spines_only = False,
                                        show_plot_already =     True, 
                                        save_voltage_traces_to = None, 
                                        save_if_figure_to =     None, 
                                        save_iv_figure_to =     None, 
                                        save_if_data_to =       None, 
                                        save_iv_data_to =       None, 
                                        simulator =             "jNeuroML",
                                        num_processors =        1,
                                        include_included =      True,
                                        title_above_plot =      False,
                                        return_axes =           False,
                                        verbose =               False):
                                            
    print_comment("Running generate_current_vs_frequency_curve() on %s (%s)"%(nml2_file,os.path.abspath(nml2_file)), verbose)                
    from pyelectro.analysis import max_min
    from pyelectro.analysis import mean_spike_frequency
    import numpy as np
    traces_ax = None
    if_ax = None
    iv_ax = None
    
    
    sim_id = 'iv_%s'%cell_id
    total_duration = pre_zero_pulse+analysis_duration+analysis_delay+post_zero_pulse
    pulse_duration = analysis_duration+analysis_delay
    end_stim = pre_zero_pulse+analysis_duration+analysis_delay
    ls = LEMSSimulation(sim_id, total_duration, dt)
    
    ls.include_neuroml2_file(nml2_file, include_included=include_included)
    
    stims = []
    if len(custom_amps_nA)>0:
        stims = [float(a) for a in custom_amps_nA]
        stim_info = ['%snA'%float(a) for a in custom_amps_nA]
    else:
        amp = start_amp_nA
        while amp<=end_amp_nA : 
            stims.append(amp)
            amp+=step_nA
        
        stim_info = '(%snA->%snA; %s steps of %snA; %sms)'%(start_amp_nA, end_amp_nA, len(stims), step_nA, total_duration)
        
    print_comment_v("Generating an IF curve for cell %s in %s using %s %s"%
        (cell_id, nml2_file, simulator, stim_info))
        
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
    net_doc.includes.append(nml.IncludeType(nml2_file))
    net.populations.append(pop)

    for i in range(number_cells):
        stim_amp = "%snA"%stims[i]
        input_id = ("input_%s"%stim_amp).replace('.','_').replace('-','min')
        pg = nml.PulseGenerator(id=input_id,
                                    delay="%sms"%pre_zero_pulse,
                                    duration="%sms"%pulse_duration,
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
    
    print_comment("Written LEMS file %s (%s)"%(lems_file_name,os.path.abspath(lems_file_name)), verbose)   

    if simulator == "jNeuroML":
        results = pynml.run_lems_with_jneuroml(lems_file_name, 
                                                nogui=True, 
                                                load_saved_data=True, 
                                                plot=False,
                                                show_plot_already=False,
                                                verbose=verbose)
    elif simulator == "jNeuroML_NEURON":
        results = pynml.run_lems_with_jneuroml_neuron(lems_file_name, 
                                                nogui=True, 
                                                load_saved_data=True, 
                                                plot=False,
                                                show_plot_already=False,
                                                verbose=verbose)
    elif simulator == "jNeuroML_NetPyNE":
        results = pynml.run_lems_with_jneuroml_netpyne(lems_file_name, 
                                                nogui=True, 
                                                load_saved_data=True, 
                                                plot=False,
                                                show_plot_already=False,
                                                num_processors = num_processors,
                                                verbose=verbose)
    else:
        raise Exception("Sorry, cannot yet run current vs frequency analysis using simulator %s"%simulator)
    
    print_comment("Completed run in simulator %s (results: %s)"%(simulator,results.keys()), verbose)  
        
    #print(results.keys())
    times_results = []
    volts_results = []
    volts_labels = []
    if_results = {}
    iv_results = {}
    for i in range(number_cells):
        t = np.array(results['t'])*1000
        v = np.array(results["%s[%i]/v"%(pop.id, i)])*1000

        if plot_voltage_traces:
            times_results.append(t)
            volts_results.append(v)
            volts_labels.append("%s nA"%stims[i])
            
        mm = max_min(v, t, delta=0, peak_threshold=spike_threshold_mV)
        spike_times = mm['maxima_times']
        freq = 0
        if len(spike_times) > 2:
            count = 0
            for s in spike_times:
                if s >= pre_zero_pulse + analysis_delay and s < (pre_zero_pulse + analysis_duration+analysis_delay):
                    count+=1
            freq = 1000 * count/float(analysis_duration)
                    
        mean_freq = mean_spike_frequency(spike_times) 
        #print("--- %s nA, spike times: %s, mean_spike_frequency: %f, freq (%fms -> %fms): %f"%(stims[i],spike_times, mean_freq, analysis_delay, analysis_duration+analysis_delay, freq))
        if_results[stims[i]] = freq
        
        if freq == 0:
            if post_zero_pulse==0:
                iv_results[stims[i]] = v[-1]
            else:
                v_end = None
                for j in range(len(t)):
                    if v_end==None and t[j]>=end_stim:
                        v_end = v[j]
                iv_results[stims[i]] = v_end
            
    if plot_voltage_traces:
            
        traces_ax = pynml.generate_plot(times_results,
                            volts_results, 
                            "Membrane potential traces for: %s"%nml2_file, 
                            xaxis = 'Time (ms)' if label_xaxis else ' ', 
                            yaxis = 'Membrane potential (mV)' if label_yaxis else '',
                            xlim = [total_duration*-0.05,total_duration*1.05],
                            show_xticklabels = label_xaxis,
                            font_size = font_size,
                            bottom_left_spines_only = bottom_left_spines_only,
                            grid = False,
                            labels = volts_labels if show_volts_label else [],
                            show_plot_already=False,
                            save_figure_to = save_voltage_traces_to,
                            title_above_plot = title_above_plot,
                            verbose=verbose)
    
        
    if plot_if:
        
        stims = sorted(if_results.keys())
        stims_pA = [ii*1000 for ii in stims]
        
        freqs = [if_results[s] for s in stims]
        
        if_ax = pynml.generate_plot([stims_pA],
                            [freqs], 
                            "Firing frequency versus injected current for: %s"%nml2_file, 
                            colors = [if_iv_color], 
                            linestyles=['-'],
                            markers=['o'],
                            linewidths = [linewidth],
                            xaxis = 'Input current (pA)' if label_xaxis else ' ', 
                            yaxis = 'Firing frequency (Hz)' if label_yaxis else '',
                            xlim = xlim_if,
                            ylim = ylim_if,
                            show_xticklabels = label_xaxis,
                            show_yticklabels = label_yaxis,
                            font_size = font_size,
                            bottom_left_spines_only = bottom_left_spines_only,
                            grid = grid,
                            show_plot_already=False,
                            save_figure_to = save_if_figure_to,
                            title_above_plot = title_above_plot,
                            verbose=verbose)
                            
        if save_if_data_to:
            with open(save_if_data_to,'w') as if_file:
                for i in range(len(stims_pA)):
                    if_file.write("%s\t%s\n"%(stims_pA[i],freqs[i]))
    if plot_iv:
        
        stims = sorted(iv_results.keys())
        stims_pA = [ii*1000 for ii in sorted(iv_results.keys())]
        vs = [iv_results[s] for s in stims]
        
        xs = []
        ys = []
        xs.append([])
        ys.append([])
        
        for si in range(len(stims)):
            stim = stims[si]
            if len(custom_amps_nA)==0 and si>1 and (stims[si]-stims[si-1])>step_nA*1.01:
                xs.append([])
                ys.append([])
                
            xs[-1].append(stim*1000)
            ys[-1].append(iv_results[stim])
            
        iv_ax = pynml.generate_plot(xs,
                            ys, 
                            "V at %sms versus I below threshold for: %s"%(end_stim,nml2_file), 
                            colors = [if_iv_color for s in xs], 
                            linestyles=['-' for s in xs],
                            markers=['o' for s in xs],
                            xaxis = 'Input current (pA)' if label_xaxis else '', 
                            yaxis = 'Membrane potential (mV)' if label_yaxis else '', 
                            xlim = xlim_iv,
                            ylim = ylim_iv,
                            show_xticklabels = label_xaxis,
                            show_yticklabels = label_yaxis,
                            font_size = font_size,
                            linewidths = [linewidth for s in xs],
                            bottom_left_spines_only = bottom_left_spines_only,
                            grid = grid,
                            show_plot_already=False,
                            save_figure_to = save_iv_figure_to,
                            title_above_plot = title_above_plot,
                            verbose=verbose)
                            
                            
        if save_iv_data_to:
            with open(save_iv_data_to,'w') as iv_file:
                for i in range(len(stims_pA)):
                    iv_file.write("%s\t%s\n"%(stims_pA[i],vs[i]))
    
    if show_plot_already:
        from matplotlib import pyplot as plt
        plt.show()
        
    if return_axes:
        return traces_ax, if_ax, iv_ax
        
    return if_results


def analyse_spiketime_vs_dt(nml2_file, 
                            target,
                            duration,
                            simulator,
                            cell_v_path,
                            dts,
                            verbose=False,
                            spike_threshold_mV = 0,
                            show_plot_already=True,
                            save_figure_to=None,
                            num_of_last_spikes=None):
                                
    from pyelectro.analysis import max_min
    import numpy as np
    
    all_results = {}
    
    dts=list(np.sort(dts))
    
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
                                   copy_neuroml = False)
                                   
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
    colors=[]
    spike_times_final=[]
    array_of_num_of_spikes=[]
    
    for dt in dts:
        t = all_results[dt]['t']
        v = all_results[dt][cell_v_path]
        xs.append(t)
        ys.append(v)
        labels.append(dt)
        
        mm = max_min(v, t, delta=0, peak_threshold=spike_threshold_mV)
        
        spike_times = mm['maxima_times']
        
        spike_times_final.append(spike_times)
        
        array_of_num_of_spikes.append(len(spike_times))
        
    max_num_of_spikes=max(array_of_num_of_spikes)
    
    min_dt_spikes=spike_times_final[0]
    
    bound_dts=[math.log(dts[0]),math.log(dts[-1])]
    
    if num_of_last_spikes == None:
    
       num_of_spikes=len(min_dt_spikes)
       
    else:
       
       if len(min_dt_spikes) >=num_of_last_spikes:
       
          num_of_spikes=num_of_last_spikes
          
       else:
       
          num_of_spikes=len(min_dt_spikes)
    
    spike_indices=[(-1)*ind for ind in range(1,num_of_spikes+1) ]
    
    if len(min_dt_spikes) > abs(spike_indices[-1]):
    
       earliest_spike_time=min_dt_spikes[spike_indices[-1]-1]
       
    else:
     
       earliest_spike_time=min_dt_spikes[spike_indices[-1]]
       
    for spike_ind in range(0,max_num_of_spikes):
    
        spike_time_values=[]
        
        dt_values=[]
        
        for dt in range(0,len(dts)):
        
            if spike_times_final[dt] !=[]:
           
               if len(spike_times_final[dt]) >= spike_ind+1:
               
                  if spike_times_final[dt][spike_ind] >= earliest_spike_time:
             
                     spike_time_values.append(spike_times_final[dt][spike_ind])
               
                     dt_values.append(math.log(dts[dt]))       
        
        linestyles.append('')
               
        markers.append('o')
       
        colors.append('g')
       
        spxs.append(dt_values)
       
        spys.append(spike_time_values)
    
    for last_spike_index in spike_indices:
       
       vertical_line=[min_dt_spikes[last_spike_index],min_dt_spikes[last_spike_index] ]
          
       spxs.append(bound_dts)
          
       spys.append(vertical_line)
          
       linestyles.append('--')
          
       markers.append('')
       
       colors.append('k')
    
    pynml.generate_plot(spxs, 
          spys, 
          "Spike times vs dt",
          colors=colors,
          linestyles = linestyles,
          markers = markers,
          xaxis = 'ln ( dt (ms) )', 
          yaxis = 'Spike times (s)',
          show_plot_already=show_plot_already,
          save_figure_to=save_figure_to) 
    
    if verbose:
        pynml.generate_plot(xs, 
                  ys, 
                  "Membrane potentials in %s for %s"%(simulator,dts),
                  labels = labels,
                  show_plot_already=show_plot_already,
                  save_figure_to=save_figure_to)
                  

