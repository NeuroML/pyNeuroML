#!/usr/bin/env python
"""

Python wrapper around jnml command. 
Also a number of helper functions for 
handling/generating/running LEMS/NeuroML2 files

Thanks to Werner van Geit for an initial version of a python wrapper for jnml.

"""

from __future__ import absolute_import
from __future__ import print_function
import os
import sys
import subprocess
import math
from datetime import datetime

from pyneuroml import __version__
from pyneuroml import JNEUROML_VERSION

import neuroml
import neuroml.loaders as loaders
import neuroml.writers as writers

import lems.model.model as lems_model
from lems.parser.LEMS import LEMSFileParser

import random
import inspect
import zipfile
import shlex
import signal

DEFAULTS = {'v':False, 
            'default_java_max_memory':'400M',
            'nogui': False}

lems_model_with_units = None

def parse_arguments():
    """Parse command line arguments"""

    import argparse

    parser = argparse.ArgumentParser(
            description=('pyNeuroML v%s: Python utilities for NeuroML2' % __version__ 
                          + "\n    libNeuroML v%s"%(neuroml.__version__)
                          + "\n    jNeuroML v%s"%JNEUROML_VERSION),
            usage=('pynml [-h|--help] [<shared options>] '
                   '<one of the mutually-exclusive options>'),
            formatter_class=argparse.RawTextHelpFormatter
            )

    shared_options = parser.add_argument_group(
            title='Shared options',
            description=('These options can be added to any of the '
                         'mutually-exclusive options')
            )

    shared_options.add_argument(
            '-verbose',
            action='store_true',
            default=DEFAULTS['v'],
            help='Verbose output'
            )
    shared_options.add_argument(
            '-java_max_memory',
            metavar='MAX',
            default=DEFAULTS['default_java_max_memory'],
            help=('Java memory for jNeuroML, e.g. 400M, 2G (used in\n'
                  '-Xmx argument to java)')
            )
    shared_options.add_argument(
            '-nogui',
            action='store_true',
            default=DEFAULTS['nogui'],
            help=('Suppress GUI,\n'
                  'i.e. show no plots, just save results')
            )
            
    shared_options.add_argument(
            'lems_file',
            type=str,
            metavar='<LEMS/NeuroML 2 file>',
            help='LEMS/NeuroML 2 file to process'
            )
            
    mut_exc_opts_grp = parser.add_argument_group(
            title='Mutually-exclusive options',
            description='Only one of these options can be selected'
            )
    mut_exc_opts = mut_exc_opts_grp.add_mutually_exclusive_group(required=False)
     
    mut_exc_opts.add_argument(
            '-sedml',
            action='store_true',
            help=('(Via jNeuroML) Load a LEMS file, and convert\n'
                  'simulation settings (duration, dt, what to save)\n'
                  'to SED-ML format')
            )
    mut_exc_opts.add_argument(
            '-neuron',
            nargs=argparse.REMAINDER,
            help=('(Via jNeuroML) Load a LEMS file, and convert it to\n'
                  'NEURON format.\n'
                  'The full format of the \'-neuron\' option is:\n'
                  '-neuron [-nogui] [-run] [-outputdir dir] <LEMS file>\n'
                  '    -nogui\n'
                  '        do not generate gtaphical elements in NEURON,\n'
                  '        just run, save data, and quit\n'
                  '    -run\n'
                  '        compile NMODL files and run the main NEURON\n'
                  '        hoc file (Linux only currently)\n'
                  '    -outputdir <dir>\n'
                  '        generate NEURON files in directory <dir>\n'
                  '    <LEMS file>\n'
                  '        the LEMS file to use')
            )
    mut_exc_opts.add_argument(
            '-svg',
            action='store_true',
            help=('(Via jNeuroML) Convert NeuroML2 file (network & cells)\n'
                  'to SVG format view of 3D structure')
            )
    mut_exc_opts.add_argument(
            '-png',
            action='store_true',
            help=('(Via jNeuroML) Convert NeuroML2 file (network & cells)\n'
                  'to PNG format view of 3D structure')
            )
    mut_exc_opts.add_argument(
            '-dlems',
            action='store_true',
            help=('(Via jNeuroML) Load a LEMS file, and convert it\n'
                  'to dLEMS format, a distilled form of LEMS in JSON')
            )
    mut_exc_opts.add_argument(
            '-vertex',
            action='store_true',
            help=('(Via jNeuroML) Load a LEMS file, and convert it\n'
                  'to VERTEX format')
            )
    mut_exc_opts.add_argument(
            '-xpp',
            action='store_true',
            help=('(Via jNeuroML) Load a LEMS file, and convert it\n'
                  'to XPPAUT format')
            )
    mut_exc_opts.add_argument(
            '-dnsim',
            action='store_true',
            help=('(Via jNeuroML) Load a LEMS file, and convert it\n'
                  'to DNsim format')
            )
    mut_exc_opts.add_argument(
            '-brian',
            action='store_true',
            help=('(Via jNeuroML) Load a LEMS file, and convert it\n'
                  'to Brian format')
            )
    mut_exc_opts.add_argument(
            '-sbml',
            action='store_true',
            help=('(Via jNeuroML) Load a LEMS file, and convert it\n'
                  'to SBML format')
            )
    mut_exc_opts.add_argument(
            '-matlab',
            action='store_true',
            help=('(Via jNeuroML) Load a LEMS file, and convert it\n'
                  'to MATLAB format')
            )
    mut_exc_opts.add_argument(
            '-cvode',
            action='store_true',
            help=('(Via jNeuroML) Load a LEMS file, and convert it\n'
                  'to C format using CVODE package')
            )
    mut_exc_opts.add_argument(
            '-nineml',
            action='store_true',
            help=('(Via jNeuroML) Load a LEMS file, and convert it\n'
                  'to NineML format')
            )
    mut_exc_opts.add_argument(
            '-spineml',
            action='store_true',
            help=('(Via jNeuroML) Load a LEMS file, and convert it\n'
                  'to SpineML format')
            )
    mut_exc_opts.add_argument(
            '-sbml-import',
            metavar=('<SBML file>', 'duration', 'dt'),
            nargs=3,
            help=('(Via jNeuroML) Load a SBML file, and convert it\n'
                  'toLEMS format using values for duration & dt\n'
                  'in ms (ignoring SBML units)')
            )
    mut_exc_opts.add_argument(
            '-sbml-import-units',
            metavar=('<SBML file>', 'duration', 'dt'),
            nargs=3,
            help=('(Via jNeuroML) Load a SBML file, and convert it\n'
                  'to LEMS format using values for duration & dt\n'
                  'in ms (attempt to extract SBML units; ensure units\n'
                  'are valid in the SBML!)')
            )
    mut_exc_opts.add_argument(
            '-vhdl',
            metavar=('neuronid', '<LEMS file>'),
            nargs=2,
            help=('(Via jNeuroML) Load a LEMS file, and convert it\n'
                  'to VHDL format')
            )
    mut_exc_opts.add_argument(
            '-validate',
            action='store_true',
            help=('(Via jNeuroML) Validate NeuroML2 file(s) against the\n'
                  'latest Schema')
            )
    mut_exc_opts.add_argument(
            '-validatev1',
            action='store_true',
            help=('(Via jNeuroML) Validate NeuroML file(s) against the\n'
                  'v1.8.1 Schema')
            )

    return parser.parse_args()



