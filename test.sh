set -e

### Test script for pyNeuroML

cd examples

echo
echo "################################################"
echo "##   Executing examples with jNeuroML"

pynml LEMS_NML2_Ex5_DetCell.xml -nogui


echo
echo "################################################"
echo "##   Validate with jNeuroML"

pynml -validate NML2_SingleCompHHCell.nml


echo
echo "################################################"
echo "##   Running some of the examples"
  
run_neuron_examples=false

if [[ ($# -eq 1) && ($1 == '-neuron') ]]; then
    run_neuron_examples=true
fi

#  Run an example with jNeuroML
python run_jneuroml_plot_matplotlib.py -nogui -noneuron


    
echo
echo "################################################"
echo "##   Test analysis of NeuroML2 channel"

pynml-channelanalysis NaConductance.channel.nml -nogui

    
echo
echo "################################################"
echo "##   Generate a frequency vs current plot"

python generate_if_curve.py -nogui


# Only run these if NEURON is installed & -neuron flag is used
if [ "$run_neuron_examples" == true ]; then

    echo
    echo "################################################"
    echo "##   Try exporting morphologies to NeuroML from NEURON"

        # Export NeuroML v1 from NEURON example
        python export_neuroml1.py

        # Export NeuroML v2 from NEURON example
        python export_neuroml2.py


    echo
    echo "################################################"
    echo "##   Test analysis of channel in mod file"

        nrnivmodl
        pynml-modchananalysis -stepV 20  NaConductance  -dt 0.01 -nogui

fi

echo
echo "################################################"
echo "##   Finished all tests! "
echo "################################################"