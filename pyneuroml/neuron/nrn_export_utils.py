from neuron import *
from nrn import *

def clear_neuron():
    print(' - Clearing NEURON contents...')
    h('forall delete_section()')
    print(' - Cleared NEURON contents...')
    h('topology()')
    
def replace_brackets(ref):
    return ref.replace('[', '_').replace(']', '')

def get_cell_name(nrn_section_name, cell_index=0):
    #print("Getting cell name for %s"%nrn_section_name)
    if '.' not in nrn_section_name:
        return 'Cell%i'%cell_index
    else:
        return '%s_%i'%(replace_brackets(nrn_section_name.split('.')[0]),cell_index)
    

def get_cell_file_dir(network_file_name):
    if not '/' in network_file_name:
        return '.'
    return network_file_name[:network_file_name.rfind('/')]
    

def get_segment_group_name(nrn_section_name):
    #print("Getting segment group name for %s"%nrn_section_name)
    if '.' not in nrn_section_name:
        return replace_brackets(nrn_section_name)
    else:
        return replace_brackets(nrn_section_name.split('.')[1])
    
mechs_vs_erevs = {}

def set_erev_for_mechanism(mech, erev):
    mechs_vs_erevs[mech] = erev
    print(">> mechs_vs_erevs: %s"%mechs_vs_erevs)
    
def get_erev_for_mechanism(mech):
    
    print(">> mechs_vs_erevs: %s"%mechs_vs_erevs)
    return mechs_vs_erevs[mech]
    

if __name__ == '__main__':
    
    tests = ['Soma', 'dend[2]', 'Mitral[1].secden[8]']
    
    for test in tests:
        print("Orig: %s; cell name: %s, segment group name: %s"%(test, get_cell_name(test), get_segment_group_name(test)))