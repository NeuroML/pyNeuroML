'''

    Still under development!!
    
    Subject to change without notice!!
    
'''

import os.path
import sys

from collections import OrderedDict
from pyneuroml.pynml import read_neuroml2_file, write_neuroml2_file, print_comment_v

from NeuroMLSimulation import NeuroMLSimulation

import pprint
pp = pprint.PrettyPrinter(indent=4)

class NeuroMLController():

    def __init__(self, 
                 ref,  
                 neuroml_file, 
                 target, 
                 sim_time=1000, 
                 dt=0.05, 
                 simulator='jNeuroML', 
                 generate_dir = './'):
        
        self.ref = ref
        self.neuroml_file = neuroml_file
        self.target = target
        self.sim_time = sim_time
        self.dt = dt
        self.simulator = simulator
        self.generate_dir = generate_dir if generate_dir.endswith('/') else generate_dir+'/'
        
        self.count = 0
        

    def run(self,candidates,parameters):
        """
        Run simulation for each candidate
        
        This run method will loop through each candidate and run the simulation
        corresponding to it's parameter values. It will populate an array called
        traces with the resulting voltage traces for the simulation and return it.
        """

        traces = []
        for candidate in candidates:
            sim_var = dict(zip(parameters,candidate))
            print_comment_v('\n\n  - RUN %i; variables: %s\n'%(self.count,sim_var))
            self.count+=1
            t,v = self.run_individual(sim_var)
            traces.append([t,v])

        return traces

        
    
    def run_individual(self, sim_var, show=False):
        """
        Run an individual simulation.

        The candidate data has been flattened into the sim_var dict. The
        sim_var dict contains parameter:value key value pairs, which are
        applied to the model before it is simulated.

        """
        
        nml_doc = read_neuroml2_file(self.neuroml_file, 
                                     include_includes=True,
                                     verbose = True,
                                     already_included = [])
                                     
        
        for var_name in sim_var.keys():
            words = var_name.split('/')
            type, id1 = words[0].split(':')
            if ':' in words[1]:
                variable, id2 = words[1].split(':')
            else:
                variable = words[1]
                id2 = None
            
            units = words[2]
            value = sim_var[var_name]
            
            print_comment_v('  Changing value of %s (%s) in %s (%s) to: %s %s'%(variable, id2, type, id1, value, units))
            
            if type == 'cell':
                cell = None
                for c in nml_doc.cells:
                    if c.id == id1:
                        cell = c
                        
                if variable == 'channelDensity':
                    
                    chanDens = None
                    for cd in cell.biophysical_properties.membrane_properties.channel_densities:
                        if cd.id == id2:
                            chanDens = cd
                            
                    chanDens.cond_density = '%s %s'%(value, units)
                    
                elif variable == 'erev_id': # change all values of erev in channelDensity elements with only this id
                    
                    chanDens = None
                    for cd in cell.biophysical_properties.membrane_properties.channel_densities:
                        if cd.id == id2:
                            chanDens = cd
                            
                    chanDens.erev = '%s %s'%(value, units)
                    
                elif variable == 'erev_ion': # change all values of erev in channelDensity elements with this ion
                    
                    chanDens = None
                    for cd in cell.biophysical_properties.membrane_properties.channel_densities:
                        if cd.ion == id2:
                            chanDens = cd
                            
                    chanDens.erev = '%s %s'%(value, units)
                    
                elif variable == 'specificCapacitance': 
                    
                    specCap = None
                    for sc in cell.biophysical_properties.membrane_properties.specific_capacitances:
                        if (sc.segment_groups == None and id2 == 'all') or sc.segment_groups == id2 :
                            specCap = sc
                            
                    specCap.value = '%s %s'%(value, units)
                    
                else:
                    print_comment_v('Unknown variable (%s) in variable expression: %s'%(variable, var_name))
                    exit()
                
            elif type == 'izhikevich2007Cell':
                izhcell = None
                for c in nml_doc.izhikevich2007_cells:
                    if c.id == id1:
                        izhcell = c
                        
                izhcell.__setattr__(variable, '%s %s'%(value, units))
                
            else:
                print_comment_v('Unknown type (%s) in variable expression: %s'%(type, var_name))
       
                            
                                     
        new_neuroml_file =  '%s/%s'%(self.generate_dir,os.path.basename(self.neuroml_file))
        if new_neuroml_file == self.neuroml_file:
            print_comment_v('Cannot use a directory for generating into (%s) which is the same location of the NeuroML file (%s)!'% \
                      (self.neuroml_file, self.generate_dir))
                      
        write_neuroml2_file(nml_doc, new_neuroml_file)
    
            
        sim = NeuroMLSimulation(self.ref, 
                             neuroml_file = new_neuroml_file,
                             target = self.target,
                             sim_time = self.sim_time, 
                             dt = self.dt, 
                             simulator = self.simulator, 
                             generate_dir = self.generate_dir)
        
        sim.go()
        
        if show:
            sim.show()
    
        return sim.t, sim.volts


if __name__ == '__main__':
    
    sim_time = 700
    dt = 0.05
    
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    
    nogui = '-nogui' in sys.argv
    
    if '-net' in sys.argv:
        ''' Not yet... '''
        
    else:
    
        cont = NeuroMLController('TestHH', 
                                '../../examples/test_data/HHCellNetwork.net.nml',
                                'HHCellNetwork',
                                sim_time, 
                                dt, 
                                'jNeuroML', 
                                'temp/')

        sim_vars = OrderedDict([('cell:hhcell/channelDensity:naChans/mS_per_cm2', 100),
                                ('cell:hhcell/channelDensity:kChans/mS_per_cm2', 20)])

        t, v = cont.run_individual(sim_vars, show=(not nogui))
        
        from pyelectro import analysis
        
        analysis_var={'peak_delta':0,'baseline':0,'dvdt_threshold':0, 'peak_threshold':0}
        
        data_analysis=analysis.NetworkAnalysis(v,
                                               t,
                                               analysis_var,
                                               start_analysis=0,
                                               end_analysis=sim_time)
                                                   
        analysed = data_analysis.analyse()     
        
        pp.pprint(analysed)