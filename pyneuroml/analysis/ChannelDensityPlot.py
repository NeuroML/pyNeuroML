#!/usr/bin/env python
#
#   A script which can be used to generate graphical representation of
#   ion channel densities in NeuroML2 cells
#

from pyneuroml.pynml import print_comment, get_value_in_si,\
                            print_comment_v, read_neuroml2_file
                            
from pyneuroml.analysis.NML2ChannelAnalysis import get_ion_color

from neuroml import Cell, Cell2CaPools

import os
import math

import pprint; pp = pprint.PrettyPrinter(depth=6)

height=18
spacing=2
width_o=18
order = 8
width=width_o*order
start = -2
stop = start+order

substitute_ion_channel_names = {'LeakConductance':'Pas'}

def get_ion_color(ion):
    col =[]
    if ion.lower() == "na": 
        col=[30, 144, 255]
    elif ion.lower() == "k": 
        col=[205,	92,	92]
    elif ion.lower() == "ca": 
        col=[143,	188,	143]
    elif ion.lower() == "h": 
        col=[255, 217, 179]
    else:
        col=[169,	169,	169]
            
    return col
    
    
def _get_rect(ion_channel, row, max_, min_, r, g, b, extras=False):
    
    if max_== 0: return ''
    
    sb = ''
    
    lmin = max(math.log10(min_),start)
    lmax = min(math.log10(max_),stop)
    xmin = width*(lmin-start)/order
    xmax = width*(lmax-start)/order
    
    offset = (height+spacing)*row
    
    sb+="\n<!-- %s %s: %s -> %s (%s -> %s)-->\n"%(row, ion_channel, min_,max_, lmin,lmax)
    sb+="<rect y=\""+str(offset)+"\" width=\""+str(width)+"\" height=\""+str(height)+"\" style=\"fill:rgb("+str(r)+","+str(g)+","+str(b)+");stroke-width:0;stroke:rgb(10,10,10)\"/>\n"
    
    text = "%s: "%(ion_channel if ion_channel not in substitute_ion_channel_names else substitute_ion_channel_names[ion_channel])
        
    for i in range(order):
        x=width_o*i
        sb+="<line x1=\""+str(x)+"\" y1=\""+str(offset)+"\" x2=\""+str(x)+"\" y2=\""+str(height+offset)+"\" style=\"stroke:rgb(100,100,100);stroke-width:0.5\" />\n"
        
    if(max_==min_):

        sb+="<circle cx=\""+str(xmin)+"\" cy=\""+str(offset+(height/2))+"\" r=\"2\" style=\"stroke:yellow;fill:yellow;stroke-width:2\" />\n"
        text+=" %s S/m^2"%format_float(min_)

    else:

        sb+="<line x1=\""+str(xmin)+"\" y1=\""+str(offset+(height/2))+"\" x2=\""+str(xmax)+"\" y2=\""+str(offset+(height/2))+"\" style=\"stroke:black;stroke-width:1\" />\n"
        sb+="<circle cx=\""+str(xmin)+"\" cy=\""+str(offset+(height/2))+"\" r=\"2\" style=\"stroke:yellow;fill:yellow;stroke-width:2\" />\n"
        sb+="<circle cx=\""+str(xmax)+"\" cy=\""+str(offset+(height/2))+"\" r=\"2\" style=\"stroke:red;fill:red;stroke-width:2\" />\n"
        text+=" %s->%s S/m^2"%(format_float(min_),format_float(max_))

    if extras:
        sb+='<text x="%s" y="%s" fill="black" font-family="Arial" font-size="12">%s</text>\n'%(width+3, offset+height-3, text)
    
    return sb

def format_float(dens):
    if dens == 0: return 0
    if int(dens)==dens: return '%i'%dens
    if dens<1e-4: return '%f'%dens
    ff = '%.4f'%(dens)
    if '.'in ff: ff = ff.rstrip('0')
    return ff

