
from pyneuroml.analysis import analyse_spiketime_vs_dt
    
from matplotlib import pyplot as plt

nml2_file = 'NML2_SingleCompHHCell.nml'
target = "net1"

dts = [0.1,0.05,0.01,0.005,0.001,0.0005,0.0001]
#dts = [0.05,0.01]

analyse_spiketime_vs_dt(nml2_file,
                        target,
                        300,
                        'jNeuroML',
                        'hhpop[0]/v',
                        dts,
                        verbose=True,
                        show_plot_already=False)

analyse_spiketime_vs_dt(nml2_file,
                        target,
                        300,
                        'jNeuroML_NEURON',
                        'hhpop[0]/v',
                        dts,
                        verbose=True,
                        show_plot_already=False)
                        
plt.show()

