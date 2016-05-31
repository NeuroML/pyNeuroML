
import sys

from pyneuroml import pynml
from pyneuroml.lems.LEMSSimulation import LEMSSimulation
import neuroml as nml

from pyneuroml.pynml import print_comment_v
from pyneuroml.lems import generate_lems_file_for_neuroml

import numpy as np

def generate_Vm_vs_time_plot(nml2_file, 
                                        cell_id, 
                                        inj_amp_nA = 5.0,
                                        delay_ms = 20,
                                        inj_dur_ms = 0.5,
                                        sim_dur_ms = 100, 
                                        dt = 0.05,
                                        temperature = "32degC",
                                        spike_threshold_mV=0.,
                                        plot_voltage_traces=False,
                                        show_plot_already=True, 
                                        simulator="jNeuroML",
                                        include_included=True):
                                            
	# simulation parameters                                            
    nogui = '-nogui' in sys.argv  # Used to supress GUI in tests for Travis-CI
    
    ref = "Test"
    print_comment_v("Generating Vm(mV) vs Time(ms) plot for cell %s in %s using %s (Inj %snA / %sms dur after %sms delay)"%
        (cell_id, nml2_file, simulator, inj_amp_nA, inj_dur_ms, delay_ms))
    
    sim_id = 'Vm_%s'%ref
    duration = sim_dur_ms
    ls = LEMSSimulation(sim_id, sim_dur_ms, dt)
    
    ls.include_neuroml2_file(nml2_file, include_included=include_included)
    ls.assign_simulation_target('network')
    nml_doc = nml.NeuroMLDocument(id=cell_id)
    
    net = nml.Network(id="network")
    nml_doc.networks.append(net)
    
    input_id = ("input_%s"%str(inj_amp_nA).replace('.','_'))
    pg = nml.PulseGenerator(id=input_id,
                                    delay="0ms",
                                    duration='%sms'%sim_dur_ms,
                                    amplitude='%spA'%inj_amp_nA)
    nml_doc.pulse_generators.append(pg)
    
    # Add these to cells
    input_list = nml.InputList(id=input_id,
                                 component=pg.id)
    input = nml.Input(id='0',  target=cell_id,
                              destination="synapses")  
    
    input_list.input.append(input)
    #???.input_lists.append(input_list)
    
    pop_id = 'hhpop'
    pop = nml.Population(id=pop_id, component='hhcell', size=1)
    net.populations.append(pop)
    
    
    sim_file_name = '%s.sim.nml'%sim_id
    pynml.write_neuroml2_file(nml_doc, sim_file_name)
    ls.include_neuroml2_file(sim_file_name)


    disp0 = 'Voltage_display'
    ls.create_display(disp0,"Voltages", "-90", "50")
    ls.add_line_to_display(disp0, "V", "hhpop[0]/v", scale='1mV')
    
    of0 = 'Volts_file'
    ls.create_output_file(of0, "%s.v.dat"%sim_id)
    
    lems_file_name = ls.save_to_file()
    '''
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
                                                
 
    if show_plot_already:
        from matplotlib import pyplot as plt
        plt.show()'''
        
        
    return of0     
    

    
generate_Vm_vs_time_plot('NML2_SingleCompHHCell.nml', 'hhcell', plot_voltage_traces =  True)