def get_lems_model_with_units():
    
    global lems_model_with_units
    
    if lems_model_with_units == None:
        jar_path = get_path_to_jnml_jar()
        #print_comment_v("Loading standard NeuroML2 dimension/unit definitions from %s"%jar_path)
        jar = zipfile.ZipFile(jar_path, 'r')
        dims_units = jar.read('NeuroML2CoreTypes/NeuroMLCoreDimensions.xml')
        lems_model_with_units = lems_model.Model(include_includes=False)
        parser = LEMSFileParser(lems_model_with_units)
        parser.parse(dims_units)
        
        
    return lems_model_with_units

    
def split_nml2_quantity(nml2_quantity):

    magnitude = None
    i = len(nml2_quantity)
    while magnitude is None:
        try:
            part = nml2_quantity[0:i]
            nn = float(part)
            magnitude = nn
            unit = nml2_quantity[i:]
        except ValueError:
            i = i-1
    
    return magnitude, unit

def get_value_in_si(nml2_quantity):
    
    try:
        return float(nml2_quantity)
    except:

        model = get_lems_model_with_units()
        m, u = split_nml2_quantity(nml2_quantity)
        si_value = None
        for un in model.units:
            if un.symbol == u:
                si_value =  (m + un.offset) * un.scale * pow(10, un.power)

        return si_value
    
def convert_to_units(nml2_quantity, unit, verbose=DEFAULTS['v']):
     
    model = get_lems_model_with_units()
    m, u = split_nml2_quantity(nml2_quantity)
    si_value = None
    dim = None
    for un in model.units:
        if un.symbol == u:
            si_value =  (m + un.offset) * un.scale * pow(10, un.power)
            dim = un.dimension
            
    for un in model.units:
        if un.symbol == unit:
            
            new_value = si_value / (un.scale * pow(10, un.power)) - un.offset 
            if not un.dimension == dim:
                raise Exception("Cannot convert %s to %s. Dimensions of units (%s/%s) do not match!"% \
                                (nml2_quantity,unit,dim,un.dimension))
    
    
    print_comment("Converting %s %s to %s: %s (%s in SI units)"%(m,u,unit,new_value,si_value),verbose)
    
    return new_value



def validate_neuroml1(nml1_file_name, verbose_validate=True):
    
    pre_args = "-validatev1"
    post_args = ""
        
    return run_jneuroml(pre_args, 
                 nml1_file_name, 
                 post_args,
                 verbose = verbose_validate,
                 exit_on_fail = False)


def validate_neuroml2(nml2_file_name, verbose_validate=True,max_memory=None):
    
    pre_args = "-validate"
    post_args = ""
        
    if max_memory !=None:
    
       return run_jneuroml(pre_args, 
                          nml2_file_name, 
                          post_args, 
                          max_memory=max_memory,
                          verbose = verbose_validate,
                          exit_on_fail = False)
    
    else:    
    
      return run_jneuroml(pre_args, 
                          nml2_file_name, 
                          post_args, 
                          verbose = verbose_validate,
                          exit_on_fail = False)
    

