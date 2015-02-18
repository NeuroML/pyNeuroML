set -e

### Test script for pyNeuroML

################################################
##   Create a temporary folder for tests

export PYNML_TEST="test_models"

if [ ! -d $PYNML_TEST ]; then
    mkdir $PYNML_TEST
fi 

cd $PYNML_TEST


################################################
##   Clone main NeuroML 2 repository


if [ ! -d 'NeuroML2' ]; then
    git clone https://github.com/NeuroML/NeuroML2.git
fi 


################################################
##   Run some examples with jNeuroML

cd NeuroML2/LEMSexamples
pynml LEMS_NML2_Ex5_DetCell.xml -nogui


################################################
##   Validate with jNeuroML

cd ../examples

pynml -validate NML2_SynapseTypes.nml


################################################
##   Try running some of the examples

cd ../../../examples

run_neuron_examples=false

if [[ ($# -eq 1) && ($1 == '-neuron') ]]; then
    run_neuron_examples=true
fi

#  Run an example with jNeuroML
python run_jneuroml_plot_matplotlib.py -nogui -noneuron

#  Generate a frequency vs current plot
##python generate_if_curve.py -nogui

if [ "$run_neuron_examples" == true ]; then
    
    # Export NeuroML v1 from NEURON example
    python export_neuroml1.py
    
    # Export NeuroML v2 from NEURON example
    python export_neuroml2.py

fi
    





