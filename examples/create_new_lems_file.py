'''

Example to create a new LEMS file from scratch for running a NML2 model

'''

from pyneuroml.lems import LEMSSimulation
import os

if __name__ == '__main__':
    
    sim_id = 'HHSim'
    ls = LEMSSimulation(sim_id, 500, 0.05, 'net1')
    ls.include_neuroml2_file('NML2_SingleCompHHCell.nml')
    
    disp0 = 'display0'
    ls.create_display(disp0,"Voltages", "-90", "50")
    
    ls.add_line_to_display(disp0, "v", "hhpop[0]/v", "1mV", "#ffffff")
    
    of0 = 'Volts_file'
    ls.create_output_file(of0, "%s.v.dat"%sim_id)
    ls.add_column_to_output_file(of0, 'v', "hhpop[0]/v")
    
    print("Using information to generate LEMS: ")
    print(ls.lems_info)
    print("\nLEMS: ")
    print(ls.to_xml())
    
    ls.save_to_file()
    assert os.path.isfile('LEMS_%s.xml'%sim_id)