#!/usr/bin/env python
"""

Python wrapper around jnml command. Also a number of helper functions for handling/generating/running LEMS/NeuroML2 files

Thanks to Werner van Geit for an initial version of a python wrapper for jnml.

"""

from __future__ import absolute_import
import os
import subprocess

from . import __version__

import neuroml.loaders as loaders
import neuroml.writers as writers

import lems.model.model as lems_model

import random

verbose = False

default_java_max_memory = "400M"

def parse_arguments():
    """Parse command line arguments"""
    import argparse

    parser = argparse.ArgumentParser(description='pyNeuroML v%s: Python utilities for NeuroML2'%__version__)

    parser.add_argument('target_file', metavar='target_file', type=str,
                        help='The LEMS/NeuroML2 file to process; without other options simulates a LEMS file (containing a <Simulation element>) natively using jNeuroML')

    ##parser.add_argument('-sim', choices=('pylems', 'jlems'),
    ##                     help='Simulator to use')

    parser.add_argument('-nogui', action='store_true',
                        help='Simulate LEMS file with jNeuroML, but supress GUI, i.e. show no plots, just save results', default="False")
                        
    parser.add_argument('-validate', action='store_true',
                        help='(Via jNeuroML) Validate NeuroML2 file against the latest Schema')
                        
    parser.add_argument('-svg', action='store_true',
                        help='(Via jNeuroML) Convert NeuroML2 file (network & cells) to SVG format view of 3D structure')
                        
    parser.add_argument('-sedml', action='store_true',
                        help='(Via jNeuroML) Load a LEMS file, and convert simulation settings (duration, dt, what to save) to SED-ML format')
                        
    parser.add_argument('-java_max_memory', metavar='MAX', type=str,
                        help='Java memory for jNeuroML, e.g. 400M, 2G (used in -Xmx argument to java)', default=default_java_max_memory)
                        
    parser.add_argument('-verbose', action='store_true',
                        help='Verbose output')

    ##parser.add_argument('-outputdir', nargs=1,
    ##                    help='Directory to write output scripts to')

    return parser.parse_args()


def validate_neuroml1(nml1_file_name):
    
    pre_args = "-validatev1"
    post_args = ""
        
    run_jneuroml(pre_args, nml1_file_name, post_args)


def validate_neuroml2(nml2_file_name):
    
    pre_args = "-validate"
    post_args = ""
        
    run_jneuroml(pre_args, nml2_file_name, post_args)
    


def read_neuroml2_file(nml2_file_name):
    
    return loaders.NeuroMLLoader.load(nml2_file_name)



def write_neuroml2_file(nml2_doc, nml2_file_name, validate=True):
    
    writers.NeuroMLWriter.write(nml2_doc,nml2_file_name)
    
    if validate:
        validate_neuroml2(nml2_file_name)
        
        
        
def read_lems_file(lems_file_name):
    
    model = lems_model.Model(include_includes=False)

    model.import_from_file(lems_file_name)
    
    return model


def write_lems_file(lems_model, lems_file_name, validate=False):
    
    lems_model.export_to_file(lems_file_name)
    
    if validate:
        from lems.base.util import validate_lems
        validate_lems(lems_file_name)


def run_lems_with_jneuroml(lems_file_name, max_memory=default_java_max_memory, 
                           nogui=False, load_saved_data=False, plot=False, 
                           verbose=True):           
    print_comment("Loading LEMS file: %s and running with jNeuroML"%lems_file_name, verbose)
    
    post_args = ""
    gui = " -nogui" if nogui else ""
    post_args += gui
    
    run_jneuroml("", lems_file_name, post_args, max_memory, verbose)
    
    if load_saved_data:
        return reload_saved_data(lems_file_name, plot, 'jNeuroML')
    
    

def nml2_to_svg(nml2_file_name, max_memory=default_java_max_memory, verbose=True):           
    print_comment("Converting NeuroML2 file: %s to SVG"%nml2_file_name, verbose)
    
    post_args = "-svg"
    
    run_jneuroml("", nml2_file_name, post_args, max_memory, verbose)


def run_lems_with_jneuroml_neuron(
    lems_file_name, max_memory=default_java_max_memory, nogui=False, 
    load_saved_data=False, plot=False, verbose=True):           
    print_comment("Loading LEMS file: %s and running with jNeuroML_NEURON"%lems_file_name, verbose)
    
    post_args = " -neuron -run"
    gui = " -nogui" if nogui else ""
    post_args += gui
    
    run_jneuroml("", lems_file_name, post_args, max_memory)
    
    if load_saved_data:
        return reload_saved_data(lems_file_name, plot, 'jNeuroML_NEURON')
    
    
