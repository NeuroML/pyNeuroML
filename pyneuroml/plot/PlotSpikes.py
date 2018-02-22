
from pyneuroml import pynml

import argparse

import matplotlib.pyplot as plt 
from collections import OrderedDict
import numpy as np
import re


DEFAULTS = {'format': 'id_t',
            'rates': False,
            'save_spike_plot_to':None,
            'rate_window':50,
            'rate_bins':500,
            'show_plots_already':True}

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
                             'id_t: id of cell, space(s)/tab(s), time of spike (default)\n'+\
                             't_id: time of spike, space(s)/tab(s), id of cell')
                             
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


def run(a=None,**kwargs): 

    a = build_namespace(a,**kwargs)
    
    pynml.print_comment_v('Generating spiketime plot for %s; plotting: %s; save to: %s'%(a.spiketime_files, a.show_plots_already, a.save_spike_plot_to))
        
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
        labels.append("%s (%i cells)"%(name,max_id_here-offset_id))
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
                        show_plot_already=False,
                        save_figure_to=a.save_spike_plot_to)
                        
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