def read_neuroml2_file(nml2_file_name, include_includes=False, 
                       verbose=False, already_included=[], 
                       optimized=False, check_validity_pre_include=False):  
    
    print_comment("Loading NeuroML2 file: %s" % nml2_file_name, verbose)
    
    if not os.path.isfile(nml2_file_name):
        print_comment("Unable to find file: %s!" % nml2_file_name, True)
        sys.exit()
        
    if nml2_file_name.endswith('.h5') or nml2_file_name.endswith('.hdf5'):
        nml2_doc = loaders.NeuroMLHdf5Loader.load(nml2_file_name, optimized=optimized)
    else:
        nml2_doc = loaders.NeuroMLLoader.load(nml2_file_name)
    
    base_path = os.path.dirname(os.path.realpath(nml2_file_name))
    
    if include_includes:
        print_comment('Including included files (included already: %s)' \
                      % already_included, verbose)
        
        incl_to_remove = []
        for include in nml2_doc.includes:
            incl_loc = os.path.abspath(os.path.join(base_path, include.href))
            if incl_loc not in already_included:
                              
                inc = True
                if check_validity_pre_include:
                    inc = validate_neuroml2(incl_loc, verbose_validate=False)
                    
                print_comment("Loading included NeuroML2 file: %s (base: %s, resolved: %s, checking %s)" % (include.href, base_path, incl_loc,check_validity_pre_include), 
                              verbose)
                if inc:
                    nml2_sub_doc = read_neuroml2_file(incl_loc, True, 
                        verbose=verbose, already_included=already_included, 
                        check_validity_pre_include=check_validity_pre_include)
                    if not incl_loc in already_included:
                        already_included.append(incl_loc)

                    membs = inspect.getmembers(nml2_sub_doc)

                    for memb in membs:
                        if isinstance(memb[1], list) and len(memb[1])>0 \
                                and not memb[0].endswith('_'):
                            for entry in memb[1]:
                                if memb[0] != 'includes':
                                    print_comment("  Adding %s from: %s to list: %s" \
                                        %(entry, incl_loc, memb[0]))
                                    getattr(nml2_doc, memb[0]).append(entry)
                    incl_to_remove.append(include)
                else:
                    print_comment("Not including file as it's not valid...",verbose)
                      
        for include in incl_to_remove:
            nml2_doc.includes.remove(include)
            
    return nml2_doc


def quick_summary(nml2_doc):
    '''
    Or better just use nml2_doc.summary(show_includes=False)
    '''
    
    info = 'Contents of NeuroML 2 document: %s\n'%nml2_doc.id
    membs = inspect.getmembers(nml2_doc)

    for memb in membs:

        if isinstance(memb[1], list) and len(memb[1])>0 \
                and not memb[0].endswith('_'):
            info+='  %s:\n    ['%memb[0]
            for entry in memb[1]:
                extra = '???'
                extra = entry.name if hasattr(entry,'name') else extra
                extra = entry.href if hasattr(entry,'href') else extra
                extra = entry.id if hasattr(entry,'id') else extra
                
                info+=" %s (%s),"%(entry, extra)
            
            info+=']\n'
    return info


def write_neuroml2_file(nml2_doc, nml2_file_name, validate=True, 
                        verbose_validate=False):
    
    writers.NeuroMLWriter.write(nml2_doc,nml2_file_name)
    
    if validate:
        validate_neuroml2(nml2_file_name, verbose_validate)
        
        

def read_lems_file(lems_file_name, include_includes=False, fail_on_missing_includes=False, debug=False):
    
    if not os.path.isfile(lems_file_name):
        print_comment("Unable to find file: %s!"%lems_file_name, True)
        sys.exit()
        
    model = lems_model.Model(include_includes=include_includes, 
                             fail_on_missing_includes=fail_on_missing_includes)
    model.debug = debug
    
    model.import_from_file(lems_file_name)
    
    return model


def write_lems_file(lems_model, lems_file_name, validate=False):
    
    lems_model.export_to_file(lems_file_name)
    
    if validate:
        from lems.base.util import validate_lems
        validate_lems(lems_file_name)


def run_lems_with_jneuroml(lems_file_name, 
                           paths_to_include=[],
                           max_memory=DEFAULTS['default_java_max_memory'],
                           skip_run=False, 
                           nogui=False, 
                           load_saved_data=False, 
                           reload_events=False,
                           plot=False, 
                           show_plot_already=True, 
                           exec_in_dir = ".",
                           verbose=DEFAULTS['v'],
                           exit_on_fail = True,
                           cleanup=False):  
                               
    print_comment("Loading LEMS file: %s and running with jNeuroML" \
                  % lems_file_name, verbose)
    post_args = ""
    post_args += gui_string(nogui)
    post_args += include_string(paths_to_include)
    
    t_run = datetime.now()
    
    if not skip_run:
        success = run_jneuroml("", 
                           lems_file_name, 
                           post_args, 
                           max_memory = max_memory, 
                           exec_in_dir = exec_in_dir, 
                           verbose = verbose, 
                           exit_on_fail = exit_on_fail)
    
    if not success: 
        return False
    
    if load_saved_data:
        return reload_saved_data(lems_file_name, 
                                 base_dir = exec_in_dir,
                                 t_run=t_run,
                                 plot=plot, 
                                 show_plot_already=show_plot_already, 
                                 simulator='jNeuroML',
                                 reload_events=reload_events,
                                 remove_dat_files_after_load=cleanup)
    else:
        return True
    
    

def nml2_to_svg(nml2_file_name, max_memory=DEFAULTS['default_java_max_memory'], 
                verbose=True):           
    print_comment("Converting NeuroML2 file: %s to SVG"%nml2_file_name, verbose)
    
    post_args = "-svg"
    
    run_jneuroml("", 
                 nml2_file_name, 
                 post_args, 
                 max_memory = max_memory, 
                 verbose = verbose)
    

