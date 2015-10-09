'''

    Still under developemnt!!

    Subject to change without notice!!

'''


from pyneuroml.tune.NeuroMLTuner import run_optimisation
import sys


if __name__ == '__main__':
    
    nogui = '-nogui' in sys.argv
        

    parameters = ['cell:hhcell/channelDensity:naChans/mS_per_cm2',
                  'cell:hhcell/channelDensity:kChans/mS_per_cm2']

    #above parameters will not be modified outside these bounds:
    min_constraints = [50,   10]
    max_constraints = [200,  60]


    max_peak_no = 'hhpop[0]/v:max_peak_no'

    weights = {max_peak_no: 1}

    target_data = {max_peak_no:  30}

    simulator  = 'jNeuroML_NEURON'
    simulator  = 'jNeuroML'

    run_optimisation(prefix =           'TestHHpy', 
                     neuroml_file =     'test_data/HHCellNetwork.net.nml',
                     target =           'HHCellNetwork',
                     parameters =       parameters,
                     max_constraints =  max_constraints,
                     min_constraints =  min_constraints,
                     weights =          weights,
                     target_data =      target_data,
                     sim_time =         700,
                     population_size =  10,
                     max_evaluations =  20,
                     num_selected =     5,
                     num_offspring =    5,
                     mutation_rate =    0.5,
                     num_elites =       1,
                     simulator =        simulator,
                     nogui =            nogui)