def generate_channel_density_plots(nml2_file, text_densities=False, passives_erevs=False, target_directory=None):
    
    nml_doc = read_neuroml2_file(nml2_file, include_includes=True, verbose=False, optimized=True)
    
    cell_elements = []
    cell_elements.extend(nml_doc.cells)
    cell_elements.extend(nml_doc.cell2_ca_poolses)
    svg_files = []
    all_info = {}
    
    for cell in cell_elements:
        info = {}
        all_info[cell.id] = info
        print_comment_v("Extracting channel density info from %s"%cell.id)
        sb = ''
        ions = {}
        maxes = {}
        mins = {}
        row = 0
        na_ions = []
        k_ions = []
        ca_ions = []
        other_ions = []
        
        if isinstance(cell, Cell2CaPools):
            cds = cell.biophysical_properties2_ca_pools.membrane_properties2_ca_pools.channel_densities + \
                cell.biophysical_properties2_ca_pools.membrane_properties2_ca_pools.channel_density_nernsts
        elif isinstance(cell, Cell):
            cds = cell.biophysical_properties.membrane_properties.channel_densities + \
                cell.biophysical_properties.membrane_properties.channel_density_nernsts
              
        epas = None
        ena = None
        ek = None
        eh = None
        eca = None
              
        for cd in cds:
            dens_si = get_value_in_si(cd.cond_density)
            print_comment_v("cd: %s, ion_channel: %s, ion: %s, density: %s (SI: %s)"%(cd.id,cd.ion_channel,cd.ion,cd.cond_density,dens_si))
            
            ions[cd.ion_channel] = cd.ion
            erev_V = get_value_in_si(cd.erev) if hasattr(cd,'erev') else None
            erev = '%s mV'%format_float(erev_V*1000) if hasattr(cd,'erev') else None
            
            if cd.ion == 'na':
                if not cd.ion_channel in na_ions: na_ions.append(cd.ion_channel)
                ena = erev
                info['ena']=erev_V
            elif cd.ion == 'k':
                if not cd.ion_channel in k_ions: k_ions.append(cd.ion_channel)
                ek = erev
                info['ek']=erev_V
            elif cd.ion == 'ca':
                if not cd.ion_channel in ca_ions: ca_ions.append(cd.ion_channel)
                eca = erev
                info['eca']=erev_V
            else:
                if not cd.ion_channel in other_ions: other_ions.append(cd.ion_channel)
                if cd.ion == 'non_specific':
                    epas = erev
                    info['epas']=erev_V
                if cd.ion == 'h':
                    eh = erev
                    info['eh']=erev_V
            
            if cd.ion_channel in maxes:
                if dens_si>maxes[cd.ion_channel]: maxes[cd.ion_channel]=dens_si
            else: 
                maxes[cd.ion_channel]=dens_si
            if cd.ion_channel in mins:
                if dens_si<mins[cd.ion_channel]: mins[cd.ion_channel]=dens_si
            else: 
                mins[cd.ion_channel]=dens_si
                
        for ion_channel in na_ions + k_ions + ca_ions + other_ions:
            col = get_ion_color(ions[ion_channel])
            info[ion_channel]={'max':maxes[ion_channel],'min':mins[ion_channel]}
            
            if maxes[ion_channel]>0:
                sb+=_get_rect(ion_channel, row, maxes[ion_channel],mins[ion_channel],col[0],col[1],col[2],text_densities)
                row+=1
            
        if passives_erevs:
            
            if ena:
                sb+=add_text(row, "E Na = %s "%ena)
                row+=1
            if ek:
                sb+=add_text(row, "E K = %s "%ek)
                row+=1
            if eca:
                sb+=add_text(row, "E Ca = %s"%eca)
                row+=1
            if eh:
                sb+=add_text(row, "E H = %s"%eh)
                row+=1
            if epas:
                sb+=add_text(row, "E pas = %s"%epas)
                row+=1
                
            for sc in cell.biophysical_properties.membrane_properties.specific_capacitances:
                sb+=add_text(row, "C (%s) = %s"%(sc.segment_groups, sc.value))
                
                info['specific_capacitance_%s'%sc.segment_groups]=get_value_in_si(sc.value)
                row+=1
                
                
            #sb+='<text x="%s" y="%s" fill="black" font-family="Arial">%s</text>\n'%(width/3., (height+spacing)*(row+1), text)
        
            
        sb="<?xml version='1.0' encoding='UTF-8'?>\n<svg xmlns=\"http://www.w3.org/2000/svg\" width=\""+str(width+text_densities*200)+"\" height=\""+str((height+spacing)*row)+"\">\n"+sb+"</svg>\n"

        print(sb)
        svg_file = nml2_file+"_channeldens.svg"
        if target_directory:
            svg_file = target_directory+"/"+svg_file.split('/')[-1]
        svg_files.append(svg_file)
        sf = open(svg_file,'w')
        sf.write(sb)
        sf.close()
        print_comment_v("Written to %s"%os.path.abspath(svg_file))
        
        pp.pprint(all_info)
        
    return svg_files, all_info
    
def add_text(row, text):
    return '<text x="%s" y="%s" fill="black" font-family="Arial" font-size="12">%s</text>\n'%(width/3., (height+spacing)*(row+.5), text)
    

if __name__ == '__main__':
    
    generate_channel_density_plots('../../examples/test_data/HHCellNetwork.net.nml', True, True)
    generate_channel_density_plots('../../../neuroConstruct/osb/showcase/BlueBrainProjectShowcase/NMC/NeuroML2/cADpyr229_L23_PC_5ecbf9b163_0_0.cell.nml', True, True)