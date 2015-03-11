from setuptools import setup

import pyneuroml
version = pyneuroml.__version__

setup(
    name='pyNeuroML',
    version=version,
    author='Padraig Gleeson',
    author_email='p.gleeson@gmail.com',
    packages = ['pyneuroml', 'pyneuroml.analysis', 'pyneuroml.lems', 'pyneuroml.neuron'],
    entry_points={
        'console_scripts': ['pynml                 = pyneuroml.pynml:main',
                            'pynml-channelanalysis = pyneuroml.analysis.NML2ChannelAnalysis:main']},
    package_data={
        'pyneuroml': [
            'lib/jNeuroML-0.7.1-jar-with-dependencies.jar',
            'analysis/LEMS_Test_TEMPLATE.xml',
            'lems/LEMS_TEMPLATE.xml',
            'neuron/mview_neuroml1.hoc',
            'neuron/mview_neuroml2.hoc']},
    url='https://github.com/pgleeson/pyNeuroML',
    license='LICENSE.lesser',
    description='Python utilities for NeuroML',
    long_description=open('README.md').read(),
    install_requires=[
        'argparse',
        'lxml',
        'pylems',
        'airspeed>=0.4.1',
        'libNeuroML>=0.2.5'],
    dependency_links=[
      'https://github.com/purcell/airspeed.git',
      'git+https://github.com/NeuralEnsemble/libNeuroML.git@development#egg=libNeuroML-0.2.5'
    ],
    classifiers = [
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: LGPL',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Topic :: Scientific/Engineering']
)
