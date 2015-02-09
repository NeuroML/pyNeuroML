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
##   Try running one of the examples

cd ../../../examples

python run_jneuroml_plot_matplotlib.py -nogui -noneuron





