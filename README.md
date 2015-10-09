pyNeuroML
=========

A single package in Python unifying scripts and modules for reading, writing, simulating and analysing NeuroML2/LEMS models.

Builds on: [libNeuroML](https://github.com/NeuralEnsemble/libNeuroML) & [PyLEMS](https://github.com/LEMS/pylems) and wraps functionality from [jNeuroML](https://github.com/NeuroML/jNeuroML).

Installation
------------

Clone the repository:

    git clone https://github.com/NeuroML/pyNeuroML.git
    cd pyNeuroML
    
It should be possible to install pyNeuroML using just:

    sudo python setup.py install
    
You **may** have to install the development version of [libNeuroML](https://github.com/NeuralEnsemble/libNeuroML) manually:

    cd ..
    git clone https://github.com/NeuralEnsemble/libNeuroML.git
    cd libNeuroML
    git checkout development
    sudo python setup.py install
    

Some current/planned features
-----------------------------

**1) Single Python package for NeuroML2/LEMS**

One Python package which can be installed using pip & a user has everything they need to work with NeuroML2/LEMS files:

- libNeuroML
- PyLEMS
- A bundled version of jNeuroML which can be used to run simulations

**2) Run models using jNeuroML or PyLEMS**

Ability to run NeuroML2/LEMS models using jLEMS/jNeuroML (with [bundled jar](https://github.com/NeuroML/pyNeuroML/tree/master/pyneuroml/lib)) or PyLEMS (coming soon...)

Uses similar command line interface to jNeuroML, i.e. based on jnml

Try:

    pynml -h

**Access to export & import options of jNeuroML**

All export & import options of jNeuroML available through easy command line interface (coming soon...) & through Python methods.

Example of export of NeuroML2/LEMS to NEURON and execution of generated code using single method is [here](https://github.com/NeuroML/pyNeuroML/blob/master/examples/run_jneuroml_plot_matplotlib.py#L21).

**3) Helper Python scripts**

Lots of helper scripts for commonly used NeuroML2 functions, e.g.

**4) Analysis of ion channels**

Generation of plots of activation rates for ion channels from NeuroML2 channel file ([example](https://github.com/NeuroML/pyNeuroML/blob/master/examples/analyseNaNml2.sh)):

    pynml-channelanalysis NaConductance.channel.nml
    
Generation of plots of activation rates for ion channels from NEURON mod file ([example](https://github.com/NeuroML/pyNeuroML/blob/master/examples/analyseNaMod.sh)):

    pynml-modchananalysis NaConductance -modFile NaConductance.mod

**5) Home for existing functionality distributed in various places**

Incorporate ChannelML2NeuroML2beta.xsl for updating ChannelML (coming soon...)

**6) NEURON to NeuroML2**

Scripts for converting NEURON to NeuroML2
	
- Export morphologies (plus channels, soon). See [here](https://github.com/NeuroML/pyNeuroML/blob/master/examples/export_neuroml2.py).

- mod files - make best guess at initial NeuroML2 form
	
**7) Planned functionality**

Built in viewer of cells in 3D? Mayavi?
More closely tied to PyNN?


[![Build Status](https://travis-ci.org/NeuroML/pyNeuroML.svg?branch=master)](https://travis-ci.org/NeuroML/pyNeuroML)