def reload_saved_data(lems_file_name, plot=False, 
                      simulator=None, verbose=verbose): 
    
    # Could use pylems to parse this...

    results = {}
    
    if plot:
        import matplotlib.pyplot as pylab

    from lxml import etree
    tree = etree.parse(lems_file_name)
    sim = tree.getroot().find('Simulation')
    ns_prefix = ''
    
    possible_prefixes = ['{http://www.neuroml.org/lems/0.7.2}']
    if sim is None:
        #print tree.getroot().nsmap
        #print tree.getroot().getchildren()
        for pre in possible_prefixes:
            for comp in tree.getroot().findall(pre+'Component'):
                if comp.attrib['type'] == 'Simulation':
                    ns_prefix = pre
                    sim = comp
    
    for of in sim.findall(ns_prefix+'OutputFile'):
        results['t'] = []
        file_name = of.attrib['fileName']
        print_comment("Loading saved data from %s%s"%(file_name, ' (%s)'%simulator if simulator else ''), verbose)

        cols = []
        cols.append('t')
        for col in of.findall(ns_prefix+'OutputColumn'):
            quantity = col.attrib['quantity']
            results[quantity] = []
            cols.append(quantity)
            
        for line in open(file_name):
            values = line.split()
            
            for vi in range(len(values)):
               results[cols[vi]].append(float(values[vi]))
               

        if plot:
            fig = pylab.figure()
            fig.canvas.set_window_title("Data loaded from %s%s"%(file_name, ' (%s)'%simulator if simulator else ''))
            
            for key in cols:

                pylab.xlabel('Time (ms)')
                pylab.ylabel('(SI units...)')
                pylab.grid('on')

                curr_plot = pylab.subplot(111)
                
                if key != 't':
                    curr_plot.plot(results['t'], results[key], label=key)
                    print_comment("Adding trace for: %s, from: %s"%(key,file_name), True)
                    
                pylab.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=4) 
                   
    #print(results.keys())
        
    if plot:
        pylab.show()

    return results
                
            
def get_next_hex_color():
    
    return "#%06x" % random.randint(0,0xFFFFFF)

def evaluate_arguments(args):
    
    global verbose 
    verbose = args.verbose

    pre_args = ""
    post_args = ""
        
    gui = " -nogui" if args.nogui==True else ""
    post_args += gui
    
    if args.validate:
        pre_args += " -validate"
        
    elif args.svg:
        post_args += " -svg"
        
    elif args.sedml:
        post_args += " -sedml"
        
    run_jneuroml(pre_args, args.target_file, post_args, args.java_max_memory)
    
        
def run_jneuroml(pre_args, target_file, post_args, max_memory=default_java_max_memory, verbose=True):    
       
    exec_dir = "." 
    
    script_dir = os.path.dirname(os.path.realpath(__file__))

    jar = os.path.join(script_dir, "lib/jNeuroML-0.7.1-jar-with-dependencies.jar")
    

    output = execute_command_in_dir("java -Xmx%s -jar  %s %s %s %s" %
                                        (max_memory, jar, pre_args, target_file, 
                                         post_args), exec_dir, verbose=verbose)
                                            
    print_comment(output, verbose)

    
    
def print_comment(text, print_it=verbose):
    
    prefix = "pyNeuroML >>> "
    if not isinstance(text, str): text = text.decode('ascii')
    if print_it:
        
        print("%s%s"%(prefix, text.replace("\n", "\n"+prefix)))



def execute_command_in_dir(command, directory, verbose=True):
    
    """Execute a command in specific working directory"""
    
    if os.name == 'nt':
        directory = os.path.normpath(directory)
        
    print_comment("Executing: (%s) in dir: %s" % (command, directory), verbose)
    
    try:
        return_string = subprocess.check_output(command, cwd=directory, shell=True)

        return return_string
    
    except AttributeError:
        # For python 2.6...
        return_string = subprocess.Popen(command, cwd=directory, shell=True,
                                     stdout=subprocess.PIPE).communicate()[0]
        return return_string
                              

def main(args=None):
    """Main"""

    if args is None:
        args = parse_arguments()

    evaluate_arguments(args)
    
    
if __name__ == "__main__":
    main()
