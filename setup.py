from setuptools import setup

import pyneuroml
version = pyneuroml.__version__
jnml_version = pyneuroml.JNEUROML_VERSION

setup(
    name='pyNeuroML',
    version=version,
    author='Padraig Gleeson',
    author_email='p.gleeson@gmail.com',
    packages=['pyneuroml',
              'pyneuroml.analysis',
              'pyneuroml.lems',
              'pyneuroml.tune',
              'pyneuroml.neuron',
              'pyneuroml.povray',
              'pyneuroml.plot',
              'pyneuroml.swc',
              'pyneuroml.neuron.analysis'],
    entry_points={
        'console_scripts': [
            'pynml                 = pyneuroml.pynml:main',
            'pynml-channelanalysis = pyneuroml.analysis.NML2ChannelAnalysis:main',
            'pynml-modchananalysis = pyneuroml.neuron.analysis.HHanalyse:main',
            'pynml-povray          = pyneuroml.povray.NeuroML2ToPOVRay:main',
            'pynml-tune            = pyneuroml.tune.NeuroMLTuner:main',
            'pynml-summary         = pyneuroml.pynml:summary',
            'pynml-plotspikes      = pyneuroml.plot.PlotSpikes:main',
            'pynml-sonata          = neuromllite.SonataReader:main']},
    package_data={
        'pyneuroml': [
            'lib/jNeuroML-{}-jar-with-dependencies.jar'.format(
                jnml_version),
            'analysis/LEMS_Test_TEMPLATE.xml',
            'analysis/ChannelInfo_TEMPLATE.html',
            'analysis/ChannelInfo_TEMPLATE.md',
            'lems/LEMS_TEMPLATE.xml',
            'neuron/mview_neuroml1.hoc',
            'neuron/mview_neuroml2.hoc']},
    url='https://github.com/NeuroML/pyNeuroML',
    license='LICENSE.lesser',
    description='Python utilities for NeuroML',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    install_requires=[
        'argparse',
        'pylems>=0.5.0',
        'airspeed>=0.5.5',
        'libNeuroML>=0.2.52',
        'neuromllite>=0.2.2',
        'matplotlib',
        'graphviz'],
    dependency_links=[
        'git+https://github.com/NeuralEnsemble/libNeuroML.git@development#egg=libNeuroML',
        'git+https://github.com/NeuroML/NeuroMLlite.git#egg=neuromllite'
    ],
    classifiers=[
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Scientific/Engineering']
)
