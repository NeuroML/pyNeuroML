pyNeuroML
=========

[![GitHub CI](https://github.com/NeuroML/pyNeuroML/actions/workflows/ci.yml/badge.svg)](https://github.com/NeuroML/pyNeuroML/actions/workflows/ci.yml)
[![Travis CI](https://travis-ci.com/NeuroML/pyNeuroML.svg?branch=master)](https://travis-ci.com/NeuroML/pyNeuroML)
[![PyPI](https://img.shields.io/pypi/v/pyNeuroML)](https://pypi.org/project/pyNeuroML/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyNeuroML)](https://pypi.org/project/pyNeuroML/)
[![GitHub](https://img.shields.io/github/license/NeuroML/pyNeuroML)](https://github.com/NeuroML/pyNeuroML/blob/master/LICENSE.lesser)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/NeuroML/pyNeuroML)](https://github.com/NeuroML/pyNeuroML/pulls)
[![GitHub issues](https://img.shields.io/github/issues/NeuroML/pyNeuroML)](https://github.com/NeuroML/pyNeuroML/issues)
[![GitHub Org's stars](https://img.shields.io/github/stars/NeuroML?style=social)](https://github.com/NeuroML)
[![Twitter Follow](https://img.shields.io/twitter/follow/NeuroML?style=social)](https://twitter.com/NeuroML)

A single package in Python unifying scripts and modules for reading, writing, simulating and analysing NeuroML2/LEMS models.

Builds on: [libNeuroML](https://github.com/NeuralEnsemble/libNeuroML) & [PyLEMS](https://github.com/LEMS/pylems) and wraps functionality from [jNeuroML](https://github.com/NeuroML/jNeuroML).

Installation
------------

### Dependencies

pyNeuroML relies on additional software to carry out its functions:

- Java Runtime environment (JRE)
- dot (from [Graphviz](http://graphviz.org/))
- lxml

On most Linux systems, these can be installed using the default package manager.
On Ubuntu based distributions:

    sudo apt-get install python-lxml graphviz openjdk-11-jdk


### Pip

pyNeuroML can be installed with pip (preferably in a [virtual environment](https://docs.python.org/3/tutorial/venv.html)):

    pip install pyneuroml

### Fedora

The [NeuroFedora](https://neuro.fedoraproject.org) community initiative provides pyNeuroML for use on the [Fedora Linux Distribution](https://getfedora.org).
Fedora users can install pyNeuroML using the following commands:

    sudo dnf copr enable @neurofedora/neurofedora-extra
    sudo dnf install python3-pyneuroml

This will also pull in all the necessary dependencies (Java, lxml, graphviz).
Please see the [project documentation](https://docs.fedoraproject.org/en-US/neurofedora/copr/) for more information.

### Installation from source

Clone the repository:

    git clone https://github.com/NeuroML/pyNeuroML.git
    cd pyNeuroML

It should be possible to install pyNeuroML using just:

    sudo pip install .

You **may** have to install lxml and the development version of [libNeuroML](https://github.com/NeuralEnsemble/libNeuroML) manually:

    apt-get install python-lxml
    cd ..
    git clone https://github.com/NeuralEnsemble/libNeuroML.git
    cd libNeuroML
    git checkout development
    sudo python setup.py install


Current/planned features
------------------------

**1) Single Python package for NeuroML2/LEMS**

One Python package which can be installed using pip & a user has everything they need to work with NeuroML2/LEMS files:

- libNeuroML
- PyLEMS
- A bundled version of jNeuroML which can be used to run simulations

**2) Run models using jNeuroML or PyLEMS**

Ability to run NeuroML2/LEMS models using jLEMS/jNeuroML (with [bundled jar](https://github.com/NeuroML/pyNeuroML/tree/master/pyneuroml/lib)) or PyLEMS (todo...)

Uses similar command line interface to jNeuroML, i.e. based on jnml

Try:

    pynml -h

to list current options.


**3) Access to export & import options of jNeuroML**

All export & import options of jNeuroML available through easy command line interface (see [here](https://github.com/NeuroML/pyNeuroML/issues/21) for progress) & through Python methods.

Example of export of NeuroML2/LEMS to NEURON and execution of generated code using single method is [here](https://github.com/NeuroML/pyNeuroML/blob/master/examples/run_jneuroml_plot_matplotlib.py#L21).

**4) Helper Python scripts**

Lots of helper scripts for commonly used functions, e.g. [generating a firing frequency vs injected current plot](https://github.com/NeuroML/pyNeuroML/blob/master/pyneuroml/analysis/__init__.py#L8), [generating a LEMS file for use with a NeuroML2 file](https://github.com/NeuroML/pyNeuroML/blob/master/pyneuroml/lems/__init__.py),

**5) Analysis of ion channels**

Generation of plots of activation rates for ion channels from NeuroML2 channel file ([example](https://github.com/NeuroML/pyNeuroML/blob/master/examples/analyseNaNml2.sh)):

    pynml-channelanalysis NaConductance.channel.nml

Generation of plots of activation rates for ion channels from NEURON mod file ([example](https://github.com/NeuroML/pyNeuroML/blob/master/examples/analyseNaMod.sh)):

    pynml-modchananalysis NaConductance -modFile NaConductance.mod

See [here](http://www.opensourcebrain.org/docs#Converting_To_NeuroML2) for more.

**6) Home for existing functionality distributed in various places**

Incorporate ChannelML2NeuroML2beta.xsl for updating ChannelML (coming soon...)

**7) NEURON to NeuroML2**

Scripts for converting NEURON to NeuroML2

- Export morphologies (plus channels, soon). See [here](https://github.com/NeuroML/pyNeuroML/blob/master/examples/export_neuroml2.py).

- mod files - make best guess at initial NeuroML2 form (todo)

**8) Export of images/movies from cell/networks**

Files can be generated for [POV-Ray](http://www.povray.org/) which can be used to generate high resolution images and even sequences of images for creating movies. try:

    pynml-povray -h

**9) Tuning cell models in NeuroML 2**

Builds on [Neurotune](https://github.com/NeuralEnsemble/neurotune) and [pyelectro](https://github.com/NeuralEnsemble/pyelectro). See [here](https://github.com/NeuroML/pyNeuroML/blob/master/examples/tuneHHCell.py) for example.

**9) Planned functionality**

Built in viewer of cells in 3D? Mayavi?
More closely tied to PyNN?


[![Build Status](https://travis-ci.com/NeuroML/pyNeuroML.svg?branch=master)](https://travis-ci.com/NeuroML/pyNeuroML)
