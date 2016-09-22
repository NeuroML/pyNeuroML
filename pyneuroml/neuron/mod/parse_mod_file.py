import neuroml as nml

import sys
import os
import pprint 

import airspeed

from pyneuroml.pynml import print_comment_v

pp = pprint.PrettyPrinter(depth=4)


def check_brackets(line, bracket_depth):
    if len(line)>0:
        bracket_depth0 = bracket_depth
        for c in line:
            if c=='{':
                bracket_depth+=1
            elif c=='}':
                bracket_depth-=1
        if bracket_depth0 !=bracket_depth:
            print_comment_v("       <%s> moved bracket %i -> %i"%(line, bracket_depth0,bracket_depth))
    return bracket_depth

def merge_with_template(info):
    
    templfile = "TEMPLATE.channel.nml"
    if not os.path.isfile(templfile):
        templfile = os.path.join(os.path.dirname(sys.argv[0]), templfile)
    print_comment_v("Merging with template %s"%templfile)
    with open(templfile) as f:
        templ = airspeed.Template(f.read())
    return templ.merge(info)

def generate_neuroml2_for_mod_file(mod_file):

    print_comment_v("Generating NeuroML2 representation for mod file: "+mod_file)
    
    blocks ={}
    info = {}
    lines = [(str(ll.strip())).replace('\t',' ') for ll in open(mod_file)]
    line_num = 0
    while line_num<len(lines):
        l = lines[line_num]
        if len(l)>0:
            print_comment_v(">>> %i > %s"%(line_num,l))
            # @type l str
            if l.startswith('TITLE'):
                blocks['TITLE'] = l[6:].strip()
            if '{' in l:
                block_name = l[:l.index('{')].strip()
                blocks[block_name]=[]
                
                li = l[l.index('{')+1:]
                bracket_depth = check_brackets(li,1)
                while bracket_depth>0:
                    if len(li)>0:
                        blocks[block_name].append(li)
                        print_comment_v("        > %s > %s"%(block_name,li))
                    line_num+=1
                    li = lines[line_num]
                    
                    bracket_depth = check_brackets(li,bracket_depth)
                
                rem = li[:-1].strip()
                if len(rem)>0:
                    blocks[block_name].append(rem)
                
        line_num+=1
        
    for line in blocks['STATE']:
        if ' ' in line or '\t' in line:
            blocks['STATE'].remove(line)
            for s in line.split():
                blocks['STATE'].append(s)
                
    for line in blocks['NEURON']:
        if line.startswith('SUFFIX'):
            info['id'] = line[7:].strip()
        if line.startswith('USEION') and 'WRITE' in line:
            info['species'] = line.split()[1]
            
    gates =[]
    for s in blocks['STATE']:
        gate ={}
        gate['id'] = s
        gate['type'] = '???'
        gate['instances'] = '???'
        gates.append(gate)
            
            
    info['type'] = 'ionChannelHH'
    info['gates'] = gates
            
    info['notes'] = "NeuroML2 file automatically generated from NMODL file: %s"%mod_file

                
    pp.pprint(blocks)
    
    chan_file_name = '%s.channel.nml'%info['id']
    chan_file = open(chan_file_name,'w')
    chan_file.write(merge_with_template(info))
    chan_file.close()
    
    
    

if __name__ == '__main__':
    
    mod_file = sys.argv[1]
    
    generate_neuroml2_for_mod_file(mod_file)


