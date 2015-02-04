#!/usr/bin/env python
"""
Python wrapper around jnml command

Thanks to Werner van Geit for initiating this
"""

import os
import subprocess

from . import __version__

verbose = False

def parse_arguments():
    """Parse command line arguments"""
    import argparse

    parser = argparse.ArgumentParser(description='pyNeuroML v%s: Python utilities for NeuroML2'%__version__)

    parser.add_argument('target_file', metavar='target_file', type=str,
                        help='The LEMS/NeuroML2 file to process')

    ##parser.add_argument('-sim', choices=('pylems', 'jlems'),
    ##                     help='Simulator to use')

    parser.add_argument('-validate', action='store_true',
                        help='Validate NeuroML2 file against the latest Schema')
                        
    parser.add_argument('-nogui', action='store_true',
                        help='Supress GUI, i.e. show no plots, just save results', default="False")
                        
    parser.add_argument('-verbose', action='store_true',
                        help='Verbose output')

    ##parser.add_argument('-outputdir', nargs=1,
    ##                    help='Directory to write output scripts to')

    return parser.parse_args()


def run_lems_with_jneuroml(lems_file_name, nogui=False, load_saved_data=False):           
    print_comment("Loading LEMS file: %s and running with jNeuroML"%lems_file_name, True)
    
    post_args = ""
    gui = " -nogui" if nogui else ""
    post_args += gui
    
    run_jneuroml("", lems_file_name, post_args)
    
    if load_saved_data:
        
        # Could use pylems to parse this...
        
        results = {}
        
        import xml.etree.ElementTree as ET
        tree = ET.parse(lems_file_name)
        sim = tree.getroot().find('Simulation')
        for of in sim.findall('OutputFile'):
            results[of.attrib['id']] = {}
            results[of.attrib['id']]['t'] = []
            file_name = of.attrib['fileName']
            print_comment("Loading saved data from %s"%file_name, True)
        
            for col in of.findall('OutputColumn'):
                results[of.attrib['id']][col.attrib['id']] = []
            for line in open(file_name):
                values = line.split()
                for vi in range(len(values)):
                   results[of.attrib['id']].values()[vi].append(values[vi])
            
        return results
                
            


def evaluate_arguments(args):
    
    global verbose 
    verbose = args.verbose

    ##if args.outputdir:
    ##    initialize_outputdir(args.outputdir[0], args.xml_filename)
    ##    exec_dir = args.outputdir[0]
    ##else:
        
    pre_args = ""
    post_args = ""

    '''
    if not args.sim:
        simulator_option = ''
    elif args.sim == 'jlems':
        simulator_option = ''
    else:
        simulator_option = '-%s' % args.sim
    '''
        
    gui = " -nogui" if args.nogui==True else ""
    post_args += gui
    
    if args.validate:
        pre_args += " -validate"
        
    run_jneuroml(pre_args, args.target_file, post_args)
    
        
def run_jneuroml(pre_args, target_file, post_args):    
       
    exec_dir = "." 
    
    script_dir = os.path.dirname(os.path.realpath(__file__))

    jar = os.path.join(script_dir, "lib/jNeuroML-0.7.0-jar-with-dependencies.jar")
    

    output = execute_command_in_dir("java -jar %s %s %s %s" %
                                        (jar, pre_args, target_file, post_args), exec_dir)
                                            
    print_comment(output, True)
                              

def main():
    """Main"""

    args = parse_arguments()

    evaluate_arguments(args)
    
def print_comment(text, print_it=verbose):
    
    if print_it:
        print("pyNeuroML >>> %s"%(text))


def execute_command_in_dir(command, directory):
    
    """Execute a command in specific working directory"""
    
    if os.name == 'nt':
        directory = os.path.normpath(directory)
        
    print_comment("Executing: (%s) in dir: %s" % (command, directory))
    
    return_string = subprocess.Popen(command, cwd=directory, shell=True,
                                     stdout=subprocess.PIPE).communicate()[0]
                                     
    return return_string


if __name__ == "__main__":
    main()
