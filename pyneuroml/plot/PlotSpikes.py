
from pyneuroml import pynml

import argparse


def process_args():
    """ 
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="A script for plotting files containing spike time data")
    
    parser.add_argument('spiketime_files', type=str, metavar='<spiketime file>', 
                        help='List of text file containing spike times', nargs='+')
                        
    parser.add_argument('-format', 
                        type=str,
                        metavar='<format>',
                        default='id_t',
                        help='How the spiketimes are represented on each line of file:\n'+\
                             'id_t: id of cell, space(s)/tab(s), time of spike (default)\n'+\
                             't_id: time of spike, space(s)/tab(s), id of cell')
                        
    return parser.parse_args()
                        
                        
def main ():

    args = process_args()
        
    xs = []
    ys = []
    labels = []
    markers = []
    linestyles = []

    offset_id = 0

    max_time = 0
    max_id = 0
    unique_ids = []
    for file_name in args.spiketime_files:
        print("Loading spike times from: %s"%file_name)
        spikes_file = open(file_name)
        x = []
        y = []
        max_id_here = 0
        for line in spikes_file:
            if not line.startswith('#'):
                if args.format == 'id_t':
                    [id, t] = line.split()
                elif args.format == 't_id':
                    [t, id] = line.split()
                id_shift = offset_id+int(float(id))
                max_id = max(max_id,id_shift)
                t = float(t)
                max_id_here = max(max_id_here,id_shift) 
                max_time = max(t,max_time)
                if not id_shift in unique_ids:
                    unique_ids.append(id_shift)
                x.append(t)
                y.append(id_shift)
        print("max_id_here in %s: %i"%(file_name,max_id_here))
        labels.append("%s (%i cells)"%(spikes_file.name,max_id_here-offset_id))
        offset_id = max_id_here+1
        xs.append(x)
        ys.append(y)
        markers.append('.')
        linestyles.append('')


    xlim = [max_time/-20.0, max_time*1.05]
    ylim = [max_id_here/-20., max_id_here*1.05]
    markersizes = []
    for a in xs:
        if len(unique_ids)>50:
           markersizes.append(2) 
        elif len(unique_ids)>200:
           markersizes.append(1) 
        else:
           markersizes.append(4) 
            
    
    pynml.generate_plot(xs,
                        ys, 
                        "Spike times from: %s"%spikes_file.name, 
                        labels = labels, 
                        linestyles=linestyles,
                        markers=markers,
                        xaxis = "Time (s)", 
                        yaxis = "Cell index", 
                        xlim = xlim,
                        ylim = ylim,
                        markersizes = markersizes,
                        grid = False,
                        show_plot_already=True)


if __name__ == '__main__':
    main()
