import sys
from pyneuroml import pynml


####################################################################
#   Choose a LEMS/NeuroML2 file and run it with jNeuroML

example_lems_file = "LEMS_NML2_Ex5_DetCell.xml"

print("Running with jNeuroML...")
results1 = pynml.run_lems_with_jneuroml(
    example_lems_file, nogui=True, load_saved_data=True
)


####################################################################
#   Convert LEMS/NeuroML2 file to NEURON with jNeuroML & run

if "-noneuron" not in sys.argv:  # To allow skipping of this for ease of testing
    print("Running with jNeuroML_NEURON...")
    results2 = pynml.run_lems_with_jneuroml_neuron(
        example_lems_file, nogui=True, load_saved_data=True, verbose=True
    )


####################################################################
#   Convert LEMS/NeuroML2 file to NEURON with jNeuroML & run


if "-brian2" in sys.argv:  # To allow skipping of this for ease of testing
    print("Running with jNeuroML_Brian2...")
    results3 = pynml.run_lems_with_jneuroml_brian2(
        example_lems_file, nogui=True, load_saved_data=True, verbose=True
    )


####################################################################
#   Run LEMS in EDEN


if "-eden" in sys.argv:  # To allow skipping of this for ease of testing
    print("Running with EDEN...")
    results4 = pynml.run_lems_with_eden(
        example_lems_file, load_saved_data=True, verbose=True
    )


####################################################################
#   Reload & plot results

if "-nogui" not in sys.argv:
    from matplotlib import pyplot as plt

    for key in results1.keys():
        plt.xlabel("Time (ms)")
        plt.ylabel("")
        plt.grid("on")

        if key != "t":
            plt.plot(results1["t"], results1[key], label="jNeuroML: " + key)
            if "-noneuron" not in sys.argv:
                plt.plot(results2["t"], results2[key], label="jNeuroML_NEURON: " + key)
            if "-brian2" in sys.argv:
                plt.plot(results3["t"], results3[key], label="jNeuroML_Brian2: " + key)
            if "-eden" in sys.argv:
                plt.plot(results4["t"], results4[key], label="EDEN: " + key)
        plt.legend(loc=2, fontsize="x-small")

    plt.show()