def nml2_to_png(nml2_file_name, max_memory=DEFAULTS['default_java_max_memory'], 
                verbose=True):           
    print_comment("Converting NeuroML2 file: %s to PNG"%nml2_file_name, verbose)
    
    post_args = "-png"
    
    run_jneuroml("", 
                 nml2_file_name, 
                 post_args, 
                 max_memory = max_memory, 
                 verbose = verbose)


def include_string(paths_to_include):
  if paths_to_include:
    if type(paths_to_include) is str:
      paths_to_include = [paths_to_include]
    if type(paths_to_include) in (tuple,list):
      result = " -I '%s'" % ':'.join(paths_to_include)
  else:
    result = ""
  return result


def gui_string(nogui):
  return " -nogui" if nogui else ""


def run_lems_with_jneuroml_neuron(lems_file_name, 
                                  paths_to_include = [],
                                  max_memory = DEFAULTS['default_java_max_memory'], 
                                  skip_run = False,
                                  nogui = False, 
                                  load_saved_data = False, 
                                  reload_events = False,
                                  plot = False, 
                                  show_plot_already = True, 
                                  exec_in_dir = ".",
                                  only_generate_scripts = False,
                                  compile_mods = True,
                                  verbose = DEFAULTS['v'],
                                  exit_on_fail = True,
                                  cleanup=False,
                                  realtime_output=False):
                                  #jnml_runs_neuron=True):  #jnml_runs_neuron=False is Work in progress!!!
                          
    print_comment("Loading LEMS file: %s and running with jNeuroML_NEURON" % lems_file_name, verbose)
                  
    post_args = " -neuron"
    if not only_generate_scripts:# and jnml_runs_neuron:
        post_args += ' -run'
    if compile_mods:
        post_args += ' -compile'
    
    post_args += gui_string(nogui)
    post_args += include_string(paths_to_include)
    
    t_run = datetime.now()
    if skip_run:
      success = True
    else:
        
        # Fix PYTHONPATH for NEURON: has been an issue on HBP Collaboratory...
        if not 'PYTHONPATH' in os.environ:
            os.environ['PYTHONPATH']=''
        for path in sys.path:
            if not path+":" in os.environ['PYTHONPATH']:
                os.environ['PYTHONPATH'] = '%s:%s'%(path,os.environ['PYTHONPATH'])

        print_comment('PYTHONPATH for NEURON: %s'%os.environ['PYTHONPATH'], verbose)

        if realtime_output:
            success = run_jneuroml_with_realtime_output("", 
                           lems_file_name, 
                           post_args, 
                           max_memory = max_memory, 
                           exec_in_dir = exec_in_dir, 
                           verbose = verbose, 
                           exit_on_fail = exit_on_fail)

        #print_comment('PYTHONPATH for NEURON: %s'%os.environ['PYTHONPATH'], verbose)

        else: 
            success = run_jneuroml("", 
                           lems_file_name, 
                           post_args, 
                           max_memory = max_memory, 
                           exec_in_dir = exec_in_dir, 
                           verbose = verbose, 
                           exit_on_fail = exit_on_fail)
                          
        #TODO: Work in progress!!!
        #if not jnml_runs_neuron:
        #    print_comment("Running...",verbose)
        #    from LEMS_NML2_Ex5_DetCell_nrn import NeuronSimulation
        #    ns = NeuronSimulation(tstop=300, dt=0.01, seed=123456789)
        #    ns.run()
    
    if not success: 
        return False
    
    if load_saved_data:
        return reload_saved_data(lems_file_name, 
                                 base_dir = exec_in_dir, 
                                 t_run = t_run,
                                 plot = plot, 
                                 show_plot_already = show_plot_already, 
                                 simulator = 'jNeuroML_NEURON',
                                 reload_events = reload_events,
                                 remove_dat_files_after_load = cleanup)
    else:
        return True


def run_lems_with_jneuroml_netpyne(lems_file_name,
                                  paths_to_include = [], 
                                  max_memory = DEFAULTS['default_java_max_memory'], 
                                  skip_run = False,
                                  nogui = False, 
                                  num_processors = 1, 
                                  load_saved_data = False, 
                                  reload_events = False,
                                  plot = False, 
                                  show_plot_already = True, 
                                  exec_in_dir = ".",
                                  only_generate_scripts = False,
                                  verbose = DEFAULTS['v'],
                                  exit_on_fail = True,
                                  cleanup = False):
                                      
    print_comment("Loading LEMS file: %s and running with jNeuroML_NetPyNE" \
                  % lems_file_name, verbose)
                  
    post_args = " -netpyne"
    
    if num_processors!=1:
        post_args += ' -np %i'%num_processors
    if not only_generate_scripts:
        post_args += ' -run'
    
    post_args += gui_string(nogui)
    post_args += include_string(paths_to_include)
    
    t_run = datetime.now()
    if skip_run:
      success = True
    else:
      success = run_jneuroml("", 
                           lems_file_name, 
                           post_args, 
                           max_memory = max_memory, 
                           exec_in_dir = exec_in_dir, 
                           verbose = verbose, 
                           exit_on_fail = exit_on_fail)
    
    if not success: 
        return False
    
    if load_saved_data:
        return reload_saved_data(lems_file_name, 
                                 base_dir = exec_in_dir,
                                 t_run = t_run,
                                 plot = plot, 
                                 show_plot_already = show_plot_already, 
                                 simulator = 'jNeuroML_NEURON',
                                 reload_events = reload_events,
                                 remove_dat_files_after_load = cleanup)
    else:
        return True
    
    
