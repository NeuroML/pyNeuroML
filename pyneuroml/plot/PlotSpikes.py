
from pyneuroml import pynml

import argparse

import matplotlib.pyplot as plt 
from collections import OrderedDict
import numpy as np
import re
import sys
import os


DEFAULTS = {'format': 'id_t',
            'rates': False,
            'save_spike_plot_to':None,
            'rate_window':50,
            'rate_bins':500,
            'show_plots_already':True}
            
POP_NAME_SPIKEFILE_WITH_GIDS = 'Spiketimes for GIDs'

def convert_case(name):
    """Converts from camelCase to under_score"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def build_namespace(a=None,**kwargs):
    
    
    if a is None:
        a = argparse.Namespace()
    
    # Add arguments passed in by keyword.  
    for key,value in kwargs.items():
        setattr(a,key,value)

    # Add defaults for arguments not provided.  
    for key,value in DEFAULTS.items():
        if not hasattr(a,key):
            setattr(a,key,value)
    # Change all values from camelCase to under_score.
    # This should have always worked in one pass, but for some reason
    # it is failing (stochastically) on some keys, so it needs to keep 
    # trying until all keys are under_score.  
    flag = True
    while flag:
        flag = False
        for key,value in a.__dict__.items():
            new_key = convert_case(key)
            if new_key != key:
                setattr(a,new_key,value)
                delattr(a,key)
                flag = True
    return a


def process_args():
    """ 
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="A script for plotting files containing spike time data")
    
    parser.add_argument('spiketimeFiles', 
                        type=str, 
                        metavar='<spiketime file>', 
                        help='List of text file containing spike times', 
                        nargs='+')
                        
    parser.add_argument('-format', 
                        type=str,
                        metavar='<format>',
                        default=DEFAULTS['format'],
                        help='How the spiketimes are represented on each line of file:\n'+\
                             'id_t: id of cell, space(s)/tab(s), time of spike (default);\n'+\
                             't_id: time of spike, space(s)/tab(s), id of cell;\n'+\
                             'sonata: SONATA format HDF5 file containing spike times')
                             
    parser.add_argument('-rates', 
                        action='store_true',
                        default=DEFAULTS['rates'],
                        help='Show a plot of rates')
                        
    parser.add_argument('-showPlotsAlready', 
                        action='store_true',
                        default=DEFAULTS['show_plots_already'],
                        help='Show plots once generated')
                        
    parser.add_argument('-saveSpikePlotTo', 
                        type=str,
                        metavar='<spiketime plot filename>',
                        default=DEFAULTS['save_spike_plot_to'],
                        help='Name of file in which to save spiketime plot')
                        
    parser.add_argument('-rateWindow', 
                        type=int,
                        metavar='<rate window>',
                        default=DEFAULTS['rate_window'],
                        help='Window for rate calculation in ms')
                        
    parser.add_argument('-rateBins', 
                        type=int,
                        metavar='<rate bins>',
                        default=DEFAULTS['rate_bins'],
                        help='Number of bins for rate histogram')
                        
    return parser.parse_args()
                        
                    
def main(args=None):
    if args is None:
        args = process_args()
    run(a=args)
    
    
def read_sonata_spikes_hdf5_file(file_name):
    
    full_path = os.path.abspath(file_name)
    pynml.print_comment_v("Loading SONATA spike times from: %s (%s)"%(file_name,full_path))
    
    import tables   # pytables for HDF5 support
    h5file=tables.open_file(file_name,mode='r')
    
    sorting = h5file.root.spikes._v_attrs.sorting if hasattr(h5file.root.spikes._v_attrs, 'sorting') else '???'
    pynml.print_comment_v("Opened HDF5 file: %s; sorting=%s"%(h5file.filename,sorting))
    
    ids_times_pops = {}
    
    if hasattr(h5file.root.spikes, 'gids'):
        
        gids = h5file.root.spikes.gids
        timestamps = h5file.root.spikes.timestamps
        ids_times = {}
        count=0
        max_t = -1*sys.float_info.max
        min_t = sys.float_info.max
        for i in range(len(gids)):
            id = gids[i]
            t = timestamps[i]
            max_t = max(max_t,t)
            min_t = min(min_t,t)
            if not id in ids_times:
                ids_times[id] = []
            ids_times[id].append(t)
            count+=1

        ids = ids_times.keys()
        pynml.print_comment_v("Loaded %s spiketimes, ids (%s -> %s) times (%s -> %s)"%(count,min(ids), max(ids),min_t,max_t))
        
        ids_times_pops[POP_NAME_SPIKEFILE_WITH_GIDS] = ids_times
    else:
        
        for group in h5file.root.spikes:
            node_ids = group.node_ids
            timestamps = group.timestamps
            ids_times = {}
            count=0
            max_t = -1*sys.float_info.max
            min_t = sys.float_info.max
            for i in range(len(node_ids)):
                id = node_ids[i]
                t = timestamps[i]
                max_t = max(max_t,t)
                min_t = min(min_t,t)
                if not id in ids_times:
                    ids_times[id] = []
                ids_times[id].append(t)
                count+=1

            ids = ids_times.keys()
            pynml.print_comment_v("Loaded %s spiketimes for %s, ids (%s -> %s) times (%s -> %s)"%(count,group._v_name,min(ids), max(ids),min_t,max_t))

            ids_times_pops[group._v_name] = ids_times
    
    h5file.close()
    
    return ids_times_pops


