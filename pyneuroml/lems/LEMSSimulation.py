#!/usr/bin/env python
"""
Helper class for generating LEMS xml files for simulations
"""
    
import airspeed
import os.path

from pyneuroml import __version__ as pynml_ver
from neuroml import __version__ as libnml_ver
from pyneuroml.pynml import read_neuroml2_file
from pyneuroml.pynml import read_lems_file
from pyneuroml.pynml import print_comment
from pyneuroml.pynml import print_comment_v
from pyneuroml.pynml import get_next_hex_color

class LEMSSimulation():
    
    TEMPLATE_FILE = "%s/LEMS_TEMPLATE.xml"%(os.path.dirname(__file__))
    
    lems_info = {}
    
    
    def __init__(self, 
                 sim_id, 
                 duration, 
                 dt, 
                 target=None, \
                 comment="\n\n        This LEMS file has been automatically generated using PyNeuroML v%s (libNeuroML v%s)\n\n    "%(pynml_ver, libnml_ver),
                 lems_seed = 12345):
                     
        
        self.lems_info['sim_id'] = sim_id
        self.lems_info['duration'] = duration
        self.lems_info['dt'] = dt
        self.lems_info['comment'] = comment
        self.lems_info['seed'] = lems_seed
        self.lems_info['report'] = ''
        
        self.lems_info['include_files'] = []
        self.lems_info['displays'] = []
        self.lems_info['output_files'] = []
        self.lems_info['event_output_files'] = []
        
        if target:
            self.lems_info['target'] = target
            
            
    def __setattr__(self, attr, value):
        if attr in self.lems_info.keys():
            self.lems_info[attr] = value
        else:
            raise Exception("There is not a field: %s in LEMSSimulation"%attr)
        
        
    def assign_simulation_target(self, target):
        self.lems_info['target'] = target
        
        
    def set_report_file(self, report_file_name):
        '''
        short file saved after simulation with run time, simulator version etc.
        '''
        if report_file_name != None:
            self.lems_info['report'] = ' reportFile="%s"'%report_file_name
        
        
    def include_neuroml2_file(self, nml2_file_name, include_included=True, relative_to_dir='.'):
        full_path = os.path.abspath(relative_to_dir+'/'+nml2_file_name)
        base_path = os.path.dirname(full_path)
        #print_comment_v("Including in generated LEMS file: %s (%s)"%(nml2_file_name, full_path))
        if not nml2_file_name in self.lems_info['include_files']:
            self.lems_info['include_files'].append(nml2_file_name)
            
        if include_included:
            cell = read_neuroml2_file(full_path)
            for include in cell.includes:
                self.include_neuroml2_file(include.href, include_included=True, relative_to_dir=base_path)
        
        
    def include_lems_file(self, lems_file_name, include_included=True):
        if not lems_file_name in self.lems_info['include_files']:
            self.lems_info['include_files'].append(lems_file_name)
            
        if include_included:
            model = read_lems_file(lems_file_name)
            for inc in model.included_files:
                self.lems_info['include_files'].append(inc)
        
        
    def create_display(self, id, title, ymin, ymax, timeScale="1ms"):
        disp = {}
        self.lems_info['displays'].append(disp)
        disp['id'] = id
        disp['title'] = title
        disp['ymin'] = ymin
        disp['ymax'] = ymax
        disp['time_scale'] = timeScale
        disp['lines'] = []
        
        
    def create_output_file(self, id, file_name):
        of = {}
        self.lems_info['output_files'].append(of)
        of['id'] = id
        of['file_name'] = file_name
        of['columns'] = []
        
    def create_event_output_file(self, id, file_name,format='ID_TIME'):
        eof = {}
        self.lems_info['event_output_files'].append(eof)
        eof['id'] = id
        eof['file_name'] = file_name
        eof['format'] = format
        eof['selections'] = []
        
        
    def add_line_to_display(self, display_id, line_id, quantity, scale=1, color=None, timeScale="1ms"):
        disp = None
        for d in self.lems_info['displays']:
            if d['id'] == display_id:
                disp = d
                
        line = {}
        disp['lines'].append(line)
        line['id'] = line_id
        line['quantity'] = quantity
        line['scale'] = scale
        line['color'] = color if color else get_next_hex_color()
        line['time_scale'] = timeScale
        
        
    def add_column_to_output_file(self, output_file_id, column_id, quantity):
        of = None
        for o in self.lems_info['output_files']:
            if o['id'] == output_file_id:
                of = o
                
        column = {}
        of['columns'].append(column)
        column['id'] = column_id
        column['quantity'] = quantity
        
    def add_selection_to_event_output_file(self, event_output_file_id, event_id, select, event_port):
        eof = None
        for o in self.lems_info['event_output_files']:
            if o['id'] == event_output_file_id:
                eof = o
                
        selection = {}
        eof['selections'].append(selection)
        selection['id'] = event_id
        selection['select'] = select
        selection['event_port'] = event_port
        
    
    def to_xml(self):
        templfile = self.TEMPLATE_FILE
        if not os.path.isfile(templfile):
            templfile = '.' + templfile
        with open(templfile) as f:
            templ = airspeed.Template(f.read())
        return templ.merge(self.lems_info)
    

    def save_to_file(self, file_name=None):
        if file_name==None:
            file_name = "LEMS_%s.xml"%self.lems_info['sim_id']
            
        lems_file = open(file_name, 'w')
        lems_file.write(self.to_xml())
        lems_file.close()
        print_comment("Written LEMS Simulation %s to file: %s"%(self.lems_info['sim_id'], file_name), True)
        
        return file_name
        
        
# main method example moved to examples/create_new_lems_file.py