def reload_saved_data(lems_file_name, 
                      base_dir = '.',
                      t_run = datetime(1900,1,1),
                      plot = False, 
                      show_plot_already = True, 
                      simulator = None, 
                      reload_events = False, 
                      verbose = DEFAULTS['v'],
                      remove_dat_files_after_load = False): 
                              
    if not os.path.isfile(lems_file_name):
        real_lems_file = os.path.realpath(os.path.join(base_dir,lems_file_name))
    else:
        real_lems_file = os.path.realpath(lems_file_name)
        
    print_comment("Reloading data specified in LEMS file: %s (%s), base_dir: %s, cwd: %s" \
                  % (lems_file_name,real_lems_file,base_dir,os.getcwd()), True)
    
    # Could use pylems to parse all this...
    traces = {}
    events = {}
    
    if plot:
        import matplotlib.pyplot as plt

    from lxml import etree
    base_lems_file_path = os.path.dirname(os.path.realpath(lems_file_name))
    tree = etree.parse(real_lems_file)
    
    sim = tree.getroot().find('Simulation')
    ns_prefix = ''
    
    possible_prefixes = ['{http://www.neuroml.org/lems/0.7.2}']
    if sim is None:
        #print(tree.getroot().nsmap)
        #print(tree.getroot().getchildren())
        for pre in possible_prefixes:
            for comp in tree.getroot().findall(pre+'Component'):
                if comp.attrib['type'] == 'Simulation':
                    ns_prefix = pre
                    sim = comp
        
    if reload_events:
        event_output_files = sim.findall(ns_prefix+'EventOutputFile')
        for i,of in enumerate(event_output_files):
            name = of.attrib['fileName']
            file_name = os.path.join(base_dir,name)
            if not os.path.isfile(file_name): # If not relative to the LEMS file...
                file_name = os.path.join(base_lems_file_path,name) 
            
            #if not os.path.isfile(file_name): # If not relative to the LEMS file...
            #    file_name = os.path.join(os.getcwd(),name) 
                # ... try relative to cwd.  
            #if not os.path.isfile(file_name): # If not relative to the LEMS file...
            #    file_name = os.path.join(os.getcwd(),'NeuroML2','results',name) 
                # ... try relative to cwd in NeuroML2/results subdir.  
            if not os.path.isfile(file_name): # If not relative to the base dir...
                raise OSError(('Could not find simulation output '
                               'file %s' % file_name))
            format = of.attrib['format']
            print_comment("Loading saved events from %s (format: %s)"%(file_name, format), 
                             True)
            selections = {}
            for col in of.findall(ns_prefix+'EventSelection'):
                id = int(col.attrib['id'])
                select = col.attrib['select']
                events[select] = []
                selections[id] = select

            with open(file_name) as f:
              for line in f:
                values = line.split() 
                if format == 'TIME_ID':
                    t = float(values[0])
                    id = int(values[1])
                elif format == 'ID_TIME':
                    id = int(values[0])
                    t = float(values[1])
                #print_comment("Found a event in cell %s (%s) at t = %s"%(id,selections[id],t))
                events[selections[id]].append(t)
                
            if remove_dat_files_after_load:
                print_comment_v("Removing file %s after having loading its data!"%file_name)
                os.remove(file_name)

    
    output_files = sim.findall(ns_prefix+'OutputFile')
    n_output_files = len(output_files)    
    if plot:
        rows = int(max(1,math.ceil(n_output_files/float(3))))
        columns = min(3,n_output_files)
        fig,ax = plt.subplots(rows,columns,sharex=True,
                              figsize=(8*columns,4*rows))
        if n_output_files>1:
            ax = ax.ravel()
    
    for i,of in enumerate(output_files):
        traces['t'] = []
        name = of.attrib['fileName']
        file_name = os.path.join(base_dir,name)
        
        if not os.path.isfile(file_name): # If not relative to the LEMS file...
            file_name = os.path.join(base_lems_file_path,name) 
            
        if not os.path.isfile(file_name): # If not relative to the LEMS file...
            file_name = os.path.join(os.getcwd(),name) 

            # ... try relative to cwd.  
        if not os.path.isfile(file_name): # If not relative to the LEMS file...
            file_name = os.path.join(os.getcwd(),'NeuroML2','results',name) 
            # ... try relative to cwd in NeuroML2/results subdir.  
        if not os.path.isfile(file_name): # If not relative to the LEMS file...
            raise OSError(('Could not find simulation output '
                           'file %s' % file_name))
        t_file_mod = datetime.fromtimestamp(os.path.getmtime(file_name))
        if t_file_mod < t_run:
          raise Exception("Expected output file %s has not been modified since "
                         "%s but the simulation was run later at %s." 
                         % (file_name,t_file_mod,t_run))

        print_comment("Loading saved data from %s%s" \
                      % (file_name, ' (%s)'%simulator if simulator else ''), 
                         verbose)
        
        cols = []
        cols.append('t')
        for col in of.findall(ns_prefix+'OutputColumn'):
            quantity = col.attrib['quantity']
            traces[quantity] = []
            cols.append(quantity)
            
        with open(file_name) as f:
          for line in f:
            values = line.split()
            for vi in range(len(values)):
              traces[cols[vi]].append(float(values[vi]))

        if remove_dat_files_after_load:
            print_comment_v("Removing file %s after having loading its data!"%file_name)
            os.remove(file_name)

        if plot:
            info = "Data loaded from %s%s" \
                                        % (file_name, ' (%s)' % simulator 
                                                      if simulator else '')
            print_comment_v("Reloading: %s"%info)
            fig.canvas.set_window_title(info)
            
            legend = False
            for key in cols:
                if n_output_files>1:
                    ax_ = ax[i]
                else:
                    ax_ = ax
                ax_.set_xlabel('Time (ms)')
                ax_.set_ylabel('(SI units...)')
                ax_.xaxis.grid(True)
                ax_.yaxis.grid(True)

                if key != 't':
                    ax_.plot(traces['t'], traces[key], label=key)
                    print_comment("Adding trace for: %s, from: %s" \
                                  % (key,file_name), verbose)
                    ax_.used = True
                    legend = True
                
                if legend:
                    if n_output_files>1:
                        ax_.legend(loc='upper right', fancybox=True, shadow=True, 
                                     ncol=4)#, bbox_to_anchor=(0.5, -0.05))
                    else:
                        ax_.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=4) 
                   
    #print(traces.keys())
        
    if plot and show_plot_already:
        
        if n_output_files>1:
            ax_ = ax
        else:
            ax_ = [ax]
        for axi in ax_:
            if not hasattr(axi,'used') or not axi.used:
                axi.axis('off')
        plt.tight_layout()
        plt.show()
        
    if reload_events:
        return traces, events
    else:
        return traces
               
                        
