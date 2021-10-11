from matplotlib import pyplot as plt
import sys

from pyneuroml.analysis import analyse_spiketime_vs_dt


nml2_file = "NML2_SingleCompHHCell.nml"
target = "net1"

dts = [0.1, 0.05, 0.01, 0.005, 0.001, 0.0005, 0.0001]
dts = [0.05, 0.01, 0.005]

nogui = "-nogui" in sys.argv  # Used to supress GUI in tests for Travis-CI

analyse_spiketime_vs_dt(
    nml2_file,
    target,
    300,
    "jNeuroML",
    "hhpop[0]/v",
    dts,
    verbose=True,
    show_plot_already=False,
)
if not nogui:
    analyse_spiketime_vs_dt(
        nml2_file,
        target,
        300,
        "jNeuroML_NEURON",
        "hhpop[0]/v",
        dts,
        verbose=True,
        show_plot_already=False,
    )

if not nogui:
    plt.show()
