#!/usr/bin/env python
"""
Python wrapper around jnml command

Thanks to Werner van Geit for initiating this
"""

import os
import subprocess

verbose = False

def parse_arguments():
    """Parse command line arguments"""
    import argparse

    parser = argparse.ArgumentParser(description='Python utilities for NeuroML2')

    parser.add_argument('neuroml2_file', metavar='neuroml2_file', type=str,
                        help='The NeuroML2 file to process')

    parser.add_argument('-sim', choices=('pylems', 'jlems'),
                        help='Simulator to use')

    parser.add_argument('-validate', action='store_true',
                        help='Only validate')
                        
    parser.add_argument('-verbose', action='store_true',
                        help='Verbose output')

    parser.add_argument('-outputdir', nargs=1,
                        help='Directory to write output scripts to')

    return parser.parse_args()


def run_jnml(args):
    """Run the jnml command"""
    
    global verbose 
    verbose = args.verbose

    if args.outputdir:
        initialize_outputdir(args.outputdir[0], args.xml_filename)
        exec_dir = args.outputdir[0]
    else:
        exec_dir = "."

    if not args.sim:
        simulator_option = ''
    elif args.sim == 'jlems':
        simulator_option = ''
    else:
        simulator_option = '-%s' % args.sim

    script_dir = os.path.dirname(os.path.realpath(__file__))

    jar = os.path.join(script_dir, "lib/jNeuroML-0.7.0-jar-with-dependencies.jar")
    
    print_comment(script_dir)

    output = execute_command_in_dir("java -jar %s %s %s" %
                                        (jar, args.neuroml2_file,
                                            simulator_option), exec_dir)
                                            
    print_comment(output)
                              

def main():
    """Main"""

    args = parse_arguments()

    run_jnml(args)
    
def print_comment(text):
    
    if verbose:
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