def get_next_hex_color():
    
    return "#%06x" % random.randint(0,0xFFFFFF)

def evaluate_arguments(args):

    global DEFAULTS
    DEFAULTS['v'] = args.verbose

    pre_args = ""
    files = ""
    post_args = ""
    exit_on_fail = True
    
    files = args.lems_file
        
    if args.nogui:
        post_args = "-nogui"
        
    if args.sedml:
        post_args = "-sedml"
    elif args.neuron is not None:
        num_neuron_args = len(args.neuron)
        if num_neuron_args < 0 or num_neuron_args > 4:
            print("ERROR: The \'-neuron\' option was given an invalid "
                  "number of arguments: %d given, 0-4 required"
                  % num_neuron_args)
            sys.exit(-1)
        post_args = "-neuron %s" % ' '.join(args.neuron[:-1])
    elif args.svg:
        post_args = "-svg"
    elif args.png:
        post_args = "-png"
    elif args.dlems:
        post_args = "-dlems"
    elif args.vertex:
        post_args = "-vertex"
    elif args.xpp:
        post_args = "-xpp"
    elif args.dnsim:
        post_args = "-dnsim"
    elif args.brian:
        post_args = "-brian"
    elif args.sbml:
        post_args = "-sbml"
    elif args.matlab:
        post_args = "-matlab"
    elif args.cvode:
        post_args = "-cvode"
    elif args.nineml:
        post_args = "-nineml"
    elif args.spineml:
        post_args = "-spineml"
    elif args.sbml_import:
        pre_args = "-sbml-import"
        files = args.sbml_import[0]
        post_args = ' '.join(args.sbml_import[1:])
    elif args.sbml_import_units:
        pre_args = "-smbl-import-units"
        files = args.sbml_import_units[0]
        post_args = ' '.join(args.sbml_import_units[1:])
    elif args.vhdl:
        files = args.vhdl[1]
        post_args = "-vhdl %s" % args.vhdl[0]
    elif args.validate:
        pre_args = "-validate"
        exit_on_fail = True
    elif args.validatev1:
        pre_args = "-validatev1"
        exit_on_fail = True
        

    run_jneuroml(pre_args,
                 files,
                 post_args,
                 max_memory = args.java_max_memory,
                 exit_on_fail = exit_on_fail)

def get_path_to_jnml_jar():

    script_dir = os.path.dirname(os.path.realpath(__file__))

    jar_path = os.path.join(script_dir, "lib", 
                       "jNeuroML-%s-jar-with-dependencies.jar" % JNEUROML_VERSION)
            
    return jar_path

def run_jneuroml(pre_args, 
                 target_file, 
                 post_args, 
                 max_memory   = DEFAULTS['default_java_max_memory'], 
                 exec_in_dir  = ".",
                 verbose      = DEFAULTS['v'],
                 exit_on_fail = True):    

    if 'nogui' in post_args and not os.name == 'nt':
        pre_jar = " -Djava.awt.headless=true"
    else:
        pre_jar = ""
        
    jar_path = get_path_to_jnml_jar()
    
    output = ''

    
    try:
        command = 'java -Xmx%s %s -jar  "%s" %s "%s" %s' % \
          (max_memory, pre_jar, jar_path, pre_args, target_file, post_args)
        output = execute_command_in_dir(command, exec_in_dir, verbose=verbose,
                                        prefix = ' jNeuroML >>  ')
                          
        if not output:
            if exit_on_fail: 
                sys.exit(-1)
            else:
                return False

    #except KeyboardInterrupt as e:
    #    raise e
            
    except Exception as e:
        print_comment('*** Execution of jnml has failed! ***', True)
        print_comment('Error:  %s'%e)
        print_comment('*** Command: %s ***'%command, True)
        print_comment('Output: %s'%output, True)
        if exit_on_fail: 
            sys.exit(-1)
        else:
            return False
        
    
    return True


