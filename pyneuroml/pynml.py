#!/usr/bin/env python
"""
Python wrapper around jnml command

Thanks to Werner van Geit for initiating this
"""

import os
import subprocess
import shutil
from xml.dom import minidom


def parse_arguments():
    """Parse command line arguments"""
    import argparse

    parser = argparse.ArgumentParser(description='Python utility for NeuroML2')

    parser.add_argument('xml_filename', metavar='xmlfile', type=str,
                        help='The xml file to process')

    parser.add_argument('--sim', choices=('neuron', 'jlems'),
                        help='Simulator to use')

    parser.add_argument('--validate', action='store_true',
                        help='Only validate')

    parser.add_argument('--outputdir', nargs=1,
                        help='Directory to write output scripts to')

    return parser.parse_args()


def run_jnml(args):
    """Run the jnml command"""

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

    jar = os.path.join(script_dir, "../lib/jNeuroML-0.7.0-jar-with-dependencies.jar")
    
    print(script_dir)

    execute_command_in_dir("java -jar %s %s %s" %
                          (jar, args.xml_filename,
                              simulator_option), exec_dir)



def main():
    """Main"""

    args = parse_arguments()

    run_jnml(args)


def execute_command_in_dir(command, directory):
    """Execute a command in specific working directory"""
    if os.name == 'nt':
        directory = os.path.normpath(directory)
    print ">>>  Executing: (%s) in dir: %s" % (command, directory)
    
    return_string = subprocess.Popen(command, cwd=directory, shell=True,
                                     stdout=subprocess.PIPE).communicate()[0]
    return return_string


if __name__ == "__main__":
    main()
