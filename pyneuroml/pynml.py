#!/usr/bin/env python
"""

Python wrapper around jnml command.
Also a number of helper functions for
handling/generating/running LEMS/NeuroML2 files

Thanks to Werner van Geit for an initial version of a python wrapper for jnml.

"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
import os
import sys
import subprocess
import math
from datetime import datetime
import textwrap
import random
import inspect
import zipfile
import shlex
from lxml import etree
import pprint

import lems.model.model as lems_model
from lems.parser.LEMS import LEMSFileParser

from pyneuroml import __version__
from pyneuroml import JNEUROML_VERSION

import neuroml
import neuroml.loaders as loaders
import neuroml.writers as writers


DEFAULTS = {'v': False,
            'default_java_max_memory': '400M',
            'nogui': False}

lems_model_with_units = None


def parse_arguments():
    """Parse command line arguments"""

    import argparse
    try:
        from neuromllite.GraphVizHandler import engines
        engine_info = '\nAvailable engines: %s\n' % str(engines)
    except:
        engine_info = ''

    parser = argparse.ArgumentParser(
        description=('pyNeuroML v{}: Python utilities for NeuroML2'.format(__version__) +\
                     "\n    libNeuroML v{}".format(neuroml.__version__) +\
                     "\n    jNeuroML v{}".format(JNEUROML_VERSION)),
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
        'input_files',
        type=str,
        nargs='*',
        metavar='<LEMS/NeuroML 2 file(s)>',
        help='LEMS/NeuroML 2 file(s) to process'
    )

    mut_exc_opts_grp = parser.add_argument_group(
        title='Mutually-exclusive options',
        description='Only one of these options can be selected'
    )
    mut_exc_opts = mut_exc_opts_grp.add_mutually_exclusive_group(required=False)  # noqa: E501

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
        '-graph',
        metavar=('level'),
        nargs=1,
        help=('Load a NeuroML file, and convert it to a graph using GraphViz.\n'
              'Detail is set by level (min20..0..20, where min implies negative)\n'
              'An optional single letter suffix can be used to select engine\n'
              'Example: 1d for level 1, using the dot engine'+engine_info
              )
    )
    mut_exc_opts.add_argument(
        '-lems-graph',
        action='store_true',
        help=('(Via jNeuroML) Load LEMS file, and convert it to a \n'
              'graph using GraphViz.')
    )
    mut_exc_opts.add_argument(
        '-matrix',
        metavar=('level'),
        nargs=1,
        help=('Load a NeuroML file, and convert it to a matrix displaying\n'  # noqa: E501
              'connectivity. Detail is set by level (1, 2, etc.)')
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

    if lems_model_with_units is None:
        jar_path = get_path_to_jnml_jar()
        # print_comment_v("Loading standard NeuroML2 dimension/unit definitions from %s"%jar_path)
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
            i = i - 1

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
                si_value = (m + un.offset) * un.scale * pow(10, un.power)
        return si_value


def convert_to_units(nml2_quantity, unit, verbose=DEFAULTS['v']):
    model = get_lems_model_with_units()
    m, u = split_nml2_quantity(nml2_quantity)
    si_value = None
    dim = None
    for un in model.units:
        if un.symbol == u:
            si_value = (m + un.offset) * un.scale * pow(10, un.power)
            dim = un.dimension

    for un in model.units:
        if un.symbol == unit:

            new_value = si_value / (un.scale * pow(10, un.power)) - un.offset
            if not un.dimension == dim:
                raise Exception(
                    "Cannot convert {} to {}. Dimensions of units ({}/{}) do not match!".format(
                        nml2_quantity, unit, dim, un.dimension))

    print_comment("Converting {} {} to {}: {} ({} in SI units)".format(
        m, u, unit, new_value, si_value), verbose)

    return new_value


def generate_nmlgraph(nml2_file_name, level=1, engine='dot', verbose_generate=True):
    """Generate NeuroML graph.

    :nml2_file_name (string): NML file to parse
    :level (string): level of graph to generate (default: '1')
    :engine (string): graph engine to use (default: 'dot')
    :verbose_generate (boolean): output verbosity

    """
    from neuromllite.GraphVizHandler import GraphVizHandler
    from neuroml.hdf5.NeuroMLXMLParser import NeuroMLXMLParser
    from neuromllite.GraphVizHandler import engines

    print_comment('Converting %s to graphical form, level %i, engine %s' % (nml2_file_name, level, engine))

    handler = GraphVizHandler(level=level, engine=engine, nl_network=None)
    currParser = NeuroMLXMLParser(handler)
    currParser.parse(nml2_file_name)
    handler.finalise_document()

    print_comment("Done with GraphViz...")
    return 0


def generate_lemsgraph(lems_file_name, verbose_generate=True):
    """Generate LEMS graph using jNeuroML

    :lems_file_name (string): LEMS file to parse
    :verbose_generate (boolean): output verbosity
    """
    pre_args = ""
    post_args = "-lems-graph"

    return run_jneuroml(pre_args,
                        lems_file_name,
                        post_args,
                        verbose=verbose_generate,
                        report_jnml_output=verbose_generate,
                        exit_on_fail=True)


def validate_neuroml1(nml1_file_name, verbose_validate=True):
    pre_args = "-validatev1"
    post_args = ""

    return run_jneuroml(pre_args,
                        nml1_file_name,
                        post_args,
                        verbose=verbose_validate,
                        report_jnml_output=verbose_validate,
                        exit_on_fail=False)


def validate_neuroml2(nml2_file_name, verbose_validate=True,
                      max_memory=None):
    pre_args = "-validate"
    post_args = ""

    if max_memory is not None:
        return run_jneuroml(pre_args,
                            nml2_file_name,
                            post_args,
                            max_memory=max_memory,
                            verbose=verbose_validate,
                            report_jnml_output=verbose_validate,
                            exit_on_fail=False)
    else:
        return run_jneuroml(pre_args,
                            nml2_file_name,
                            post_args,
                            verbose=verbose_validate,
                            report_jnml_output=verbose_validate,
                            exit_on_fail=False)


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
        print_comment('Including included files (included already: {})'.format(
            already_included, verbose))

        incl_to_remove = []
        for include in nml2_doc.includes:
            incl_loc = os.path.abspath(os.path.join(base_path, include.href))
            if incl_loc not in already_included:

                inc = True
                if check_validity_pre_include:
                    inc = validate_neuroml2(incl_loc, verbose_validate=False)

                print_comment(
                    "Loading included NeuroML2 file: {} (base: {}, resolved: {}, checking {})".format(
                        include.href, base_path, incl_loc, check_validity_pre_include), verbose)
                if inc:
                    nml2_sub_doc = read_neuroml2_file(
                        incl_loc, True,
                        verbose=verbose, already_included=already_included,
                        check_validity_pre_include=check_validity_pre_include
                    )
                    if incl_loc not in already_included:
                        already_included.append(incl_loc)

                    membs = inspect.getmembers(nml2_sub_doc)

                    for memb in membs:
                        if isinstance(memb[1], list) and len(memb[1]) > 0 \
                                and not memb[0].endswith('_'):
                            for entry in memb[1]:
                                if memb[0] != 'includes':
                                    print_comment(
                                        "  Adding %s from: %s to list: {}".format(
                                            entry, incl_loc, memb[0])
                                    )
                                    getattr(nml2_doc, memb[0]).append(entry)
                    incl_to_remove.append(include)
                else:
                    print_comment("Not including file as it's not valid...", verbose)

        for include in incl_to_remove:
            nml2_doc.includes.remove(include)

    return nml2_doc


def quick_summary(nml2_doc):
    '''
    Or better just use nml2_doc.summary(show_includes=False)
    '''

    info = 'Contents of NeuroML 2 document: {}\n'.format(nml2_doc.id)
    membs = inspect.getmembers(nml2_doc)

    for memb in membs:

        if isinstance(memb[1], list) and len(memb[1]) > 0 \
                and not memb[0].endswith('_'):
            info += '  {}:\n    ['.format(memb[0])
            for entry in memb[1]:
                extra = '???'
                extra = entry.name if hasattr(entry, 'name') else extra
                extra = entry.href if hasattr(entry, 'href') else extra
                extra = entry.id if hasattr(entry, 'id') else extra

                info += " {} ({}),".format(entry, extra)

            info += ']\n'
    return info


def summary(nml2_doc=None, verbose=False):
    '''
    Based on nml2_doc.summary(show_includes=False)
    '''

    usage = textwrap.dedent(
        """
        Usage:

        pynml-summary <NeuroML file> [-v]

        Compulsory arguments:
        NeuroML file: name of file to summarise

        Optional arguments:

        -v:  enable verbose mode
        """
    )

    if '-v' in sys.argv:
        verbose = True
        sys.argv.remove('-v')

    if len(sys.argv) < 2:
        print("Argument required.")
        print(usage)
        return

    if nml2_doc is None:
        nml2_file_name = sys.argv[1]
        nml2_doc = read_neuroml2_file(nml2_file_name, include_includes=verbose)

    info = nml2_doc.summary(show_includes=False)

    if verbose:
        cell_info_str = ''
        for cell in nml2_doc.cells:
            cell_info_str += cell_info(cell) + '*\n'
        lines = info.split('\n')
        info = ''
        still_to_add = False
        for line in lines:
            if 'Cell: ' in line:
                still_to_add = True
                pass
            elif 'Network: ' in line:
                still_to_add = False
                if len(cell_info_str) > 0:
                    info += '%s' % cell_info_str
                info += '%s\n' % line
            else:
                if still_to_add and '******' in line:
                    if len(cell_info_str) > 0:
                        info += '%s' % cell_info_str
                info += '%s\n' % line
    print(info)


def cells_info(nml_file_name):
    from neuroml.loaders import read_neuroml2_file
    nml_doc = read_neuroml2_file(nml_file_name, include_includes=True, verbose=False, optimized=True)

    info = ''
    info += 'Extracting information on %i cells in %s' % (len(nml_doc.cells), nml_file_name)

    for cell in nml_doc.cells:
        info += cell_info(cell)
    return info


def cell_info(cell):
    info = ''
    prefix = '*  '
    info += prefix + 'Cell: %s\n' % cell.id
    tot_length = 0
    tot_area = 0
    for seg in cell.morphology.segments:
        info += (prefix + '  %s\n' % seg)
        dist = seg.distal
        prox = seg.proximal
        parent_id = seg.parent.segments if seg.parent else 'None (root segment)'
        length = cell.get_segment_length(seg.id)
        info += (prefix + '    Parent segment: %s\n' % (parent_id))
        info += (prefix + '    %s -> %s; seg length: %s um\n' % (prox, dist, length))

        tot_length += length
        area = cell.get_segment_surface_area(seg.id)
        volume = cell.get_segment_volume(seg.id)
        tot_area += area
        info += (prefix + '    Surface area: %s um2, volume: %s um3\n' % (area, volume))
    numseg = len(cell.morphology.segments)
    info += (prefix + '  Total length of %i segment%s: %s um; total area: %s um2\n' % (numseg, 's' if numseg > 1 else '', tot_length, tot_area))

    info += (prefix + '\n')

    for sg in cell.morphology.segment_groups:
        segs = cell.get_all_segments_in_group(sg.id)
        info += (prefix + '  %s;\tcontains %i segment%s\n' % (str(sg).replace(', ', ',\t'), len(segs), ', id: %s' % segs[0] if len(segs) == 1 else 's in total'))

    if len(cell.morphology.segment_groups) > 0:
        info += (prefix + '\n')

    seg_info = cell.get_segment_ids_vs_segments()
    if cell.biophysical_properties:
        for cd in cell.biophysical_properties.membrane_properties.channel_densities:
            # print dir(cd)
            group = cd.segment_groups if cd.segment_groups else 'all'
            info += (prefix + '  Channel density: %s on %s;\tconductance of %s through ion chan %s with ion %s, erev: %s\n' % (cd.id, group, cd.cond_density, cd.ion_channel, cd.ion, cd.erev))
            segs = cell.get_all_segments_in_group(group)
            for seg_id in segs:
                seg = seg_info[seg_id]

                cond_dens_si = get_value_in_si(cd.cond_density)
                surface_area_si = get_value_in_si('%s um2' % cell.get_segment_surface_area(seg_id))
                cond_si = cond_dens_si * surface_area_si
                cond_pS = convert_to_units('%sS' % cond_si, 'pS')
                info += (prefix + '    Channel is on %s,\ttotal conductance: %s S_per_m2 x %s m2 = %s S (%s pS)\n' % (seg, cond_dens_si, surface_area_si, cond_si, cond_pS))

        if len(cell.biophysical_properties.membrane_properties.channel_densities) > 0:
            info += (prefix + '\n')

        for sc in cell.biophysical_properties.membrane_properties.specific_capacitances:
            group = sc.segment_groups if sc.segment_groups else 'all'
            info += (prefix + '  Specific capacitance on %s: %s\n' % (group, sc.value))
            segs = cell.get_all_segments_in_group(group)
            for seg_id in segs:
                seg = seg_info[seg_id]
                spec_cap_si = get_value_in_si(sc.value)
                surface_area_si = get_value_in_si('%s um2' % cell.get_segment_surface_area(seg_id))
                cap_si = spec_cap_si * surface_area_si
                cap_pF = convert_to_units('%sF' % cap_si, 'pF')
                info += (prefix + '    Capacitance of %s,\ttotal capacitance: %s F_per_m2 x %s m2 = %s F (%s pF)\n' % (seg, spec_cap_si, surface_area_si, cap_si, cap_pF))

    return info


def write_neuroml2_file(nml2_doc, nml2_file_name, validate=True,
                        verbose_validate=False):

    writers.NeuroMLWriter.write(nml2_doc, nml2_file_name)

    if validate:
        validate_neuroml2(nml2_file_name, verbose_validate)


def read_lems_file(lems_file_name, include_includes=False, fail_on_missing_includes=False, debug=False):
    if not os.path.isfile(lems_file_name):
        print_comment("Unable to find file: %s!" % lems_file_name, True)
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
                           exec_in_dir=".",
                           verbose=DEFAULTS['v'],
                           exit_on_fail=True,
                           cleanup=False):

    print_comment("Loading LEMS file: %s and running with jNeuroML".format(
                  lems_file_name, verbose))
    post_args = ""
    post_args += gui_string(nogui)
    post_args += include_string(paths_to_include)

    t_run = datetime.now()

    if not skip_run:
        success = run_jneuroml(
            "",
            lems_file_name,
            post_args,
            max_memory=max_memory,
            exec_in_dir=exec_in_dir,
            verbose=verbose,
            report_jnml_output=verbose,
            exit_on_fail=exit_on_fail)

    if not success:
        return False

    if load_saved_data:
        return reload_saved_data(
            lems_file_name,
            base_dir=exec_in_dir,
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
    print_comment("Converting NeuroML2 file: %s to SVG" % nml2_file_name, verbose)

    post_args = "-svg"

    run_jneuroml("",
                 nml2_file_name,
                 post_args,
                 max_memory=max_memory,
                 verbose=verbose)


def nml2_to_png(nml2_file_name, max_memory=DEFAULTS['default_java_max_memory'],
                verbose=True):
    print_comment("Converting NeuroML2 file: %s to PNG" % nml2_file_name, verbose)

    post_args = "-png"

    run_jneuroml("",
                 nml2_file_name,
                 post_args,
                 max_memory=max_memory,
                 verbose=verbose)


def include_string(paths_to_include):
    if paths_to_include:
        if type(paths_to_include) is str:
            paths_to_include = [paths_to_include]
    if type(paths_to_include) in (tuple, list):
        result = " -I '%s'" % ':'.join(paths_to_include)
    else:
        result = ""
    return result


def gui_string(nogui):
    return " -nogui" if nogui else ""


def run_lems_with_jneuroml_neuron(
    lems_file_name,
    paths_to_include=[],
    max_memory=DEFAULTS['default_java_max_memory'],
    skip_run=False,
    nogui=False,
    load_saved_data=False,
    reload_events=False,
    plot=False,
    show_plot_already=True,
    exec_in_dir=".",
    only_generate_scripts=False,
    compile_mods=True,
    verbose=DEFAULTS['v'],
    exit_on_fail=True,
    cleanup=False,
        realtime_output=False):
    # jnml_runs_neuron=True):  #jnml_runs_neuron=False is Work in progress!!!

    print_comment("Loading LEMS file: %s and running with jNeuroML_NEURON" % lems_file_name, verbose)

    post_args = " -neuron"
    if not only_generate_scripts:  # and jnml_runs_neuron:
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
        if 'PYTHONPATH' not in os.environ:
            os.environ['PYTHONPATH'] = ''
        for path in sys.path:
            if path + ":" not in os.environ['PYTHONPATH']:
                os.environ['PYTHONPATH'] = '%s:%s' % (path, os.environ['PYTHONPATH'])

        # print_comment('PYTHONPATH for NEURON: %s'%os.environ['PYTHONPATH'], verbose)

        if realtime_output:
            success = run_jneuroml_with_realtime_output(
                "",
                lems_file_name,
                post_args,
                max_memory=max_memory,
                exec_in_dir=exec_in_dir,
                verbose=verbose,
                exit_on_fail=exit_on_fail)

        # print_comment('PYTHONPATH for NEURON: %s'%os.environ['PYTHONPATH'], verbose)

        else:
            success = run_jneuroml(
                "",
                lems_file_name,
                post_args,
                max_memory=max_memory,
                exec_in_dir=exec_in_dir,
                verbose=verbose,
                report_jnml_output=verbose,
                exit_on_fail=exit_on_fail)

        """
        TODO: Work in progress!!!
        if not jnml_runs_neuron:
          print_comment("Running...",verbose)
          from LEMS_NML2_Ex5_DetCell_nrn import NeuronSimulation
          ns = NeuronSimulation(tstop=300, dt=0.01, seed=123456789)
          ns.run()
        """

    if not success:
        return False

    if load_saved_data:
        return reload_saved_data(
            lems_file_name,
            base_dir=exec_in_dir,
            t_run=t_run,
            plot=plot,
            show_plot_already=show_plot_already,
            simulator='jNeuroML_NEURON',
            reload_events=reload_events,
            remove_dat_files_after_load=cleanup)
    else:
        return True


def run_lems_with_jneuroml_netpyne(
    lems_file_name,
    paths_to_include=[],
    max_memory=DEFAULTS['default_java_max_memory'],
    skip_run=False,
    nogui=False,
    num_processors=1,
    load_saved_data=False,
    reload_events=False,
    plot=False,
    show_plot_already=True,
    exec_in_dir=".",
    only_generate_scripts=False,
    verbose=DEFAULTS['v'],
    exit_on_fail=True,
    cleanup=False
):

    print_comment(
        "Loading LEMS file: %s and running with jNeuroML_NetPyNE".format(
            lems_file_name), verbose)

    post_args = " -netpyne"

    if num_processors != 1:
        post_args += ' -np %i' % num_processors
    if not only_generate_scripts:
        post_args += ' -run'

    post_args += gui_string(nogui)
    post_args += include_string(paths_to_include)

    t_run = datetime.now()
    if skip_run:
        success = True
    else:
        success = run_jneuroml(
            "",
            lems_file_name,
            post_args,
            max_memory=max_memory,
            exec_in_dir=exec_in_dir,
            verbose=verbose,
            exit_on_fail=exit_on_fail)

    if not success:
        return False

    if load_saved_data:
        return reload_saved_data(lems_file_name,
                                 base_dir=exec_in_dir,
                                 t_run=t_run,
                                 plot=plot,
                                 show_plot_already=show_plot_already,
                                 simulator='jNeuroML_NetPyNE',
                                 reload_events=reload_events,
                                 remove_dat_files_after_load=cleanup)
    else:
        return True


def run_lems_with_jneuroml_brian2(
    lems_file_name,
    paths_to_include=[],
    max_memory=DEFAULTS['default_java_max_memory'],
    skip_run=False,
    nogui=False,
    load_saved_data=False,
    reload_events=False,
    plot=False,
    show_plot_already=True,
    exec_in_dir=".",
    verbose=DEFAULTS['v'],
    exit_on_fail=True,
    cleanup=False
):

    print_comment(
        "Loading LEMS file: %s and running with jNeuroML_Brian2".format(
            lems_file_name), verbose)

    post_args = " -brian2"

    post_args += gui_string(nogui)
    post_args += include_string(paths_to_include)

    t_run = datetime.now()
    if skip_run:
        success = True
    else:
        success = run_jneuroml(
            "",
            lems_file_name,
            post_args,
            max_memory=max_memory,
            exec_in_dir=exec_in_dir,
            verbose=verbose,
            exit_on_fail=exit_on_fail)
        print('oooooo')
        import LEMS_SimFNTest_brian2
        print('eeee')

    if not success:
        return False

    if load_saved_data:
        return reload_saved_data(
            lems_file_name,
            base_dir=exec_in_dir,
            t_run=t_run,
            plot=plot,
            show_plot_already=show_plot_already,
            simulator='jNeuroML_Brian2',
            reload_events=reload_events,
            remove_dat_files_after_load=cleanup)
    else:
        return True


def reload_saved_data(lems_file_name,
                      base_dir='.',
                      t_run=datetime(1900, 1, 1),
                      plot=False,
                      show_plot_already=True,
                      simulator=None,
                      reload_events=False,
                      verbose=DEFAULTS['v'],
                      remove_dat_files_after_load=False):

    if not os.path.isfile(lems_file_name):
        real_lems_file = os.path.realpath(os.path.join(base_dir, lems_file_name))
    else:
        real_lems_file = os.path.realpath(lems_file_name)

    print_comment("Reloading data specified in LEMS file: %s (%s), base_dir: %s, cwd: %s; plotting %s"
                  % (lems_file_name, real_lems_file, base_dir, os.getcwd(), show_plot_already), True)

    # Could use pylems to parse all this...
    traces = {}
    events = {}

    if plot:
        import matplotlib.pyplot as plt

    base_lems_file_path = os.path.dirname(os.path.realpath(lems_file_name))
    tree = etree.parse(real_lems_file)

    sim = tree.getroot().find('Simulation')
    ns_prefix = ''

    possible_prefixes = ['{http://www.neuroml.org/lems/0.7.2}']
    if sim is None:
        # print(tree.getroot().nsmap)
        # print(tree.getroot().getchildren())
        for pre in possible_prefixes:
            for comp in tree.getroot().findall(pre + 'Component'):
                if comp.attrib['type'] == 'Simulation':
                    ns_prefix = pre
                    sim = comp

    if reload_events:
        event_output_files = sim.findall(ns_prefix + 'EventOutputFile')
        for i, of in enumerate(event_output_files):
            name = of.attrib['fileName']
            file_name = os.path.join(base_dir, name)
            if not os.path.isfile(file_name):  # If not relative to the LEMS file...
                file_name = os.path.join(base_lems_file_path, name)

            # if not os.path.isfile(file_name): # If not relative to the LEMS file...
            #    file_name = os.path.join(os.getcwd(),name)
                # ... try relative to cwd.
            # if not os.path.isfile(file_name): # If not relative to the LEMS file...
            #    file_name = os.path.join(os.getcwd(),'NeuroML2','results',name)
                # ... try relative to cwd in NeuroML2/results subdir.
            if not os.path.isfile(file_name):  # If not relative to the base dir...
                raise OSError(('Could not find simulation output '
                               'file %s' % file_name))
            format = of.attrib['format']
            print_comment("Loading saved events from %s (format: %s)" % (file_name, format),
                          True)
            selections = {}
            for col in of.findall(ns_prefix + 'EventSelection'):
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
                # print_comment("Found a event in cell %s (%s) at t = %s" % (id,selections[id],t))
                events[selections[id]].append(t)

            if remove_dat_files_after_load:
                print_comment_v("Removing file %s after having loading its data!" % file_name)
                os.remove(file_name)

    output_files = sim.findall(ns_prefix + 'OutputFile')
    n_output_files = len(output_files)
    if plot:
        rows = int(max(1, math.ceil(n_output_files / float(3))))
        columns = min(3, n_output_files)
        fig, ax = plt.subplots(rows, columns, sharex=True,
                               figsize=(8 * columns, 4 * rows))
        if n_output_files > 1:
            ax = ax.ravel()

    for i, of in enumerate(output_files):
        traces['t'] = []
        name = of.attrib['fileName']
        file_name = os.path.join(base_dir, name)

        if not os.path.isfile(file_name):  # If not relative to the LEMS file...
            file_name = os.path.join(base_lems_file_path, name)

        if not os.path.isfile(file_name):  # If not relative to the LEMS file...
            file_name = os.path.join(os.getcwd(), name)

            # ... try relative to cwd.
        if not os.path.isfile(file_name):  # If not relative to the LEMS file...
            file_name = os.path.join(os.getcwd(), 'NeuroML2', 'results', name)
            # ... try relative to cwd in NeuroML2/results subdir.
        if not os.path.isfile(file_name):  # If not relative to the LEMS file...
            raise OSError(('Could not find simulation output '
                           'file %s' % file_name))
        t_file_mod = datetime.fromtimestamp(os.path.getmtime(file_name))
        if t_file_mod < t_run:
            raise Exception("Expected output file %s has not been modified since "
                            "%s but the simulation was run later at %s."
                            % (file_name, t_file_mod, t_run))

        print_comment("Loading saved data from %s%s"
                      % (file_name, ' (%s)' % simulator if simulator else ''),
                      verbose)

        cols = []
        cols.append('t')
        for col in of.findall(ns_prefix + 'OutputColumn'):
            quantity = col.attrib['quantity']
            traces[quantity] = []
            cols.append(quantity)

        with open(file_name) as f:
            for line in f:
                values = line.split()
                for vi in range(len(values)):
                    traces[cols[vi]].append(float(values[vi]))

        if remove_dat_files_after_load:
            print_comment_v("Removing file %s after having loading its data!" % file_name)
            os.remove(file_name)

        if plot:
            info = (
                "Data loaded from %s%s"
                % (file_name, ' (%s)' % simulator if simulator else '')
            )
            print_comment_v("Reloading: %s" % info)
            fig.canvas.set_window_title(info)

            legend = False
            for key in cols:
                if n_output_files > 1:
                    ax_ = ax[i]
                else:
                    ax_ = ax
                ax_.set_xlabel('Time (ms)')
                ax_.set_ylabel('(SI units...)')
                ax_.xaxis.grid(True)
                ax_.yaxis.grid(True)

                if key != 't':
                    ax_.plot(traces['t'], traces[key], label=key)
                    print_comment("Adding trace for: %s, from: %s"
                                  % (key, file_name), verbose)
                    ax_.used = True
                    legend = True

                if legend:
                    if n_output_files > 1:
                        ax_.legend(loc='upper right', fancybox=True, shadow=True,
                                   ncol=4)  # ,bbox_to_anchor=(0.5, -0.05))
                    else:
                        ax_.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=4)

    #  print(traces.keys())

    if plot and show_plot_already:
        if n_output_files > 1:
            ax_ = ax
        else:
            ax_ = [ax]
        for axi in ax_:
            if not hasattr(axi, 'used') or not axi.used:
                axi.axis('off')
        plt.tight_layout()
        plt.show()

    if reload_events:
        return traces, events
    else:
        return traces


def get_next_hex_color(my_random=None):
    if my_random is not None:
        return "#%06x" % my_random.randint(0, 0xFFFFFF)
    else:
        return "#%06x" % random.randint(0, 0xFFFFFF)


def confirm_file_exists(filename):
    if not os.path.isfile(filename):
        print_comment_v("Error! Unable to find file: %s!" % filename)
        sys.exit()


def confirm_neuroml_file(filename):
    """Confirm that file exists and is a NeuroML file before proceeding with
    processing.

    :param filename: Names of files to check
    :type filename: str
    """
    # print('Checking file: %s'%filename)
    # Some conditions to check if a LEMS file was entered
    # TODO: Ideally we'd like to check the root node: checking file extensions is brittle
    confirm_file_exists(filename)
    if filename.startswith('LEMS_'):
        print_comment_v(textwrap.dedent(
            """
            *************************************************************************************
            **  Warning, you may be trying to use a LEMS XML file (containing <Simulation> etc.)
            **  for a pyNeuroML option when a NeuroML2 file is required...
            *************************************************************************************
            """
        ))


def confirm_lems_file(filename):
    """Confirm that file exists and is a LEMS file before proceeding with
    processing.

    :param filename: Names of files to check
    :type filename: list of strings
    """
    # print('Checking file: %s'%filename)
    # Some conditions to check if a LEMS file was entered
    # TODO: Ideally we'd like to check the root node: checking file extensions is brittle
    confirm_file_exists(filename)
    if filename.endswith('nml'):
        print_comment_v(textwrap.dedent(

            """
            *************************************************************************************
            **  Warning, you may be trying to use a NeuroML2 file for a pyNeuroML option
            **  when a LEMS XML file (containing <Simulation> etc.) is required...
            *************************************************************************************
            """
        ))


def evaluate_arguments(args):
    #print('    ====  Args: %s'%args)
    global DEFAULTS
    DEFAULTS['v'] = args.verbose

    pre_args = ""
    post_args = ""
    exit_on_fail = True

    # These do not use the shared option where files are supplied
    # They require the file name to be specified after
    # TODO: handle these better
    if args.sbml_import or args.sbml_import_units or args.vhdl:
        if args.sbml_import:
            pre_args = "-sbml-import"
            f = args.sbml_import[0]
            post_args = ' '.join(args.sbml_import[1:])
        elif args.sbml_import_units:
            pre_args = "-smbl-import-units"
            f = args.sbml_import_units[0]
            post_args = ' '.join(args.sbml_import_units[1:])
        elif args.vhdl:
            f = args.vhdl[1]
            confirm_lems_file(f)
            post_args = "-vhdl %s" % args.vhdl[0]

        run_jneuroml(pre_args,
                     f,
                     post_args,
                     max_memory=args.java_max_memory,
                     exit_on_fail=exit_on_fail)
        # No need to go any further
        return True

    # Process bits that process the file list provided as the shared option
    if len(args.input_files) == 0:
        print_comment_v("ERROR: Please specify NeuroML/LEMS files to process")
        return

    for f in args.input_files:
        if args.nogui:
            post_args = "-nogui"

        if args.sedml:
            confirm_lems_file(f)
            post_args = "-sedml"
        elif args.neuron is not None:

            # Note: either a lems file or nml2 file is allowed here...
            confirm_file_exists(f)

            num_neuron_args = len(args.neuron)
            if num_neuron_args < 0 or num_neuron_args > 4:
                print_comment("ERROR: The \'-neuron\' option was given an invalid "
                              "number of arguments: %d given, 0-4 required"
                              % num_neuron_args)
                sys.exit(-1)
            post_args = "-neuron %s" % ' '.join(args.neuron[:-1])
        elif args.svg:
            confirm_neuroml_file(f)
            post_args = "-svg"
        elif args.png:
            confirm_neuroml_file(f)
            post_args = "-png"
        elif args.dlems:
            confirm_lems_file(f)
            post_args = "-dlems"
        elif args.vertex:
            confirm_lems_file(f)
            post_args = "-vertex"
        elif args.xpp:
            confirm_lems_file(f)
            post_args = "-xpp"
        elif args.dnsim:
            confirm_lems_file(f)
            post_args = "-dnsim"
        elif args.brian:
            confirm_lems_file(f)
            post_args = "-brian"
        elif args.sbml:
            confirm_lems_file(f)
            post_args = "-sbml"
        elif args.matlab:
            confirm_lems_file(f)
            post_args = "-matlab"
        elif args.cvode:
            confirm_lems_file(f)
            post_args = "-cvode"
        elif args.nineml:
            confirm_lems_file(f)
            post_args = "-nineml"
        elif args.spineml:
            confirm_lems_file(f)
            post_args = "-spineml"
        elif args.graph:
            confirm_neuroml_file(f)
            from neuromllite.GraphVizHandler import engines
            engine = 'dot'

            # They can use min1 to mean -1
            level = args.graph[0].replace('min', '-')

            # If they only provide a level
            try:
                level = int(level)
                print("Level selected: {}".format(level))
            # If they provide level and engine specs: 1d, 2c
            # Or some wrong value
            except ValueError:
                try:
                    engine = engines[level[-1:]]
                    print("Engine selected: {}".format(engine))
                except KeyError as e:
                    print("Unknown value for engine: {}. Please use one of {}".format(e, engines))
                    sys.exit(-1)

                # if a valid engine was provided, we try the level again
                try:
                    level = int(level[:-1])
                    print("Level selected: {}".format(level))
                except ValueError:
                    print("Incorrect value for level: {}.".format(level[:-1]))
                    sys.exit(-1)

            generate_nmlgraph(f, level, engine)
            sys.exit(0)
        elif args.lems_graph:
            confirm_lems_file(f)
            pre_args = ""
            post_args = "-lems-graph"
            exit_on_fail = True
        elif args.matrix:
            confirm_neuroml_file(f)
            from neuromllite.MatrixHandler import MatrixHandler

            level = int(args.matrix[0])

            print_comment('Converting %s to matrix form, level %i' % (f, level))

            from neuroml.hdf5.NeuroMLXMLParser import NeuroMLXMLParser

            handler = MatrixHandler(level=level, nl_network=None)

            currParser = NeuroMLXMLParser(handler)

            currParser.parse(f)

            handler.finalise_document()

            print_comment("Done with MatrixHandler...")

            exit()
        elif args.validate:
            confirm_neuroml_file(f)
            pre_args = "-validate"
            exit_on_fail = True
        elif args.validatev1:
            confirm_neuroml_file(f)
            pre_args = "-validatev1"
            exit_on_fail = True

        run_jneuroml(pre_args,
                     f,
                     post_args,
                     max_memory=args.java_max_memory,
                     exit_on_fail=exit_on_fail)


def get_path_to_jnml_jar():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    jar_path = os.path.join(
        script_dir, "lib",
        "jNeuroML-%s-jar-with-dependencies.jar" % JNEUROML_VERSION
    )
    return jar_path


def run_jneuroml(pre_args,
                 target_file,
                 post_args,
                 max_memory=DEFAULTS['default_java_max_memory'],
                 exec_in_dir=".",
                 verbose=DEFAULTS['v'],
                 report_jnml_output=True,
                 exit_on_fail=True):

    print_comment('Running jnml on %s with pre args: %s, post args: %s, in dir: %s, verbose: %s, report: %s, exit on fail: %s' %
                  (target_file, pre_args, post_args, exec_in_dir, verbose, report_jnml_output, exit_on_fail), verbose)
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
                                        prefix=' jNeuroML >>  ')

        if not output:
            if exit_on_fail:
                print_comment('Error: execute_command_in_dir returned with output: %s' % output, True)
                sys.exit(-1)
            else:
                return False

        if report_jnml_output:
            print_comment('Successfully ran the following command using pyNeuroML v%s: \n    %s' % (__version__, command), True)
            print_comment('Output:\n\n%s' % output, True)

    #  except KeyboardInterrupt as e:
    #    raise e

    except Exception as e:
        print_comment('*** Execution of jnml has failed! ***', True)
        print_comment('Error:  %s' % e)
        print_comment('*** Command: %s ***' % command, True)
        print_comment('Output: %s' % output, True)
        if exit_on_fail:
            sys.exit(-1)
        else:
            return False
    return True


# TODO: Refactorinng
def run_jneuroml_with_realtime_output(
    pre_args,
    target_file,
    post_args,
    max_memory=DEFAULTS['default_java_max_memory'],
    exec_in_dir=".",
    verbose=DEFAULTS['v'],
    exit_on_fail=True
):
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
        output = execute_command_in_dir_with_realtime_output(
            command, exec_in_dir, verbose=verbose, prefix=' jNeuroML >>  ')

    except KeyboardInterrupt as e:
        raise e
    except:
        print_comment('*** Execution of jnml has failed! ***', True)
        print_comment('*** Command: %s ***' % command, True)
        if exit_on_fail:
            sys.exit(-1)
        else:
            return False
    return True


def print_comment_v(text, end='\n'):
    print_comment(text, True, end)


def print_comment(text, print_it=DEFAULTS['v'], end='\n'):
    prefix = "pyNeuroML >>> "
    if not isinstance(text, str):
        text = text.decode('ascii')
    if print_it:
        print("%s%s" % (prefix, text.replace("\n", "\n" + prefix)), end=end)


def execute_command_in_dir_with_realtime_output(command, directory,
                                                verbose=DEFAULTS['v'],
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
                print_comment(line, end="")
        p.wait()  # wait for the subprocess to exit
    except KeyboardInterrupt as e:
        print_comment_v('*** Command interrupted: \n       %s' % command)
        if p:
            p.kill()
        #  return True
        raise e

    if not p.returncode == 0:
        print_comment_v('*** Problem running command (return code: %s): \n       %s' % (p.returncode, command))

    return p.returncode == 0


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

        return_string = return_string.decode("utf-8")  # For Python 3

        print_comment('Command completed. Output: \n %s%s' %
                      (prefix, return_string.replace('\n', '\n ' + prefix)),
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
        print_comment_v('*** Problem running command: \n       %s' % e)
        print_comment_v('%s%s' % (prefix, e.output.decode().replace('\n', '\n' + prefix)))
        return None
    except:
        print_comment_v('*** Unknown problem running command: %s' % e)
        return None

    print_comment("Finished execution", verbose)


def generate_plot(xvalues,
                  yvalues,
                  title,
                  labels=None,
                  colors=None,
                  linestyles=None,
                  linewidths=None,
                  markers=None,
                  markersizes=None,
                  xaxis=None,
                  yaxis=None,
                  xlim=None,
                  ylim=None,
                  show_xticklabels=True,
                  show_yticklabels=True,
                  grid=False,
                  logx=False,
                  logy=False,
                  font_size=12,
                  bottom_left_spines_only=False,
                  cols_in_legend_box=3,
                  legend_position=None,
                  show_plot_already=True,
                  save_figure_to=None,
                  title_above_plot=False,
                  verbose=False):
    """Utility function to generate plots using the Matplotlib library.

    This function can be used to generate graphs with multiple plot lines.
    For example, to plot two metrics you can use:

    ::

        generate_plot(xvalues=[[ax1, ax2, ax3], [bx1, bx2, bx3]], yvalues=[[ay1, ay2, ay3], [by1, by2, by3]], labels=["metric 1", "metric 2"])

    Please note that while plotting multiple plots, you should take care to
    ensure that the number of x values and y values for each metric correspond.
    These lists are passed directly to Matplotlib for plotting without
    additional sanity checks.

    Please see the Matplotlib documentation for the complete list of available
    styles and colours:
    - https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.plot.html
    - https://matplotlib.org/stable/gallery/index.html

    :param xvalues: X values
    :type xvalues: list of lists
    :param yvalues: Y values
    :type yvalues: lists of lists
    :param title: title of plot
    :type title: str
    :param labels: labels for each plot (default: None)
    :type labels: list of strings
    :param colors: colours for each plot (default: None)
    :type colors: list of strings
    :param linestyles: list of line styles (default: None)
    :type linestyles: list strings
    :param linewidths: list of line widths (default: None)
    :type linewidths: list of floats
    :param markers: list of markers (default: None)
    :type markers: list strings
    :param markersizes: list of marker sizes (default: None)
    :type markersizes: list of floats
    :param xaxis: label of X axis (default: None)
    :type xaxis: str
    :param yaxis: label of Y axis (default: None)
    :type yaxis: str
    :param xlim: left and right extents of x axis (default: None)
    :type xlim: tuple of (float, float) or individual arguments: (left=float), (right=float)
                See https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.xlim.html
    :param ylim: top and bottom extents of y axis (default: None)
    :type ylim: tuple of (float, float) or individual arguments: (top=float), (bottom=float)
                See https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.ylim.html
    :param show_xticklabels: whether labels should be shown on xtics (default: True)
    :type show_xticklabels: boolean
    :param show_yticklabels: whether labels should be shown on ytics (default: True)
    :type show_yticklabels: boolean
    :param grid: enable/disable grid (default: False)
    :type grid: boolean
    :param logx: should the x axis be in log scale (default: False)
    :type logx: boolean
    :param logy: should the y ayis be in log scale (default: False)
    :type logy: boolean
    :param font_size: font size (default: 12)
    :type font_size: float
    :param bottom_left_spines_only: enable/disable spines on right and top (default: False)
                (a spine is line noting the data area boundary)
    :type bottom_left_spines_only: boolean
    :param cols_in_legend_box: number of columns to use in legend box (default: 3)
    :type cols_in_legend_box: float
    :param legend_position: position of legend: (default: None)
                See: https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.legend.html
    :type legend_position: str
    :param show_plot_already: if plot should be shown when created (default: True)
    :type show_plot_already: boolean
    :param save_figure_to: location to save generated figure to (default: None)
    :type save_figure_to: str
    :param title_above_plot: enable/disable title above the plot (default: False)
    :type title_above_plot: boolean
    :param verbose: enable/disable verbose logging (default: False)
    :type verbose: boolean
    """

    print_comment_v("Generating plot: %s" % (title))

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
        markersize = 6 if not markersizes else markersizes[i]

        if colors:
            plt.plot(xvalues[i], yvalues[i], 'o', color=colors[i], marker=marker, markersize=markersize, linestyle=linestyle, linewidth=linewidth, label=label)
        else:
            plt.plot(xvalues[i], yvalues[i], 'o', marker=marker, markersize=markersize, linestyle=linestyle, linewidth=linewidth, label=label)

    if labels:
        if legend_position == 'right':
            box = ax.get_position()
            ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
            # Put a legend to the right of the current axis
            ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        else:
            plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=cols_in_legend_box)

    if xlim:
        plt.xlim(xlim)
    if ylim:
        plt.ylim(ylim)

    if save_figure_to:
        print_comment("Saving image to %s of plot: %s" % (os.path.abspath(save_figure_to), title), verbose)
        plt.savefig(save_figure_to, bbox_inches='tight')
        print_comment_v("Saved image to %s of plot: %s" % (save_figure_to, title))

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

        if 't' not in data.keys():
            data['t'] = []
            for i in range(len(words) - 1):
                data[i] = []
                indeces.append(i)
        data['t'].append(float(words[0]))
        for i in range(len(words) - 1):
            data[i].append(float(words[i + 1]))

    print_comment_v("Loaded data from %s; columns: %s" % (file_name, indeces))

    dat_file.close()
    return data, indeces


def _find_elements(el, name, rdf=False):
    ns = 'http://www.neuroml.org/schema/neuroml2'
    if rdf:
        ns = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
    return el.findall('.//{%s}%s' % (ns, name))


def _get_attr_in_element(el, name, rdf=False):
    ns = 'http://www.neuroml.org/schema/neuroml2'
    if rdf:
        ns = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
    aname = '{%s}%s' % (ns, name)
    return el.attrib[aname] if aname in el.attrib else None


def extract_annotations(nml2_file):
    pp = pprint.PrettyPrinter()
    test_file = open(nml2_file)
    root = etree.parse(test_file).getroot()
    annotations = {}

    for a in _find_elements(root, 'annotation'):
        for r in _find_elements(a, 'Description', rdf=True):
            desc = _get_attr_in_element(r, 'about', rdf=True)
            annotations[desc] = []

            for info in r:
                if isinstance(info.tag, str):
                    kind = info.tag.replace('{http://biomodels.net/biology-qualifiers/}', 'bqbiol:')
                    kind = kind.replace('{http://biomodels.net/model-qualifiers/}', 'bqmodel:')

                    for li in _find_elements(info, 'li', rdf=True):

                        attr = _get_attr_in_element(li, 'resource', rdf=True)
                        if attr:
                            annotations[desc].append({kind: attr})

    print_comment_v("Annotations in %s: " % (nml2_file))
    pp.pprint(annotations)


'''
Work in progress: expand a (simple) ComponentType  and evaluate an instance of it by
giving parameters & required variables
'''


def evaluate_component(comp_type, req_variables={}, parameter_values={}):
    print_comment('Evaluating %s with req:%s; params:%s' % (comp_type.name, req_variables, parameter_values))
    exec_str = ''
    return_vals = {}
    for p in parameter_values:
        exec_str += '%s = %s\n' % (p, get_value_in_si(parameter_values[p]))
    for r in req_variables:
        exec_str += '%s = %s\n' % (r, get_value_in_si(req_variables[r]))
    for c in comp_type.Constant:
        exec_str += '%s = %s\n' % (c.name, get_value_in_si(c.value))
    for d in comp_type.Dynamics:
        for dv in d.DerivedVariable:
            exec_str += '%s = %s\n' % (dv.name, dv.value)
            exec_str += 'return_vals["%s"] = %s\n' % (dv.name, dv.name)
        for cdv in d.ConditionalDerivedVariable:
            for case in cdv.Case:
                if case.condition:
                    cond = case.condition.replace('.neq.', '!=').replace('.eq.', '==').replace('.gt.', '<').replace('.lt.', '<')
                    exec_str += 'if ( %s ): %s = %s \n' % (cond, cdv.name, case. value)
                else:
                    exec_str += 'else: %s = %s \n' % (cdv.name, case.value)

            exec_str += '\n'

            exec_str += 'return_vals["%s"] = %s\n' % (cdv.name, cdv.name)

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
