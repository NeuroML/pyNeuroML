from pyneuroml import pynml

from matplotlib import pyplot as plt

example_lems_file = 'LEMS_NML2_Ex1_HH.xml'

results = pynml.run_lems_with_jneuroml(example_lems_file, nogui=True, load_saved_data=True)

for file_contents in results.keys():

    plt.xlabel('Time (ms)')
    plt.ylabel('Membrane potential (mV)')
    plt.grid('on')

    plt.plot(results[file_contents]['t'],results[file_contents]['v'])
    plt.show()