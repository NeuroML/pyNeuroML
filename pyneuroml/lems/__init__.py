import os.path
from pyneuroml.lems.LEMSSimulation import LEMSSimulation

import shutil
import os
from pyneuroml.pynml import read_neuroml2_file, get_next_hex_color, print_comment_v, print_comment
import random

def generate_lems_file_for_neuroml(sim_id, 
                                   neuroml_file, 
                                   target, 
                                   duration, 
                                   dt, 
                                   lems_file_name,
                                   target_dir,
                                   gen_plots_for_all_v = True,
                                   gen_saves_for_all_v = True,
                                   copy_neuroml = True,
                                   seed=None):
                                       
    
    if seed:
        random.seed(seed) # To ensure same LEMS file (e.g. colours of plots) are generated every time for the same input
    
    file_name_full = '%s/%s'%(target_dir,lems_file_name)
    
    print_comment_v('Creating LEMS file at: %s for NeuroML 2 file: %s'%(file_name_full,neuroml_file))
    
    ls = LEMSSimulation(sim_id, duration, dt, target)
    
    nml_doc = read_neuroml2_file(neuroml_file)
    
    quantities_saved = []
    
    if not copy_neuroml:
        rel_nml_file = os.path.relpath(os.path.abspath(neuroml_file), os.path.abspath(target_dir))
        print_comment_v("Including existing NeuroML file (%s) as: %s"%(neuroml_file, rel_nml_file))
        ls.include_neuroml2_file(rel_nml_file, include_included=True, relative_to_dir=os.path.abspath(target_dir))
    else:
        if os.path.abspath(os.path.dirname(neuroml_file))!=os.path.abspath(target_dir):
            shutil.copy(neuroml_file, target_dir)
        
        neuroml_file_name = os.path.basename(neuroml_file)
        
        ls.include_neuroml2_file(neuroml_file_name, include_included=False)
        
        
        for include in nml_doc.includes:
            incl_curr = '%s/%s'%(os.path.dirname(neuroml_file),include.href)
            print_comment_v(' - Including %s located at %s'%(include.href, incl_curr))
            shutil.copy(incl_curr, target_dir)
            ls.include_neuroml2_file(include.href, include_included=False)
            
            sub_doc = read_neuroml2_file(incl_curr)
        
            for include in sub_doc.includes:
                incl_curr = '%s/%s'%(os.path.dirname(neuroml_file),include.href)
                print_comment_v(' -- Including %s located at %s'%(include.href, incl_curr))
                shutil.copy(incl_curr, target_dir)
                ls.include_neuroml2_file(include.href, include_included=False)
                
                
    if gen_plots_for_all_v or gen_saves_for_all_v:
        
        for network in nml_doc.networks:
            for population in network.populations:
                size = population.size
                component = population.component
                
                quantity_template = "%s[%i]/v"
                if population.type and population.type == 'populationList':
                    quantity_template = "%s/%i/"+component+"/v"
                
                if gen_plots_for_all_v:
                    print_comment('Generating %i plots for %s in population %s'%(size, component, population.id))
   
                    disp0 = 'DispPop__%s'%population.id
                    ls.create_display(disp0, "Voltages of %s"%disp0, "-90", "50")
                    for i in range(size):
                        quantity = quantity_template%(population.id, i)
                        ls.add_line_to_display(disp0, "v %s"%safe_variable(quantity), quantity, "1mV", get_next_hex_color())
                
                if gen_saves_for_all_v:
                    print_comment('Saving %i values of v for %s in population %s'%(size, component, population.id))
   
                    of0 = 'Volts_file__%s'%population.id
                    ls.create_output_file(of0, "%s.%s.v.dat"%(sim_id,population.id))
                    for i in range(size):
                        quantity = quantity_template%(population.id, i)
                        ls.add_column_to_output_file(of0, 'v_%s'%safe_variable(quantity), quantity)
                        quantities_saved.append(quantity)
                        
        
    ls.save_to_file(file_name=file_name_full)
    
    return quantities_saved

# Mainly for NEURON etc.
def safe_variable(quantity):
    return quantity.replace(' ','_').replace('[','_').replace(']','_').replace('/','_')