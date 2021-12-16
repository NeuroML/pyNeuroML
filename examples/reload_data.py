import sys
from pyneuroml import pynml


example_lems_file = "LEMS_NML2_Ex5_DetCell.xml"

pynml.reload_saved_data(example_lems_file, plot=True, show_plot_already=False)


example_lems_file = "LEMS_NML2_Ex9_FN.xml"

pynml.reload_saved_data(example_lems_file, plot=True, show_plot_already=False)


if "-nogui" not in sys.argv:
    from matplotlib import pyplot as plt

    plt.show()