# TODO: Refactorinng
def run_jneuroml_with_realtime_output(pre_args, 
                                      target_file, 
                                      post_args, 
                                      max_memory   = DEFAULTS['default_java_max_memory'], 
                                      exec_in_dir  = ".",
                                      verbose      = DEFAULTS['v'],
                                      exit_on_fail = True):    

    # NOTE: Only tested with Linux

    if 'nogui' in post_args and not os.name == 'nt':
        pre_jar = " -Djava.awt.headless=true"
    else:
        pre_jar = ""
        
    jar_path = get_path_to_jnml_jar()
    
    command = ''
    output = ''

    try:
        command = 'java -Xmx%s %s -jar  "%s" %s "%s" %s' % \
              (max_memory, pre_jar, jar_path, pre_args, target_file, post_args)
        output = execute_command_in_dir_with_realtime_output(command, exec_in_dir, verbose=verbose,
                                        prefix = ' jNeuroML >>  ')
    except KeyboardInterrupt as e:
        raise e
    except:
        print_comment('*** Execution of jnml has failed! ***', True)
        print_comment('*** Command: %s ***'%command, True)
        if exit_on_fail: 
            sys.exit(-1)
        else:
            return False
    
    return True

    
def print_comment_v(text):
    print_comment(text, True)
    
    
def print_comment(text, print_it=DEFAULTS['v']):
    prefix = "pyNeuroML >>> "
    if not isinstance(text, str): text = text.decode('ascii')
    if print_it:
        
        print("%s%s"%(prefix, text.replace("\n", "\n"+prefix)))


def execute_command_in_dir_with_realtime_output(command, directory, verbose=DEFAULTS['v'], 
                                                prefix="Output: ", env=None):

    # NOTE: Only tested with Linux
    if os.name == 'nt':
        directory = os.path.normpath(directory)
        
    print_comment("Executing: (%s) in directory: %s" % (command, directory), verbose)
    if env is not None:
        print_comment("Extra env variables %s" % (env), verbose)

    p = None
    try:
        p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, bufsize=1, cwd=directory, env=env)
        with p.stdout:
            for line in iter(p.stdout.readline, b''):
                print(line, end="")
        p.wait() # wait for the subprocess to exit
    except KeyboardInterrupt as e:
        if p:
            p.kill()
        #return True
        raise e

    return True


def execute_command_in_dir(command, directory, verbose=DEFAULTS['v'], 
                           prefix="Output: ", env=None):
    
    """Execute a command in specific working directory"""
    
    if os.name == 'nt':
        directory = os.path.normpath(directory)
        
    print_comment("Executing: (%s) in directory: %s" % (command, directory),
                  verbose)
    if env is not None:
        print_comment("Extra env variables %s" % (env), verbose)
    
    try:
        if os.name == 'nt':
            return_string = subprocess.check_output(command, 
                                                    cwd=directory, 
                                                    shell=True, 
                                                    env=env,
                                                    close_fds=False)
        else:
            return_string = subprocess.check_output(command, 
                                                    cwd=directory, 
                                                    shell=True, 
                                                    stderr=subprocess.STDOUT,
                                                    env=env,
                                                    close_fds=True)
        
        return_string = return_string.decode("utf-8") # For Python 3
                                
        print_comment('Command completed. Output: \n %s%s' % \
                      (prefix,return_string.replace('\n','\n '+prefix)), 
                      verbose)

        return return_string
    
    except AttributeError:
        # For python 2.6...
        print_comment_v('Assuming Python 2.6...')
        
        return_string = subprocess.Popen(command, 
                                         cwd=directory, 
                                         shell=True,
                                         stdout=subprocess.PIPE).communicate()[0]
        return return_string
    
    except subprocess.CalledProcessError as e:        
        
        print_comment_v('*** Problem running command: \n       %s'%e)
        print_comment_v('%s%s'%(prefix,e.output.decode().replace('\n','\n'+prefix)))
        
        return None
        
    except:
        print_comment_v('*** Unknown problem running command: %s'%e)
        
        return None
        
    print_comment("Finished execution", verbose)
        
    
    
