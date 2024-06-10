pyNeuroML
=========

[![GitHub CI](https://github.com/NeuroML/pyNeuroML/actions/workflows/ci.yml/badge.svg)](https://github.com/NeuroML/pyNeuroML/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/pyNeuroML)](https://pypi.org/project/pyNeuroML/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyNeuroML)](https://pypi.org/project/pyNeuroML/)
[![GitHub](https://img.shields.io/github/license/NeuroML/pyNeuroML)](https://github.com/NeuroML/pyNeuroML/blob/master/LICENSE.lesser)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/NeuroML/pyNeuroML)](https://github.com/NeuroML/pyNeuroML/pulls)
[![GitHub issues](https://img.shields.io/github/issues/NeuroML/pyNeuroML)](https://github.com/NeuroML/pyNeuroML/issues)
[![Documentation Status](https://readthedocs.org/projects/pyneuroml/badge/?version=latest)](https://pyneuroml.readthedocs.io/en/latest/?badge=latest)
[![GitHub Org's stars](https://img.shields.io/github/stars/NeuroML?style=social)](https://github.com/NeuroML)
[![Twitter Follow](https://img.shields.io/twitter/follow/NeuroML?style=social)](https://twitter.com/NeuroML)
[![Gitter](https://badges.gitter.im/NeuroML/community.svg)](https://gitter.im/NeuroML/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-12-orange.svg?style=flat-square)](#contributors)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

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


A number of extra packages are also provided for convenience. You can install these to pull in other dependencies if required:


    pip install pyneuroml[neuron]       # for NEURON simulation backend
    pip install pyneuroml[brian]        # for Brian2 simulation backend
    pip install pyneuroml[netpyne]      # for NetPyNE simulation backend
    pip install pyneuroml[povray]       # for povray functions
    pip install pyneuroml[hdf5]         # for HDF5 support
    pip install pyneuroml[analysis]     # for analysis functions
    pip install pyneuroml[tune]         # for tuning/fitting functions
    pip install pyneuroml[vispy]        # for 3D interactive morphology plotting using vispy
    pip install pyneuroml[plotly]       # for interactive plotting with plotly
    pip install pyneuroml[nsg]          # pulls in pynsgr to use NSG
    pip install pyneuroml[combine]      # includes libsbml, libsedml
    pip install pyneuroml[tellurium]    # for Tellurium simulation backend
    pip install pyneuroml[all]          # installs all of the above
    pip install pyneuroml[dev]          # installs all of the above and other test related packages
    pip install pyneuroml[doc]          # for building documentation


Please see the `setup.cfg` file for more details.


### Fedora

The [NeuroFedora](https://neuro.fedoraproject.org) community initiative provides pyNeuroML for use on the [Fedora Linux Distribution](https://getfedora.org).
Fedora users can install pyNeuroML using the following commands:

    sudo dnf copr enable @neurofedora/neurofedora-extra
    sudo dnf install python3-pyneuroml

This will also pull in all the necessary dependencies (Java, lxml, graphviz).
Please see the [project documentation](https://docs.fedoraproject.org/en-US/neurofedora/copr/) for more information.

### Installation from the source

Clone the repository:

    git clone https://github.com/NeuroML/pyNeuroML.git
    cd pyNeuroML

It should be possible to install pyNeuroML using just:

    pip install .

To develop pyNeuroML, you can use the `dev` extra and the `development` branch:

    git clone https://github.com/NeuroML/pyNeuroML.git
    cd pyNeuroML
    git checkout development
    pip install .[dev]


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


## Contributors

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="http://www.opensourcebrain.org/"><img src="https://avatars.githubusercontent.com/u/1556687?v=4?s=100" width="100px;" alt="Padraig Gleeson"/><br /><sub><b>Padraig Gleeson</b></sub></a><br /><a href="https://github.com/NeuroML/pyNeuroML/issues?q=author%3Apgleeson" title="Bug reports">🐛</a> <a href="https://github.com/NeuroML/pyNeuroML/commits?author=pgleeson" title="Code">💻</a> <a href="#content-pgleeson" title="Content">🖋</a> <a href="#data-pgleeson" title="Data">🔣</a> <a href="https://github.com/NeuroML/pyNeuroML/commits?author=pgleeson" title="Documentation">📖</a> <a href="#design-pgleeson" title="Design">🎨</a> <a href="#eventOrganizing-pgleeson" title="Event Organizing">📋</a> <a href="#ideas-pgleeson" title="Ideas, Planning, & Feedback">🤔</a> <a href="#infra-pgleeson" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="#maintenance-pgleeson" title="Maintenance">🚧</a> <a href="#mentoring-pgleeson" title="Mentoring">🧑‍🏫</a> <a href="#platform-pgleeson" title="Packaging/porting to new platform">📦</a> <a href="#projectManagement-pgleeson" title="Project Management">📆</a> <a href="#question-pgleeson" title="Answering Questions">💬</a> <a href="#research-pgleeson" title="Research">🔬</a> <a href="https://github.com/NeuroML/pyNeuroML/pulls?q=is%3Apr+reviewed-by%3Apgleeson" title="Reviewed Pull Requests">👀</a> <a href="#tool-pgleeson" title="Tools">🔧</a> <a href="#tutorial-pgleeson" title="Tutorials">✅</a> <a href="#talk-pgleeson" title="Talks">📢</a> <a href="#userTesting-pgleeson" title="User Testing">📓</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://ankursinha.in/"><img src="https://avatars.githubusercontent.com/u/102575?v=4?s=100" width="100px;" alt="Ankur Sinha"/><br /><sub><b>Ankur Sinha</b></sub></a><br /><a href="https://github.com/NeuroML/pyNeuroML/issues?q=author%3Asanjayankur31" title="Bug reports">🐛</a> <a href="https://github.com/NeuroML/pyNeuroML/commits?author=sanjayankur31" title="Code">💻</a> <a href="#content-sanjayankur31" title="Content">🖋</a> <a href="#data-sanjayankur31" title="Data">🔣</a> <a href="https://github.com/NeuroML/pyNeuroML/commits?author=sanjayankur31" title="Documentation">📖</a> <a href="#design-sanjayankur31" title="Design">🎨</a> <a href="#eventOrganizing-sanjayankur31" title="Event Organizing">📋</a> <a href="#ideas-sanjayankur31" title="Ideas, Planning, & Feedback">🤔</a> <a href="#mentoring-sanjayankur31" title="Mentoring">🧑‍🏫</a> <a href="#platform-sanjayankur31" title="Packaging/porting to new platform">📦</a> <a href="#question-sanjayankur31" title="Answering Questions">💬</a> <a href="#research-sanjayankur31" title="Research">🔬</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/borismarin"><img src="https://avatars.githubusercontent.com/u/3452783?v=4?s=100" width="100px;" alt="Boris Marin"/><br /><sub><b>Boris Marin</b></sub></a><br /><a href="https://github.com/NeuroML/pyNeuroML/issues?q=author%3Aborismarin" title="Bug reports">🐛</a> <a href="https://github.com/NeuroML/pyNeuroML/commits?author=borismarin" title="Code">💻</a> <a href="#content-borismarin" title="Content">🖋</a> <a href="#data-borismarin" title="Data">🔣</a> <a href="https://github.com/NeuroML/pyNeuroML/commits?author=borismarin" title="Documentation">📖</a> <a href="#design-borismarin" title="Design">🎨</a> <a href="#eventOrganizing-borismarin" title="Event Organizing">📋</a> <a href="#ideas-borismarin" title="Ideas, Planning, & Feedback">🤔</a> <a href="#infra-borismarin" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="#maintenance-borismarin" title="Maintenance">🚧</a> <a href="#platform-borismarin" title="Packaging/porting to new platform">📦</a> <a href="#question-borismarin" title="Answering Questions">💬</a> <a href="#research-borismarin" title="Research">🔬</a> <a href="https://github.com/NeuroML/pyNeuroML/pulls?q=is%3Apr+reviewed-by%3Aborismarin" title="Reviewed Pull Requests">👀</a> <a href="#tool-borismarin" title="Tools">🔧</a> <a href="#userTesting-borismarin" title="User Testing">📓</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://rick.gerk.in/"><img src="https://avatars.githubusercontent.com/u/549787?v=4?s=100" width="100px;" alt="Richard C Gerkin"/><br /><sub><b>Richard C Gerkin</b></sub></a><br /><a href="https://github.com/NeuroML/pyNeuroML/issues?q=author%3Argerkin" title="Bug reports">🐛</a> <a href="https://github.com/NeuroML/pyNeuroML/commits?author=rgerkin" title="Code">💻</a> <a href="#ideas-rgerkin" title="Ideas, Planning, & Feedback">🤔</a> <a href="#maintenance-rgerkin" title="Maintenance">🚧</a> <a href="#platform-rgerkin" title="Packaging/porting to new platform">📦</a> <a href="#research-rgerkin" title="Research">🔬</a> <a href="https://github.com/NeuroML/pyNeuroML/pulls?q=is%3Apr+reviewed-by%3Argerkin" title="Reviewed Pull Requests">👀</a> <a href="#tool-rgerkin" title="Tools">🔧</a> <a href="#userTesting-rgerkin" title="User Testing">📓</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/lungd"><img src="https://avatars.githubusercontent.com/u/5890526?v=4?s=100" width="100px;" alt="David Lung"/><br /><sub><b>David Lung</b></sub></a><br /><a href="https://github.com/NeuroML/pyNeuroML/issues?q=author%3Alungd" title="Bug reports">🐛</a> <a href="https://github.com/NeuroML/pyNeuroML/commits?author=lungd" title="Code">💻</a> <a href="#maintenance-lungd" title="Maintenance">🚧</a> <a href="#tool-lungd" title="Tools">🔧</a> <a href="#userTesting-lungd" title="User Testing">📓</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://www.thispersondoesnotexist.com/"><img src="https://avatars.githubusercontent.com/u/1487560?v=4?s=100" width="100px;" alt="Mark Watts"/><br /><sub><b>Mark Watts</b></sub></a><br /><a href="https://github.com/NeuroML/pyNeuroML/issues?q=author%3Amwatts15" title="Bug reports">🐛</a> <a href="https://github.com/NeuroML/pyNeuroML/commits?author=mwatts15" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://chchaitanya.wordpress.com/"><img src="https://avatars.githubusercontent.com/u/546703?v=4?s=100" width="100px;" alt="Chaitanya Chintaluri "/><br /><sub><b>Chaitanya Chintaluri </b></sub></a><br /><a href="https://github.com/NeuroML/pyNeuroML/issues?q=author%3Accluri" title="Bug reports">🐛</a> <a href="https://github.com/NeuroML/pyNeuroML/commits?author=ccluri" title="Code">💻</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/34383c"><img src="https://avatars.githubusercontent.com/u/17238193?v=4?s=100" width="100px;" alt="34383c"/><br /><sub><b>34383c</b></sub></a><br /><a href="https://github.com/NeuroML/pyNeuroML/issues?q=author%3A34383c" title="Bug reports">🐛</a> <a href="https://github.com/NeuroML/pyNeuroML/commits?author=34383c" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/jrieke"><img src="https://avatars.githubusercontent.com/u/5103165?v=4?s=100" width="100px;" alt="Johannes Rieke"/><br /><sub><b>Johannes Rieke</b></sub></a><br /><a href="https://github.com/NeuroML/pyNeuroML/issues?q=author%3Ajrieke" title="Bug reports">🐛</a> <a href="https://github.com/NeuroML/pyNeuroML/commits?author=jrieke" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/andrisecker"><img src="https://avatars.githubusercontent.com/u/13274870?v=4?s=100" width="100px;" alt="András Ecker"/><br /><sub><b>András Ecker</b></sub></a><br /><a href="https://github.com/NeuroML/pyNeuroML/issues?q=author%3Aandrisecker" title="Bug reports">🐛</a> <a href="https://github.com/NeuroML/pyNeuroML/commits?author=andrisecker" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/RokasSt"><img src="https://avatars.githubusercontent.com/u/12904422?v=4?s=100" width="100px;" alt="Rokas Stanislovas"/><br /><sub><b>Rokas Stanislovas</b></sub></a><br /><a href="https://github.com/NeuroML/pyNeuroML/issues?q=author%3ARokasSt" title="Bug reports">🐛</a> <a href="https://github.com/NeuroML/pyNeuroML/commits?author=RokasSt" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/robertvi"><img src="https://avatars.githubusercontent.com/u/456100?v=4?s=100" width="100px;" alt="Robert Vickerstaff"/><br /><sub><b>Robert Vickerstaff</b></sub></a><br /><a href="https://github.com/NeuroML/pyNeuroML/commits?author=robertvi" title="Code">💻</a> <a href="https://github.com/NeuroML/pyNeuroML/commits?author=robertvi" title="Tests">⚠️</a></td>
    </tr>
  </tbody>
  <tfoot>
    <tr>
      <td align="center" size="13px" colspan="7">
        <img src="https://raw.githubusercontent.com/all-contributors/all-contributors-cli/1b8533af435da9854653492b1327a23a4dbd0a10/assets/logo-small.svg">
          <a href="https://all-contributors.js.org/docs/en/bot/usage">Add your contributions</a>
        </img>
      </td>
    </tr>
  </tfoot>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->
