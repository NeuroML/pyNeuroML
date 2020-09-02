'''

Example to create some new LEMS files for running NML2 model & recording channel currents

'''

from pyneuroml.lems import generate_lems_file_for_neuroml
import neuroml.writers as writers
import pprint; pp = pprint.PrettyPrinter(depth=6)

if __name__ == '__main__':
    
    root_dir = 'test_data/ca1'
    import neuroml
    
    nml_doc = neuroml.NeuroMLDocument(id="IafNet")
    reference = 'TestOLMChannels'
    
    incl = neuroml.IncludeType('cells/olm.cell.nml')
    nml_doc.includes.append(incl)
    
    net = neuroml.Network(id=reference)
    net.notes = "A test network model: %s"%reference
    net.temperature = '35degC'

    nml_doc.networks.append(net)
    
    cell_comp = 'olmcell'

    pop0 = neuroml.Population(id="olmpop",
                      component=cell_comp,
                      size=1, 
                      type="populationList")
                      
    inst = neuroml.Instance(id=0)
    pop0.instances.append(inst)
    inst.location = neuroml.Location(x=0, y=0, z=0)

    net.populations.append(pop0)
    
    pg = neuroml.PulseGenerator(id="pulseGen0",
                    delay="100ms",
                    duration="800ms",
                    amplitude="100 pA")

    nml_doc.pulse_generators.append(pg)

    input_list = neuroml.InputList(id='il',
                         component=pg.id,
                         populations=pop0.id)
                         
    input = neuroml.Input(id=0, 
                  target="../%s/%i/%s"%(pop0.id, 0, cell_comp), 
                  destination="synapses")  
                  
    input_list.input.append(input)  

    net.input_lists.append(input_list)

    
    nml_file = '%s/%s.net.nml'%(root_dir,reference)
    writers.NeuroMLWriter.write(nml_doc, nml_file)


    print("Written network file to: "+nml_file)
    
    ############################################
    ###  Create the LEMS file with helper method
    
    
    sim_id = 'Sim%s'%reference
    target = net.id
    duration=1000
    dt = 0.025
    lems_file_name = 'LEMS_%s.xml'%sim_id
    target_dir = root_dir
    
    generate_lems_file_for_neuroml(sim_id, 
                                   nml_file, 
                                   target, 
                                   duration, 
                                   dt, 
                                   lems_file_name,
                                   target_dir,
                                   include_extra_files = [],
                                   gen_plots_for_all_v = True,
                                   plot_all_segments = True,
                                   gen_plots_for_quantities = {},   #  Dict with displays vs lists of quantity paths
                                   gen_plots_for_only_populations = [],   #  List of populations, all pops if = []
                                   gen_saves_for_all_v = True,
                                   save_all_segments = True,
                                   gen_saves_for_only_populations = [],  #  List of populations, all pops if = []
                                   gen_saves_for_quantities = {},   #  Dict with file names vs lists of quantity paths
                                   gen_spike_saves_for_all_somas = True,
                                   report_file_name = 'report.txt',
                                   copy_neuroml = True,
                                   verbose=True)
                                   

        