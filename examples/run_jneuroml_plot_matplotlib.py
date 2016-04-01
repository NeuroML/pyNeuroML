import sys

from pyneuroml import pynml


####################################################################
#   Choose a LEMS/NeuroML2 file and run it with jNeuroML

example_lems_file = 'LEMS_NML2_Ex5_DetCell.xml'

results1 = pynml.run_lems_with_jneuroml(example_lems_file, nogui=True, load_saved_data=True)



####################################################################
#   Convert LEMS/NeuroML2 file to NEURON with jNeuroML & run


if not '-noneuron' in sys.argv:  # To allow skipping of this for ease of testing

    results2 = pynml.run_lems_with_jneuroml_neuron(example_lems_file, nogui=True, load_saved_data=True)



####################################################################
#   Reload & plot results

if not '-nogui' in sys.argv:
    
    from matplotlib import pyplot as plt

    for key in results1.keys():

        plt.xlabel('Time (ms)')
        plt.ylabel('...')
        plt.grid('on')

        if key != 't':
            plt.plot(results1['t'],results1[key], label="jNeuroML: "+key)
            if not '-noneuron' in sys.argv:
                plt.plot(results2['t'],results2[key], label="jNeuroML_NEURON: "+key)
        plt.legend(loc=2, fontsize = 'x-small')


    plt.show()
