# Test script for pyNeuroML

export PYNML_TEST="test_models"

if [ ! -d $PYNML_TEST ]; then
    mkdir $PYNML_TEST
fi 

cd $PYNML_TEST

git clone https://github.com/NeuroML/NeuroML2.git

cd NeuroML2/LEMSexamples

pynml LEMS_NML2_Ex5_DetCell.xml -nogui