def generate_plot(xvalues, 
                  yvalues, 
                  title,
                  labels = None, 
                  colors = None, 
                  linestyles = None, 
                  linewidths = None, 
                  markers = None, 
                  markersizes = None, 
                  xaxis = None, 
                  yaxis = None, 
                  xlim = None,
                  ylim = None,
                  show_xticklabels = True,
                  show_yticklabels = True,
                  grid = False,
                  logx = False,
                  logy = False,
                  font_size = 12,
                  bottom_left_spines_only = False,
                  cols_in_legend_box=3,
                  show_plot_already=True,
                  save_figure_to=None,
                  title_above_plot=False,
                  verbose=False):
               
    print_comment_v("Generating plot: %s"%(title))       
                      
    from matplotlib import pyplot as plt
    from matplotlib import rcParams
    
    rcParams.update({'font.size': font_size})

    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    fig.canvas.set_window_title(title)
    if title_above_plot:
        plt.title(title)
            
    if xaxis:
        plt.xlabel(xaxis)
    if yaxis:
        plt.ylabel(yaxis)
        
    if grid:
        plt.grid('on')
        
    if logx:
        ax.set_xscale("log")
    if logy:
        ax.set_yscale("log")
        
    if bottom_left_spines_only:
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)       
        ax.yaxis.set_ticks_position('left')
        ax.xaxis.set_ticks_position('bottom')
    
    if not show_xticklabels:
        ax.set_xticklabels([])
    if not show_yticklabels:
        ax.set_yticklabels([])

    for i in range(len(xvalues)):

        linestyle = '-' if not linestyles else linestyles[i]
        label = '' if not labels else labels[i]
        marker = None if not markers else markers[i]
        linewidth = 1 if not linewidths else linewidths[i]
        markersize= 6 if not markersizes else markersizes[i]
        
        if colors:
            plt.plot(xvalues[i], yvalues[i], 'o', color=colors[i], marker=marker, markersize=markersize, linestyle=linestyle, linewidth=linewidth, label=label)
        else:
            plt.plot(xvalues[i], yvalues[i], 'o', marker=marker, markersize=markersize, linestyle=linestyle, linewidth=linewidth, label=label)

    if labels:
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=cols_in_legend_box)
        
    if xlim:
        plt.xlim(xlim)
    if ylim:
        plt.ylim(ylim)

    if save_figure_to:
        print_comment("Saving image to %s of plot: %s"%(os.path.abspath(save_figure_to),title),verbose)
        plt.savefig(save_figure_to,bbox_inches='tight')
        print_comment_v("Saved image to %s of plot: %s"%(save_figure_to,title))
        
    if show_plot_already:
        plt.show()
        
    return ax
        
'''
    As usually saved by jLEMS, etc. First column is time (in seconds), multiple other columns
'''
def reload_standard_dat_file(file_name):

    dat_file = open(file_name)
    data = {}
    indeces = []
    for line in dat_file:
        words = line.split()

        if not 't' in data.keys():
            data['t'] = []
            for i in range(len(words)-1):
                data[i] = []
                indeces.append(i)
        data['t'].append(float(words[0]))
        for i in range(len(words)-1):
            data[i].append(float(words[i+1]))

    print_comment_v("Loaded data from %s; columns: %s"%(file_name, indeces))
    
    dat_file.close()

    return data, indeces




def _find_elements(el, name, rdf=False):
    ns = 'http://www.neuroml.org/schema/neuroml2'
    if rdf:
        ns = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
    return el.findall('.//{%s}%s'%(ns,name))


def _get_attr_in_element(el, name, rdf=False):
    ns = 'http://www.neuroml.org/schema/neuroml2'
    if rdf:
        ns = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
    aname = '{%s}%s'%(ns,name)
    return el.attrib[aname] if aname in el.attrib else None



def extract_annotations(nml2_file):
    
    from lxml import etree
    
    import pprint; pp = pprint.PrettyPrinter()

    test_file = open(nml2_file)

    root = etree.parse(test_file).getroot()
    
    annotations = {}

    for a in _find_elements(root,'annotation'):

        for r in _find_elements(a,'Description',rdf=True):
            
            desc = _get_attr_in_element(r,'about',rdf=True)
            
            annotations[desc] = []

            for info in r:
                if isinstance(info.tag, str):
                    kind = info.tag.replace('{http://biomodels.net/biology-qualifiers/}','bqbiol:')
                    kind = kind.replace('{http://biomodels.net/model-qualifiers/}','bqmodel:')

                    for li in _find_elements(info,'li',rdf=True):

                        attr = _get_attr_in_element(li,'resource',rdf=True)
                        if attr:
                            annotations[desc].append({kind: attr})


    print_comment_v("Annotations in %s: "%(nml2_file))
    pp.pprint(annotations)

'''
Work in progress: expand a (simple) ComponentType  and evaluate an instance of it by
giving parameters & required variables
'''
def evaluate_component(comp_type, req_variables={}, parameter_values={}):
    
    print_comment('Evaluating %s with req:%s; params:%s'%(comp_type.name,req_variables,parameter_values))
    exec_str = ''
    return_vals = {}
    from math import exp
    for p in parameter_values:
        exec_str+='%s = %s\n'%(p, get_value_in_si(parameter_values[p]))
    for r in req_variables:
        exec_str+='%s = %s\n'%(r, get_value_in_si(req_variables[r]))
    for c in comp_type.Constant:
        exec_str+='%s = %s\n'%(c.name, get_value_in_si(c.value))
    for d in comp_type.Dynamics:
        for dv in d.DerivedVariable:
            exec_str+='%s = %s\n'%(dv.name, dv.value)
            exec_str+='return_vals["%s"] = %s\n'%(dv.name, dv.name)
        for cdv in d.ConditionalDerivedVariable:
            for case in cdv.Case:
                if case.condition:
                    cond = case.condition.replace('.neq.','!=').replace('.eq.','==').replace('.gt.','<').replace('.lt.','<')
                    exec_str+='if ( %s ): %s = %s \n'%(cond, cdv.name, case.value)
                else:
                    exec_str+='else: %s = %s \n'%(cdv.name, case.value)
                
            exec_str+='\n'
                
            exec_str+='return_vals["%s"] = %s\n'%(cdv.name, cdv.name)
          
    '''print_comment_v(exec_str)'''
    exec(exec_str)
    
    return return_vals
    
def main(args=None):
    """Main"""

    if args is None:
        args = parse_arguments()

    evaluate_arguments(args)


if __name__ == "__main__":
    main()

