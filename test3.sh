set -e

sudo cp /usr/local/bin/pynml /usr/local/bin/pynml2
sudo python3 setup.py install
sudo cp /usr/local/bin/pynml /usr/local/bin/pynml3
sudo cp /usr/local/bin/pynml2 /usr/local/bin/pynml
  
run_neuron_examples=false

if [[ ($# -eq 1) && ($1 == '-neuron') ]]; then
    run_neuron_examples=true
fi

### Test script for pyNeuroML

cd examples


echo
echo "################################################"
echo "##   Executing examples with jNeuroML"

pynml3 LEMS_NML2_Ex5_DetCell.xml -nogui



echo
echo "################################################"
echo "##   Validate with jNeuroML"

pynml3 -validate NML2_SingleCompHHCell.nml



echo
echo "################################################"
echo "##   Test some conversions"

pynml3 NML2_SingleCompHHCell.nml -svg
pynml3 NML2_SingleCompHHCell.nml -png
pynml3 LEMS_NML2_Ex5_DetCell.xml -sedml
pynml3 LEMS_NML2_Ex9_FN.xml -dlems
pynml3 LEMS_NML2_Ex9_FN.xml -brian
pynml3 LEMS_NML2_Ex5_DetCell.xml -neuron
pynml3 LEMS_NML2_Ex9_FN.xml -vertex
pynml3 LEMS_NML2_Ex9_FN.xml -xpp
pynml3 LEMS_NML2_Ex9_FN.xml -dnsim
pynml3 LEMS_NML2_Ex9_FN.xml -cvode
pynml3 LEMS_NML2_Ex9_FN.xml -matlab
pynml3 LEMS_NML2_Ex9_FN.xml -nineml
pynml3 LEMS_NML2_Ex9_FN.xml -spineml
pynml3 LEMS_NML2_Ex9_FN.xml -sbml



echo
echo "################################################"
echo "##   Running some of the examples"

#  Run an example with jNeuroML
python3 run_jneuroml_plot_matplotlib.py -nogui -noneuron


#  Run tests on units
python3 units.py

#  Run test for generating LEMS file
python3 create_new_lems_file.py

#  Run test for generating LEMS file
python3 Vm_plot.py -nogui


    
echo
echo "################################################"
echo "##   Test analysis of NeuroML2 channel"

if [ "$TRAVIS_PYTHON_VERSION" != "2.6" ]; then 
    pynml-channelanalysis NaConductance.channel.nml -nogui
    pynml-channelanalysis NaConductance.channel.nml -ivCurve -erev 55 -nogui

    if [ "$TRAVIS" != "true" ]; then   # Requires matplotlib...
        pynml-channelanalysis NaConductance.channel.nml KConductance.channel.nml -html
    fi
fi

echo
echo "################################################"
echo "##   Test export to PovRay"

 pynml-povray NML2_SingleCompHHCell.nml


    
if [ "$TRAVIS" != "true" ]; then   # Requires pyelectro, not in .travis.yml yet...
echo
echo "################################################"
echo "##   Generate a frequency vs current plot"

    python3 generate_if_curve.py -nogui  


echo
echo "################################################"
echo "##   Generate a dt dependence plot"

    python3 dt_dependence.py -nogui  

fi 



# Only run these if NEURON is installed & -neuron flag is used
if [ "$run_neuron_examples" == true ]; then

    echo
    echo "################################################"
    echo "##   Try exporting morphologies to NeuroML from NEURON"

        # Export NeuroML v1 from NEURON example
        python3 export_neuroml1.py

        # Export NeuroML v2 from NEURON example
        python3 export_neuroml2.py


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
