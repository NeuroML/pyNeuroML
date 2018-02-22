#
#   A file for converting NeuroML 2 files (including cells & network structure)
#   into POVRay files for 3D rendering
#
#   Author: Padraig Gleeson & Matteo Farinella
#
#   This file has been developed as part of the neuroConstruct project
#   This work has been funded by the Medical Research Council and Wellcome Trust
#
#
 
import random

import argparse

import neuroml
from pyneuroml import pynml

from pyneuroml.pynml import print_comment_v, print_comment

_WHITE = "<1,1,1,0.55>"
_BLACK = "<0,0,0,0.55>"
_GREY = "<0.85,0.85,0.85,0.55>"

_DUMMY_CELL = 'DUMMY_CELL'

def process_args():
    """ 
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="A file for converting NeuroML v2 files into POVRay files for 3D rendering")

    parser.add_argument('neuroml_file', type=str, metavar='<NeuroML file>', 
                        help='NeuroML (version 2 beta 3+) file to be converted to PovRay format (XML or HDF5 format)')
                        
    parser.add_argument('-split',
                        action='store_true',
                        default=False,
                        help="If this is specified, generate separate pov files for cells & network. Default is false")


    parser.add_argument('-background', 
                        type=str,
                        metavar='<background colour>',
                        default=_WHITE,
                        help='Colour of background, e.g. <0,0,0,0.55>')

    parser.add_argument('-movie',
                        action='store_true',
                        default=False,
                        help="If this is specified, generate a ini file for generating a sequence of frames for a movie of the 3D structure")
                        
    parser.add_argument('-inputs',
                        action='store_true',
                        default=False,
                        help="If this is specified, show the locations of (synaptic, current clamp, etc.) inputs into the cells of the network")
                        
    parser.add_argument('-conns',
                        action='store_true',
                        default=False,
                        help="If this is specified, show the connections present in the network with lines")
                        
    parser.add_argument('-conn_points',
                        action='store_true',
                        default=False,
                        help="If this is specified, show the end points of the connections present in the network")
                        
    parser.add_argument('-v',
                        action='store_true',
                        default=False,
                        help="Verbose output")

    parser.add_argument('-frames', 
                        type=int,
                        metavar='<frames>',
                        default=36,
                        help='Number of frames in movie')
                        
    parser.add_argument('-posx', 
                        type=float,
                        metavar='<position offset x>',
                        default=0,
                        help='Offset position in x dir (0 is centre, 1 is top)')
    parser.add_argument('-posy', 
                        type=float,
                        metavar='<position offset y>',
                        default=0,
                        help='Offset position in y dir (0 is centre, 1 is top)')
    parser.add_argument('-posz', 
                        type=float,
                        metavar='<position offset z>',
                        default=0,
                        help='Offset position in z dir (0 is centre, 1 is top)')
                        
    parser.add_argument('-viewx', 
                        type=float,
                        metavar='<view offset x>',
                        default=0,
                        help='Offset viewing point in x dir (0 is centre, 1 is top)')
    parser.add_argument('-viewy', 
                        type=float,
                        metavar='<view offset y>',
                        default=0,
                        help='Offset viewing point in y dir (0 is centre, 1 is top)')
    parser.add_argument('-viewz', 
                        type=float,
                        metavar='<view offset z>',
                        default=0,
                        help='Offset viewing point in z dir (0 is centre, 1 is top)')

    parser.add_argument('-scalex', 
                        type=float,
                        metavar='<scale position x>',
                        default=1,
                        help='Scale position from network in x dir')
    parser.add_argument('-scaley', 
                        type=float,
                        metavar='<scale position y>',
                        default=1.5,
                        help='Scale position from network in y dir')
    parser.add_argument('-scalez', 
                        type=float,
                        metavar='<scale position z>',
                        default=1,
                        help='Scale position from network in z dir')

    parser.add_argument('-mindiam', 
                        type=float,
                        metavar='<minimum diameter dendrites/axons>',
                        default=0,
                        help='Minimum diameter for dendrites/axons (to improve visualisations)')

    parser.add_argument('-plane',
                        action='store_true',
                        default=False,
                        help="If this is specified, add a 2D plane below cell/network")

    parser.add_argument('-segids',
                        action='store_true',
                        default=False,
                        help="Show segment ids")
    
    return parser.parse_args()


def define_dummy_cell(pop_id, radius, pov_file):
    dummy_cell_name = '%s_%s'%(_DUMMY_CELL,pop_id)
    pov_file.write('''\n/*\n  Defining a dummy cell to use for population %s with radius %s...\n*/\n#declare %s = 
union {
    sphere {
        <0.000000, 0.000000, 0.000000>, %s 
    }
    pigment { color rgb <1,0,0> }
}\n'''%(pop_id, radius, dummy_cell_name, radius))

    return dummy_cell_name

def main ():

    args = process_args()
        
    xmlfile = args.neuroml_file

    pov_file_name = xmlfile
    endings = [".xml",".h5",".nml"]
    for e in endings:
        if pov_file_name.endswith(e):
            pov_file_name.replace(e, ".pov")
            
    if pov_file_name == xmlfile:
        pov_file_name+='.pov'

    pov_file = open(pov_file_name, "w")


    header='''
/*
POV-Ray file generated from NeuroML network
*/
#version 3.6;

#include "colors.inc"

background {rgbt %s}


    \n''' ###    end of header


    pov_file.write(header%(args.background))

    cells_file = pov_file
    net_file = pov_file
    splitOut = False

    cf = pov_file_name.replace(".pov", "_cells.inc")
    nf = pov_file_name.replace(".pov", "_net.inc")

    if args.split:
        splitOut = True
        cells_file = open(cf, "w")
        net_file = open(nf, "w")
        print_comment_v("Saving into %s and %s and %s"%(pov_file_name, cf, nf))

    print_comment_v("Converting XML file: %s to %s"%(xmlfile, pov_file_name))


    nml_doc = pynml.read_neuroml2_file(xmlfile, include_includes=True, verbose=args.v, optimized=True)

    cell_elements = []
    cell_elements.extend(nml_doc.cells)
    cell_elements.extend(nml_doc.cell2_ca_poolses)
    
    
    minXc = 1e9
    minYc = 1e9
    minZc = 1e9
    maxXc = -1e9
    maxYc = -1e9
    maxZc = -1e9

    minX = 1e9
    minY = 1e9
    minZ = 1e9
    maxX = -1e9
    maxY = -1e9
    maxZ = -1e9

    declaredcells = {}

    print_comment_v("There are %i cells in the file"%len(cell_elements))
    
    cell_id_vs_seg_id_vs_proximal = {}
    cell_id_vs_seg_id_vs_distal = {}
    cell_id_vs_cell = {}

    for cell in cell_elements:
        
        cellName = cell.id 
        cell_id_vs_cell[cell.id] = cell
        print_comment_v("Handling cell: %s"%cellName)
        cell_id_vs_seg_id_vs_proximal[cell.id] = {}
        cell_id_vs_seg_id_vs_distal[cell.id] = {}
        
        declaredcell = "cell_"+cellName

        declaredcells[cellName] = declaredcell

        cells_file.write("#declare %s = \n"%declaredcell)
        cells_file.write("union {\n")

        prefix = ""


        segments = cell.morphology.segments

        distpoints = {}
        proxpoints = {}

        for segment in segments:

            id = int(segment.id)

            distal = segment.distal

            x = float(distal.x)
            y = float(distal.y)
            z = float(distal.z)
            r = max(float(distal.diameter)/2.0, args.mindiam)

            if x-r<minXc: minXc=x-r
            if y-r<minYc: minYc=y-r
            if z-r<minZc: minZc=z-r

            if x+r>maxXc: maxXc=x+r
            if y+r>maxYc: maxYc=y+r
            if z+r>maxZc: maxZc=z+r

            distalpoint = "<%f, %f, %f>, %f "%(x,y,z,r)

            distpoints[id] = distalpoint
            cell_id_vs_seg_id_vs_distal[cell.id][id] = (x,y,z)

            proximalpoint = ""
            if segment.proximal is not None:
                proximal = segment.proximal
                proximalpoint = "<%f, %f, %f>, %f "%(float(proximal.x),float(proximal.y),float(proximal.z),max(float(proximal.diameter)/2.0, args.mindiam))
                
                cell_id_vs_seg_id_vs_proximal[cell.id][id] = (float(proximal.x),float(proximal.y),float(proximal.z))
            else:
                parent = int(segment.parent.segments)
                proximalpoint = distpoints[parent]
                cell_id_vs_seg_id_vs_proximal[cell.id][id] = cell_id_vs_seg_id_vs_distal[cell.id][parent]
                
            
            proxpoints[id] = proximalpoint

            shape = "cone"
            if proximalpoint == distalpoint:
                shape = "sphere"
                proximalpoint = ""
                
            if ( shape == "cone" and (proximalpoint.split('>')[0] == distalpoint.split('>')[0])):
                comment = "Ignoring zero length segment (id = %i): %s -> %s\n"%(id, proximalpoint, distalpoint)
                print_comment_v(comment)
                cells_file.write("    // "+comment)
                
            else:
                cells_file.write("    %s {\n"%shape)
                cells_file.write("        %s\n"%distalpoint)
                if len(proximalpoint): cells_file.write("        %s\n"%proximalpoint)
                cells_file.write("        //%s_%s.%s\n"%('CELL_GROUP_NAME','0', id))
                cells_file.write("    }\n")
                

            if args.segids:
                cells_file.write('    text {\n')
                cells_file.write('        ttf "timrom.ttf" "------- Segment: %s" .1, 0.01\n'%(segment.id))
                cells_file.write('        pigment { Red }\n')
                cells_file.write('        rotate <0,180,0>\n')
                cells_file.write('        scale <10,10,10>')
                cells_file.write('        translate %s>\n'%distalpoint.split('>')[0])
                cells_file.write('    }\n')

        cells_file.write("    pigment { color rgb <%f,%f,%f> }\n"%(random.random(),random.random(),random.random()))

        cells_file.write("}\n\n")
        


    if splitOut:
        pov_file.write("#include \""+cf+"\"\n\n")
        pov_file.write("#include \""+nf+"\"\n\n")
        
    pov_file.write('''\n/*\n  Defining a dummy cell to use when cell in population is not found in NeuroML file...\n*/\n#declare %s = 
union {
    sphere {
        <0.000000, 0.000000, 0.000000>, 5.000000 
    }
    pigment { color rgb <1,0,0> }
}\n'''%_DUMMY_CELL)
        
    pov_file.write('''\n/*\n  Defining the spheres to use for end points of connections...\n*/
    \n#declare conn_start_point = 
union {
    sphere {
        <0.000000, 0.000000, 0.000000>, 3.000000 
    }
    pigment { color rgb <0,1,0> }
}\n
\n#declare conn_end_point = 
union {
    sphere {
        <0.000000, 0.000000, 0.000000>, 3.000000 
    }
    pigment { color rgb <1,0,0> }
}\n
\n#declare input_object = 
union {
    cone {
        <0, 0, 0>, 0.1    // Center and radius of one end
        <0, -40, 0>, 2.5    // Center and radius of other end
    }
    pigment { color rgb <0.2,0.2,0.8> }
}\n''')


    positions = {}
    popElements = nml_doc.networks[0].populations
    
    pop_id_vs_cell = {}

    print_comment_v("There are %i populations in the file"%len(popElements))

    for pop in popElements:
        
        name = pop.id
        celltype = pop.component
        instances = pop.instances
        
        if pop.component in cell_id_vs_cell.keys():
            pop_id_vs_cell[pop.id] = cell_id_vs_cell[pop.component]

        info = "Population: %s has %i positioned cells of type: %s"%(name,len(instances),celltype)
        print_comment_v(info)

        colour = "1"
        substitute_radius = None
        
        for prop in pop.properties:

            if prop.tag == 'color':
                colour = prop.value
                colour = colour.replace(" ", ",")
                #print "Colour determined to be: "+colour
            if prop.tag == 'radius':
                substitute_radius = float(prop.value)
        
        net_file.write("\n\n/* "+info+" */\n\n")

        pop_positions = {}
        
        if not celltype in declaredcells:
            minXc = 0
            minYc = 0
            minZc = 0
            maxXc = 0
            maxYc = 0
            maxZc = 0
            if substitute_radius:
                dummy_cell_name = define_dummy_cell(name, substitute_radius, pov_file)
                cell_definition = dummy_cell_name
            else:
                cell_definition = _DUMMY_CELL  
        else:
            cell_definition = declaredcells[celltype]
        
        for instance in instances:

            location = instance.location
            id = int(instance.id)
            net_file.write("object {\n")
            net_file.write("    %s\n"%cell_definition)
            x = float(location.x)
            y = float(location.y)
            z = float(location.z)
            pop_positions[id] = (x,y,z)

            if x+minXc<minX: minX=x+minXc
            if y+minYc<minY: minY=y+minYc
            if z+minZc<minZ: minZ=z+minZc

            if x+maxXc>maxX: maxX=x+maxXc
            if y+maxYc>maxY: maxY=y+maxYc
            if z+maxZc>maxZ: maxZ=z+maxZc

            net_file.write("    translate <%s, %s, %s>\n"%(x,y,z))

            if colour == '1':
                colour = "%f,%f,%f"%(random.random(),random.random(),random.random())

            if colour is not None:
                net_file.write("    pigment { color rgb <%s> }"%(colour))

            net_file.write("\n    //%s_%s\n"%(name, id)) 

            net_file.write("}\n")
        
        positions[name] = pop_positions
            
        if len(instances) == 0 and int(pop.size>0):
            
            info = "Population: %s has %i unpositioned cells of type: %s"%(name,pop.size,celltype)
            print_comment_v(info)

            colour = "1"
            '''
            if pop.annotation:
                print dir(pop.annotation)
                print pop.annotation.anytypeobjs_
                print pop.annotation.member_data_items_[0].name
                print dir(pop.annotation.member_data_items_[0])
                for prop in pop.annotation.anytypeobjs_:
                    print prop

                    if len(prop.getElementsByTagName('meta:tag'))>0 and prop.getElementsByTagName('meta:tag')[0].childNodes[0].data == 'color':
                        #print prop.getElementsByTagName('meta:tag')[0].childNodes
                        colour = prop.getElementsByTagName('meta:value')[0].childNodes[0].data
                        colour = colour.replace(" ", ",")
                    elif prop.hasAttribute('tag') and prop.getAttribute('tag') == 'color':
                        colour = prop.getAttribute('value')
                        colour = colour.replace(" ", ",")
                    print "Colour determined to be: "+colour
            '''

            net_file.write("\n\n/* "+info+" */\n\n")


            net_file.write("object {\n")
            net_file.write("    %s\n"%cell_definition)
            x = 0
            y = 0
            z = 0

            if x+minXc<minX: minX=x+minXc
            if y+minYc<minY: minY=y+minYc
            if z+minZc<minZ: minZ=z+minZc

            if x+maxXc>maxX: maxX=x+maxXc
            if y+maxYc>maxY: maxY=y+maxYc
            if z+maxZc>maxZ: maxZ=z+maxZc

            net_file.write("    translate <%s, %s, %s>\n"%(x,y,z))

            if colour == '1':
                colour = "%f,%f,%f"%(random.random(),random.random(),random.random())

            if colour is not None:
                net_file.write("    pigment { color rgb <%s> }"%(colour))

            net_file.write("\n    //%s_%s\n"%(name, id)) 

            net_file.write("}\n")
            
            
    if args.conns or args.conn_points: 
    
        projections = nml_doc.networks[0].projections + nml_doc.networks[0].electrical_projections + nml_doc.networks[0].continuous_projections
        for projection in projections:
            pre = projection.presynaptic_population
            post = projection.postsynaptic_population
            
            if isinstance(projection, neuroml.Projection):
                connections = []
                for c in projection.connection_wds: connections.append(c) 
                for c in projection.connections: connections.append(c) 
                color='Grey'
            elif isinstance(projection, neuroml.ElectricalProjection):
                connections = projection.electrical_connections + projection.electrical_connection_instances + projection.electrical_connection_instance_ws
                color='Yellow'
            elif isinstance(projection, neuroml.ContinuousProjection):
                connections = projection.continuous_connections + projection.continuous_connection_instances + projection.continuous_connection_instance_ws
                color='Blue'
                
            print_comment_v("Adding %i connections for %s: %s -> %s "%(len(connections),projection.id,pre,post))
            #print cell_id_vs_seg_id_vs_distal
            #print cell_id_vs_seg_id_vs_proximal
            for connection in connections:
                pre_cell_id = connection.get_pre_cell_id()
                post_cell_id = connection.get_post_cell_id()
                
                pre_loc = (0,0,0) 
                if pre in positions.keys(): 
                    if len(positions[pre])>0:
                        pre_loc = positions[pre][pre_cell_id] 
                post_loc = (0,0,0)
                if post in positions.keys():
                    post_loc = positions[post][post_cell_id] 
                    
                if projection.presynaptic_population in pop_id_vs_cell.keys():
                    pre_cell = pop_id_vs_cell[projection.presynaptic_population]
                    d = cell_id_vs_seg_id_vs_distal[pre_cell.id][connection.get_pre_segment_id()]
                    p = cell_id_vs_seg_id_vs_proximal[pre_cell.id][connection.get_pre_segment_id()]
                    m = [ p[i]+connection.get_pre_fraction_along()*(d[i]-p[i]) for i in [0,1,2] ]
                    print_comment("Pre point is %s, %s between %s and %s"%(m,connection.get_pre_fraction_along(),p,d))
                    pre_loc = [ pre_loc[i]+m[i] for i in [0,1,2] ]
                    
                if projection.postsynaptic_population in pop_id_vs_cell.keys():
                    post_cell = pop_id_vs_cell[projection.postsynaptic_population]
                    d = cell_id_vs_seg_id_vs_distal[post_cell.id][connection.get_post_segment_id()]
                    p = cell_id_vs_seg_id_vs_proximal[post_cell.id][connection.get_post_segment_id()]
                    m = [ p[i]+connection.get_post_fraction_along()*(d[i]-p[i]) for i in [0,1,2] ]
                    print_comment("Post point is %s, %s between %s and %s"%(m,connection.get_post_fraction_along(),p,d))
                    post_loc = [ post_loc[i]+m[i] for i in [0,1,2] ]
                  
                if post_loc != pre_loc:
                    info = "// Connection from %s:%s %s -> %s:%s %s\n"%(pre, pre_cell_id, pre_loc, post, post_cell_id, post_loc)

                    print_comment(info)
                    net_file.write("// %s"%info) 
                    if args.conns:
                        net_file.write("cylinder { <%s,%s,%s>, <%s,%s,%s>, .5  pigment{color %s}}\n"%(pre_loc[0],pre_loc[1],pre_loc[2], post_loc[0],post_loc[1],post_loc[2],color))
                    if args.conn_points:
                        net_file.write("object { conn_start_point translate <%s,%s,%s> }\n"%(pre_loc[0],pre_loc[1],pre_loc[2]))
                        net_file.write("object { conn_end_point translate <%s,%s,%s> }\n"%(post_loc[0],post_loc[1],post_loc[2]))
                    
    if args.inputs:
        for il in nml_doc.networks[0].input_lists:
            for input in il.input:
                popi = il.populations
                cell_id = input.get_target_cell_id()
                cell = pop_id_vs_cell[popi]
                
                loc = (0,0,0) 
                if popi in positions.keys(): 
                    if len(positions[popi])>0:
                        loc = positions[popi][cell_id] 

                d = cell_id_vs_seg_id_vs_distal[cell.id][input.get_segment_id()]
                p = cell_id_vs_seg_id_vs_proximal[cell.id][input.get_segment_id()]
                m = [ p[i]+input.get_fraction_along()*(d[i]-p[i]) for i in [0,1,2] ]
                
                input_info = "Input on cell %s:%s at %s; point %s along (%s -> %s): %s"%(popi,cell_id, loc,input.get_fraction_along(),d,p,m)
                
                loc = [ loc[i]+m[i] for i in [0,1,2] ]
                
                net_file.write("/* %s */\n"%input_info)
                net_file.write("object { input_object translate <%s,%s,%s> }\n\n"%(loc[0],loc[1],loc[2]))
        
        
    plane = '''
plane {
   y, vv(-1)
   pigment {checker color rgb 1.0, color rgb 0.8 scale 20}
}
'''

    footer='''

#declare minX = %f;
#declare minY = %f;
#declare minZ = %f;

#declare maxX = %f;
#declare maxY = %f;
#declare maxZ = %f;

#macro uu(xx)
    0.5 * (maxX *(1+xx) + minX*(1-xx))
#end

#macro vv(xx)
    0.5 * (maxY *(1+xx) + minY*(1-xx))
#end

#macro ww(xx)
    0.5 * (maxZ *(1+xx) + minZ*(1-xx))
#end

light_source {
  <uu(5),uu(2),uu(5)>
  color rgb <1,1,1>
  
}
light_source {
  <uu(-5),uu(2),uu(-5)>
  color rgb <1,1,1>
  
}
light_source {
  <uu(5),uu(-2),uu(-5)>
  color rgb <1,1,1>
  
}
light_source {
  <uu(-5),uu(-2),uu(5)>
  color rgb <1,1,1>
}


// Trying to view box
camera {
  location < uu(%s + %s * sin (clock * 2 * 3.141)) , vv(%s + %s * sin (clock * 2 * 3.141)) , ww(%s + %s * cos (clock * 2 * 3.141)) >
  look_at < uu(%s + 0) , vv(%s + 0.05+0.3*sin (clock * 2 * 3.141)) , ww(%s + 0)>
}

%s
    \n'''%(minX,minY,minZ,maxX,maxY,maxZ, args.posx, args.scalex, args.posy, args.scaley, args.posz, args.scalez, args.viewx, args.viewy, args.viewz, (plane if args.plane else "")) ###    end of footer


    pov_file.write(footer)

    pov_file.close()

    if args.movie:
        ini_file_name = pov_file_name.replace(".pov", "_movie.ini")
    
        ini_movie = '''
Antialias=On

+W800 +H600 
        
Antialias_Threshold=0.3
Antialias_Depth=4

Input_File_Name=%s

Initial_Frame=1
Final_Frame=%i
Initial_Clock=0
Final_Clock=1

Cyclic_Animation=on
Pause_when_Done=off
        
        '''
        ini_file = open(ini_file_name, 'w')
        ini_file.write(ini_movie%(pov_file_name, args.frames))
        ini_file.close()
        
        print_comment_v("Created file for generating %i movie frames at: %s. To run this type:\n\n    povray %s\n"%(args.frames,ini_file_name,ini_file_name))
        
    else:
        
        print_comment_v("Created file for generating image of network. To run this type:\n\n    povray %s\n"%(pov_file_name))
        print_comment_v("Or for higher resolution:\n\n    povray Antialias=On Antialias_Depth=10 Antialias_Threshold=0.1 +W1200 +H900 %s\n"%(pov_file_name))


if __name__ == '__main__':
    main()

