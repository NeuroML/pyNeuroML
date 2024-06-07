set -e

# CI already installs package and all optional dependencies, so this is redundant.
# But we keep it to allow easy local testing.
pip install .[dev]

echo
echo "################################################"
echo "##   Testing all CLI tools"

full_path=$(command -v pynml)
bin_location=$(dirname $full_path)

for f in ${bin_location}/pynml*
do
    current_exec=$(basename $f)
    echo "-> Testing $current_exec runs"
    echo
    command $current_exec -h
    echo
    echo
done

echo
echo "################################################"
echo "##   Running unit tests"


# skip a few tests that segfault etc. on GH
# see configuration in pyproject.toml
pytest -m "not localonly"


run_neuron_examples=false

if [[ ($# -eq 1) && ($1 == '-neuron') ]]; then
    run_neuron_examples=true
fi

# export NEURON_HOME
if command -v nrniv
then
    # double dirname because we also do not want the final `bin`
    NEURON_HOME=$(dirname $(dirname $(command -v nrniv)))
    export NEURON_HOME
fi

### Test script for pyNeuroML

pushd examples


echo
echo "################################################"
echo "##   Executing examples with jNeuroML"

pynml LEMS_NML2_Ex5_DetCell.xml -nogui



echo
echo "################################################"
echo "##   Validate with jNeuroML"

pynml -validate NML2_SingleCompHHCell.nml


echo "##   Multi-validate with jNeuroML"
pynml -validate *.channel.nml


echo
echo "################################################"
echo "##   Test XPP"

pynml-xpp test_data/xppaut/fhn.ode
pynml-xpp test_data/xppaut/fhn.ode -xpp
pynml-xpp test_data/xppaut/fhn.ode -lems -run
pynml-xpp test_data/xppaut/wc.ode -lems -run
pynml-xpp test_data/xppaut/nca.ode -lems -run

echo
echo "################################################"
echo "##   Test some conversions"

pynml NML2_SingleCompHHCell.nml -svg
pynml NML2_SingleCompHHCell.nml -png
pynml NML2_SingleCompHHCell.nml -swc
pynml LEMS_NML2_Ex5_DetCell.xml -sedml
pynml LEMS_NML2_Ex9_FN.xml -dlems
pynml LEMS_NML2_Ex9_FN.xml -brian
pynml LEMS_NML2_Ex5_DetCell.xml -neuron
pynml LEMS_NML2_Ex5_DetCell.xml -moose
pynml LEMS_NML2_Ex9_FN.xml -vertex
pynml LEMS_NML2_Ex9_FN.xml -xpp
pynml LEMS_NML2_Ex9_FN.xml -dnsim
pynml LEMS_NML2_Ex9_FN.xml -cvode
pynml LEMS_NML2_Ex9_FN.xml -matlab
pynml LEMS_NML2_Ex9_FN.xml -nineml
pynml LEMS_NML2_Ex9_FN.xml -spineml
pynml LEMS_NML2_Ex9_FN.xml -sbml


echo
echo "################################################"
echo "##   Simple SBML validation example"

pynml test_data/valid_doc.sbml -validate-sbml
pynml test_data/valid_doc.sbml -validate-sbml-units

echo
echo "################################################"
echo "##   Simple SEDML validation example"

pynml  test_data/valid_doc_sedml.sedml -validate-sedml

echo
echo "################################################"
echo "##   Tellurium validation example"

pynml test_data/valid_doc_sedml.sedml -run-tellurium -outputdir none

echo
echo "################################################"
echo "##   Running some of the examples"

#  Run an example with jNeuroML
python run_jneuroml_plot_matplotlib.py -nogui -noneuron


#  Run tests on units
python units.py

#  Run test for generating LEMS file
python create_new_lems_file.py -test

#  Run test for generating LEMS file
python Vm_plot.py -nogui



echo
echo "################################################"
echo "##   Test analysis of NeuroML2 channel"

pynml-channelanalysis NaConductance.channel.nml -nogui
pynml-channelanalysis NaConductance.channel.nml -ivCurve -erev 55 -nogui

# Not on GitHub Actions:
# https://docs.github.com/en/actions/reference/environment-variables#default-environment-variables
# Requires matplotlib + display
if [[ "$CI" != "true" ]]; then
    pynml-channelanalysis NaConductance.channel.nml KConductance.channel.nml -html
fi

echo
echo "################################################"
echo "##   Test export to PovRay"

pynml-povray NML2_SingleCompHHCell.nml


# Requires pyelectro, not in .travis.yml yet...
if [[ "$CI" != "true" ]]; then
echo
echo "################################################"
echo "##   Generate a frequency vs current plot"

    python generate_if_curve.py -nogui


echo
echo "################################################"
echo "##   Generate a dt dependence plot"

    python dt_dependence.py -nogui

fi



# Only run these if NEURON is installed & -neuron flag is used
if [ "$run_neuron_examples" == true ]; then

    echo
    echo "################################################"
    echo "##   Try exporting morphologies to NeuroML from NEURON"

        nrnivmodl
        # Export NeuroML v1 from NEURON example
        python export_neuroml1.py

        # Export NeuroML v2 from NEURON example
        python export_neuroml2.py


    echo
    echo "################################################"
    echo "##   Test analysis of channel in mod file"

        # do not run nrnivmodl, modchananalysis should run it if required
        pynml-modchananalysis -stepV 20  NaConductance  -dt 0.01 -nogui


    # Requires NEURON
    echo
    echo "################################################"
    echo "##   Test some tuning examples"

        pushd tune
            python tunePyr.py -tune -nogui
        popd

fi

popd

echo
echo "################################################"
echo "##   Finished all tests! "
echo "################################################"
