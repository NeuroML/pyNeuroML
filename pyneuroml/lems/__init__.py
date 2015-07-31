import os.path
from LEMSSimulation import LEMSSimulation

import shutil
import os
from pyneuroml.pynml import read_neuroml2_file, get_next_hex_color

def generate_lems_file_for_neuroml(sim_id, 
                                   neuroml_file, 
                                   target, 
                                   duration, 
                                   dt, 
                                   lems_file_name,
                                   target_dir,
                                   gen_plots_for_all_v = True,
                                   gen_saves_for_all_v = True,
                                   copy_neuroml = True):
    
    file_name_full = '%s/%s'%(target_dir,lems_file_name)
    
    print('Going to create new LEMS file at: %s for NeuroML 2 file: %s'%(file_name_full,neuroml_file))
    
    ls = LEMSSimulation(sim_id, duration, dt, target)
    
    nml_doc = read_neuroml2_file(neuroml_file)
    
    quantities_saved = []
    
    if not copy_neuroml:
        ls.include_neuroml2_file(neuroml_file)
    else:
        if os.path.abspath(os.path.dirname(neuroml_file))!=os.path.abspath(target_dir):
            shutil.copy(neuroml_file, target_dir)
        
        neuroml_file_name = os.path.basename(neuroml_file)
        
        ls.include_neuroml2_file(neuroml_file_name, include_included=False)
        
        
        for include in nml_doc.includes:
            incl_curr = '%s/%s'%(os.path.dirname(neuroml_file),include.href)
            print(' - Including %s located at %s'%(include.href, incl_curr))
            shutil.copy(incl_curr, target_dir)
            ls.include_neuroml2_file(include.href, include_included=False)
            
            sub_doc = read_neuroml2_file(incl_curr)
        
            for include in sub_doc.includes:
                incl_curr = '%s/%s'%(os.path.dirname(neuroml_file),include.href)
                print(' -- Including %s located at %s'%(include.href, incl_curr))
                shutil.copy(incl_curr, target_dir)
                ls.include_neuroml2_file(include.href, include_included=False)
                
                
    if gen_plots_for_all_v or gen_saves_for_all_v:
        
        for network in nml_doc.networks:
            for population in network.populations:
                size = population.size
                component = population.component
                
                quantity_template = "%s[%i]/v"
                
                if gen_plots_for_all_v:
                    print('Generating %i plots for %s in population %s'%(size, component, population.id))
   
                    disp0 = 'DispPop__%s'%population.id
                    ls.create_display(disp0, "Voltages of %s"%disp0, "-90", "50")
                    for i in range(size):
                        quantity = quantity_template%(population.id, i)
                        ls.add_line_to_display(disp0, "v %s"%quantity, quantity, "1mV", get_next_hex_color())
                
                if gen_saves_for_all_v:
                    print('Saving %i values of v for %s in population %s'%(size, component, population.id))
   
                    of0 = 'Volts_file__%s'%population.id
                    ls.create_output_file(of0, "%s.%s.v.dat"%(sim_id,population.id))
                    for i in range(size):
                        quantity = quantity_template%(population.id, i)
                        ls.add_column_to_output_file(of0, 'v_%s'%quantity, quantity)
                        quantities_saved.append(quantity)
                        
        
    ls.save_to_file(file_name=file_name_full)
    
    return quantities_saved
