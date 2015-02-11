from pyneuroml import pynml
from pyneuroml.lems.LEMSSimulation import LEMSSimulation
import neuroml as nml

def generate_current_vs_frequency_curve(nml2_file, 
                                        cell_id, 
                                        start_amp_nA, 
                                        end_amp_nA, 
                                        step_nA, 
                                        analysis_duration, 
                                        analysis_delay, 
                                        dt = 0.05,
                                        plot_voltage_traces=False):
    
    sim_id = 'iv_%s'%cell_id
    duration = analysis_duration+analysis_delay
    ls = LEMSSimulation(sim_id, duration, dt)
    
    ls.include_neuroml2_file(nml2_file)
    
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
    net = nml.Network(id=net_id)
    ls.assign_simulation_target(net_id)
    net_doc = nml.NeuroMLDocument(id=net.id)
    net_doc.networks.append(net)
    net.populations.append(pop)
    
    for i in range(number_cells):
        stim_amp = "%snA"%stims[i]
        input_id = ("input_%s"%stim_amp).replace('.','_')
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
    
    results = pynml.run_lems_with_jneuroml(lems_file_name, 
                                            nogui=True, 
                                            load_saved_data=True, 
                                            plot=plot_voltage_traces)