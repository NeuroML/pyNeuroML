from neuron import *
from nrn import *
    
def replace_brackets(ref):
    return ref.replace('[', '_').replace(']', '')

def get_cell_name(nrn_section_name, cell_index=0):
    print("Getting cell name for %s"%nrn_section_name)
    if '.' not in nrn_section_name:
        return 'Cell%i'%cell_index
    else:
        return replace_brackets(nrn_section_name.split('.')[0])

def get_segment_group_name(nrn_section_name):
    print("Getting segment group name for %s"%nrn_section_name)
    if isinstance(nrn_section_name, hoc.HocObject):
        nrn_section_name = nrn_section_name.name
    if '.' not in nrn_section_name:
        return replace_brackets(nrn_section_name)
    else:
        return replace_brackets(nrn_section_name.split('.')[1])
    
    

if __name__ == '__main__':
    
    tests = ['Soma', 'dend[2]', 'Mitral[1].secden[8]']
    
    for test in tests:
        print("Orig: %s; cell name: %s, segment group name: %s"%(test, get_cell_name(test), get_segment_group_name(test)))