def run(a=None,**kwargs): 

    a = build_namespace(a,**kwargs)
    
    pynml.print_comment_v('Generating spiketime plot for %s; format: %s; plotting: %s; save to: %s'%(a.spiketime_files, a.format, a.show_plots_already, a.save_spike_plot_to))
        
    xs = []
    ys = []
    labels = []
    markers = []
    linestyles = []

    offset_id = 0

    max_time = 0
    max_id = 0
    unique_ids = []
    times = OrderedDict()
    ids_in_file = OrderedDict()
    
    if a.format == 'sonata' or a.format == 's':
        
        for file_name in a.spiketime_files:
            
            ids_times_pops = read_sonata_spikes_hdf5_file(file_name)
            
            for pop in ids_times_pops:
                ids_times = ids_times_pops[pop]

                x = []
                y = []
                max_id_here = 0

                name = file_name.split('/')[-1]
                if name.endswith('_spikes.h5'): name = name[:-10]
                elif name.endswith('.h5'): name = name[:-3]
                times[name] = []
                ids_in_file[name] = []

                for id in ids_times:

                    for t in ids_times[id]:

                        id_shifted = offset_id+int(float(id))
                        max_id = max(max_id,id_shifted)

                        if not id_shifted in ids_in_file[name]:
                            ids_in_file[name].append(id_shifted)
                        times[name].append(t)
                        max_id_here = max(max_id_here,id_shifted) 
                        max_time = max(t,max_time)
                        if not id_shifted in unique_ids:
                            unique_ids.append(id_shifted)
                        x.append(t)
                        y.append(id_shifted)

                #print("max_id_here in %s: %i"%(file_name,max_id_here))
                labels.append("%s, %s (%i)"%(name,pop,max_id_here-offset_id))
                offset_id = max_id_here+1
                xs.append(x)
                ys.append(y)
                markers.append('.')
                linestyles.append('')
            

        xlim = [max_time/-20.0, max_time*1.05]
        ylim = [max_id/-20., max_id*1.05] if max_id>0 else [-1,1]
        markersizes = []
        for xx in xs:
            if len(unique_ids)>50:
               markersizes.append(2) 
            elif len(unique_ids)>200:
               markersizes.append(1) 
            else:
               markersizes.append(4) 
    else:
    
        for file_name in a.spiketime_files:
            pynml.print_comment_v("Loading spike times from: %s"%file_name)
            spikes_file = open(file_name)
            x = []
            y = []
            max_id_here = 0

            name = spikes_file.name
            if name.endswith('.spikes'): name = name[:-7]
            if name.endswith('.spike'): name = name[:-6]
            times[name] = []
            ids_in_file[name] = []

            for line in spikes_file:
                if not line.startswith('#'):
                    if a.format == 'id_t':
                        [id, t] = line.split()
                    elif a.format == 't_id':
                        [t, id] = line.split()
                    id_shifted = offset_id+int(float(id))
                    max_id = max(max_id,id_shifted)
                    t = float(t)
                    if not id_shifted in ids_in_file[name]:
                        ids_in_file[name].append(id_shifted)
                    times[name].append(t)
                    max_id_here = max(max_id_here,id_shifted) 
                    max_time = max(t,max_time)
                    if not id_shifted in unique_ids:
                        unique_ids.append(id_shifted)
                    x.append(t)
                    y.append(id_shifted)

            #print("max_id_here in %s: %i"%(file_name,max_id_here))
            labels.append("%s (%i)"%(name,max_id_here-offset_id))
            offset_id = max_id_here+1
            xs.append(x)
            ys.append(y)
            markers.append('.')
            linestyles.append('')


        xlim = [max_time/-20.0, max_time*1.05]
        ylim = [max_id_here/-20., max_id_here*1.05]
        markersizes = []
        for xx in xs:
            if len(unique_ids)>50:
               markersizes.append(2) 
            elif len(unique_ids)>200:
               markersizes.append(1) 
            else:
               markersizes.append(4) 
            
    
    pynml.generate_plot(xs,
                        ys, 
                        "Spike times from: %s"%a.spiketime_files, 
                        labels = labels, 
                        linestyles=linestyles,
                        markers=markers,
                        xaxis = "Time (s)", 
                        yaxis = "Cell index", 
                        xlim = xlim,
                        ylim = ylim,
                        markersizes = markersizes,
                        grid = False,
                        show_plot_already=False,
                        save_figure_to=a.save_spike_plot_to,
                        legend_position='right')
                        
    if a.rates:

        plt.figure()
        bins = a.rate_bins
        for name in times:
            tt = times[name]
            ids_here = len(ids_in_file[name])
            
            plt.hist(tt, bins=bins,histtype='step',weights=[bins*max(tt)/(float(ids_here))]*len(tt),label=name+"_h")
            hist, bin_edges = np.histogram(tt, bins=bins,weights=[bins*max(tt)/(float(ids_here))]*len(tt))
            '''
            width = bin_edges[1]-bin_edges[0]
            mids = [i+width/2 for i in bin_edges[:-1]]
            plt.plot(mids, hist,label=name)'''
            
            
        plt.figure()
        
        for name in times:
            tt = times[name]
            ids_here = len(ids_in_file[name])
            
            hist, bin_edges = np.histogram(tt, bins=bins,weights=[bins*max(tt)/(float(ids_here))]*len(tt))
        
            width = bin_edges[1]-bin_edges[0]
            mids = [i+width/2 for i in bin_edges[:-1]]
            
            boxes = [5,10,20,50]
            boxes = [20,50]
            boxes = [int(a.rate_window)]
            for b in boxes:
                box = np.ones(b)
                
                hist_c = np.convolve(hist/len(box), box)

                ys = hist_c
                xs = [i/(float(len(ys))) for i in range(len(ys))]
                plt.plot(xs, ys,label=name+'_%i_c'%b)
            
        #plt.legend()
        
    if a.show_plots_already:
        plt.show()
    else:
        plt.close() 


if __name__ == '__main__':
    main()
