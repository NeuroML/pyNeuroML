#!/usr/bin/env python
"""
Helper class for generating LEMS xml files for simulations
"""
    
import airspeed
import os.path
import sys

class LEMSSimulation():
    
    TEMPLATE_FILE = "%s/LEMS_TEMPLATE.xml"%(os.path.dirname(__file__))
    
    lems_info = {}
    
    
    def __init__(self, sim_id, duration, dt):
        self.lems_info['sim_id'] = sim_id
        self.lems_info['duration'] = duration
        self.lems_info['dt'] = dt
        self.lems_info['include_files'] = []
        self.lems_info['displays'] = []
        
        
    def include_neuroml2_file(self, nml2_file_name):
        self.lems_info['include_files'].append(nml2_file_name)
        
        
    def create_display(self, id, title, ymin, ymax, timeScale="1ms"):
        disp = {}
        self.lems_info['displays'].append(disp)
        disp['id'] = id
        disp['title'] = title
        disp['ymin'] = ymin
        disp['ymax'] = ymax
        disp['timeScale'] = timeScale
        disp['lines'] = []
        
    def add_line_to_display(self, display_id, line_id, quantity, scale, color, timeScale="1ms"):
        disp = None
        for d in self.lems_info['displays']:
            if d['id'] == display_id:
                disp = d
                
        line = {}
        disp['lines'].append(line)
        line['id'] = line_id
        line['quantity'] = quantity
        line['scale'] = scale
        line['color'] = color
        line['timeScale'] = timeScale
        
    
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
        print("Written LEMS Simulation %s to file: %s"%(self.lems_info['sim_id'], file_name))
        
        

if __name__ == '__main__':
    
    
    ls = LEMSSimulation('mysim', 500, 0.05)
    ls.include_neuroml2_file('../../examples/NML2_SingleCompHHCell.nml')
    
    disp0 = 'display0'
    ls.create_display(disp0,"Voltages", "-90", "50")
    
    ls.add_line_to_display(disp0, "v", "hhpop[0]/v", "1mV", "#ffffff")
    
    print(ls.lems_info)
    print(ls.to_xml())
    
    ls.save_to_file()
    
    