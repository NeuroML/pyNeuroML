
from pyneuroml import pynml

from pyneuroml.pynml import print_comment_v, print_comment


def convert_to_swc(nml_file_name, swc_file_name):
    
    nml_doc = pynml.read_neuroml2_file(nml_file_name, include_includes=True, verbose=False, optimized=True)
    
    lines = []
    
    for cell in nml_doc.cells:
        
        print_comment_v("Converting cell %s as found in NeuroML doc %s to SWC..."%(cell.id,nml_file_name))
        
        segments = cell.morphology.segments

        distpoints = {}
        proxpoints = {}

        for segment in segments:

            id = int(segment.id)

            distal = segment.distal
            
            x = float(distal.x)
            y = float(distal.y)
            z = float(distal.z)
            r = float(distal.diameter)
            
            lines.append('%s %s %s %s'%(x,y,z,r))
            
        for l in lines:
            print('\t%s'%l)
        

if __name__ == '__main__':
    
    files = {'../../examples/test_data/pyr_4_sym.cell.nml':'../../examples/test_data/tmp/pyr_4_sym.swc', 
             '../../examples/test_data/bask.cell.nml':'../../examples/test_data/tmp/bask.swc'}
    
    for f in files:
        convert_to_swc(f,files[f])