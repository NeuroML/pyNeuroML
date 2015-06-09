#!/usr/bin/env python

#
#
#   A script which can be run to generate a LEMS file to analyse the behaviour of channels in NeuroML 2
#
#
#

import argparse

import neuroml.loaders as loaders
from pyneuroml import pynml

import airspeed
import sys
import os
import os.path

import matplotlib.pyplot as pylab
import pprint

import glob
import re

pp = pprint.PrettyPrinter(depth=4)

TEMPLATE_FILE = "%s/LEMS_Test_TEMPLATE.xml"%(os.path.dirname(__file__))
HTML_TEMPLATE_FILE = "%s/ChannelInfo_TEMPLATE.html"%(os.path.dirname(__file__))
     
MAX_COLOUR = (255, 0, 0)
MIN_COLOUR = (255, 255, 0)

print("\n") 


def process_args():
    """ 
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="A script which can be run to generate a LEMS file to analyse the behaviour of channels in NeuroML 2")

    parser.add_argument('channelFiles', 
                        type=str,
                        nargs='+',
                        metavar='<NeuroML 2 Channel file>', 
                        help='Name of the NeuroML 2 file(s)')
                        
                        
    parser.add_argument('-v',
                        action='store_true',
                        default=False,
                        help="Verbose output")
                        
    parser.add_argument('-minV', 
                        type=int,
                        metavar='<min v>',
                        default=-100,
                        help='Minimum voltage to test (integer, mV)')
                        
    parser.add_argument('-maxV', 
                        type=int,
                        metavar='<max v>',
                        default=100,
                        help='Maximum voltage to test (integer, mV)')
                        
    parser.add_argument('-temperature', 
                        type=float,
                        metavar='<temperature>',
                        default=6.3,
                        help='Temperature (float, celsius)')
                        
    parser.add_argument('-duration', 
                        type=float,
                        metavar='<duration>',
                        default=100,
                        help='Duration of simulation in ms')
                        
    parser.add_argument('-clampDelay', 
                        type=float,
                        metavar='<clamp delay>',
                        default=10,
                        help='Delay before voltage clamp is activated in ms')
                        
    parser.add_argument('-clampDuration', 
                        type=float,
                        metavar='<clamp duration>',
                        default=80,
                        help='Duration of voltage clamp in ms')
                        
    parser.add_argument('-clampBaseVoltage', 
                        type=float,
                        metavar='<clamp base voltage>',
                        default=-70,
                        help='Clamp base (starting/finishing) voltage in mV')
                        
    parser.add_argument('-stepTargetVoltage', 
                        type=float,
                        metavar='<step target voltage>',
                        default=20,
                        help='Voltage in mV through which to step voltage clamps')
                        
    parser.add_argument('-erev', 
                        type=float,
                        metavar='<reversal potential>',
                        default=0,
                        help='Reversal potential of channel for currents')
                        
    parser.add_argument('-caConc', 
                        type=float,
                        metavar='<Ca2+ concentration>',
                        default=5e-5,
                        help='Internal concentration of Ca2+ (float, concentration in mM)')
                        
    parser.add_argument('-norun',
                        action='store_true',
                        default=False,
                        help="If used, just generate the LEMS file, don't run it")
                        
    parser.add_argument('-nogui',
                        action='store_true',
                        default=False,
                        help="Supress plotting of variables and only save data to file")
                        
    parser.add_argument('-html',
                        action='store_true',
                        default=False,
                        help="Generate a HTML page (as well as a Markdown version...) featuring the plots for the channel")
                        
    parser.add_argument('-ivCurve',
                        action='store_true',
                        default=False,
                        help="Save currents through voltage clamp at each level & plot current vs voltage for ion channel")
                        
                        
    return parser.parse_args()


def get_colour_hex(fract):
    rgb = [ hex(int(x + (y-x)*fract)) for x, y in zip(MIN_COLOUR, MAX_COLOUR) ]
    col = "#"
    for c in rgb: col+= ( c[2:4] if len(c)==4 else "00")
    return col

    
def get_state_color(s):
    col='#000000'
    if s.startswith('m'): col='#FF0000'
    if s.startswith('h'): col='#00FF00'
    if s.startswith('n'): col='#0000FF'
    if s.startswith('a'): col='#FF0000'
    if s.startswith('b'): col='#00FF00'
    if s.startswith('c'): col='#0000FF'
    if s.startswith('q'): col='#FF00FF'
    if s.startswith('e'): col='#00FFFF'
    if s.startswith('f'): col='#FFFF00'
    
    return col


def merge_with_template(model, templfile):
    if not os.path.isfile(templfile):
        templfile = os.path.join(os.path.dirname(sys.argv[0]), templfile)
    with open(templfile) as f:
        templ = airspeed.Template(f.read())
    return templ.merge(model)


def generate_lems_channel_analyser(channel_file, channel, min_target_voltage, \
                      step_target_voltage, max_target_voltage, clamp_delay, \
                      clamp_duration, clamp_base_voltage, duration, erev, gates, \
                      temperature, ca_conc, iv_curve):
                      
    target_voltages = []
    v = min_target_voltage
    while v <= max_target_voltage:
        target_voltages.append(v)
        v+=step_target_voltage

    target_voltages_map = []
    for t in target_voltages:
        fract = float(target_voltages.index(t)) / (len(target_voltages)-1)
        info = {}
        info["v"] = t
        info["v_str"] = str(t).replace("-", "min")
        info["col"] = get_colour_hex(fract)
        target_voltages_map.append(info)
        #print info

    model = {"channel_file":        channel_file, 
             "channel":             channel, 
             "target_voltages" :    target_voltages_map,
             "clamp_delay":         clamp_delay,
             "clamp_duration":      clamp_duration,
             "clamp_base_voltage":  clamp_base_voltage,
             "min_target_voltage":  min_target_voltage,
             "max_target_voltage":  max_target_voltage,
             "duration":  duration,
             "erev":  erev,
             "gates":  gates,
             "temperature":  temperature,
             "ca_conc":  ca_conc,
             "iv_curve":  iv_curve}
             
    #pp.pprint(model)

    merged = merge_with_template(model, TEMPLATE_FILE)

    return merged


def main():

    args = process_args()
        
    verbose = args.v
    
    ## Get name of channel mechanism to test

    if verbose: print("Going to test channel from file: "+ args.channelFile)
    
    step_target_voltage = args.stepTargetVoltage
    clamp_delay = args.clampDelay 
    clamp_duration = args.clampDuration
    clamp_base_voltage = args.clampBaseVoltage
    duration = args.duration
    erev = args.erev
    
    if args.ivCurve:
        if duration > clamp_delay + clamp_duration:
            
            print("Note: when option -ivCurve is specified, total duration "+
                  "(%sms) should be equal to or less than initial delay (%sms) + clamp duration(%sms)."%(duration, clamp_delay, clamp_duration))
            print("This is to facilitate calculation of steady state IV curves\n")
            exit(1)
    
    info = {}
    chan_list = []
    info['info'] = "Channel information at %s degC, reversal potential %smV, [Ca2+]: %smM"%(args.temperature, args.erev, args.caConc)
                    
    info["channels"] = chan_list
    
    for channel_file in args.channelFiles:

        if not os.path.isfile(channel_file):
            print("File could not be found: %s!\n"%channel_file)
            exit(1)
        doc = loaders.NeuroMLLoader.load(channel_file)

        channels = []
        for c in doc.ion_channel_hhs: channels.append(c)
        for c in doc.ion_channel: channels.append(c)

        for ic in channels:    
            channel_id = ic.id
            gates = []

            for g in ic.gates:
                gates.append(g.id)
            for g in ic.gate_hh_rates:
                gates.append(g.id)
            for g in ic.gate_hh_tau_infs:
                gates.append(g.id)

            if len(gates) == 0:
                print("No gates found in a channel with ID %s"%channel_id)
            else:
                
                if args.html:
                    if not os.path.isdir('html'):
                        os.mkdir('html')
                    channel_info = {}
                    chan_list.append(channel_info)
                    channel_info['id'] = channel_id
                    channel_info['file'] = channel_file
                    if ic.notes:
                        #print ic.notes
                        channel_info['notes'] = ic.notes
                        
                lems_content = generate_lems_channel_analyser(channel_file, channel_id, args.minV, \
                                  step_target_voltage, args.maxV, clamp_delay, \
                                  clamp_duration, clamp_base_voltage, duration, erev, gates, \
                                  args.temperature, args.caConc, args.ivCurve)

                new_lems_file = "LEMS_Test_%s.xml"%channel_id


                lf = open(new_lems_file, 'w')
                lf.write(lems_content)
                lf.close()

                print("Written generated LEMS file to %s\n"%new_lems_file)

                if not args.norun:
                    results = pynml.run_lems_with_jneuroml(new_lems_file, nogui=True, load_saved_data=True, plot=False)

                    if not args.nogui:
                        v = "rampCellPop0[0]/v"

                        fig = pylab.figure()
                        fig.canvas.set_window_title("Time Course(s) of activation variables of %s from %s at %sdegC"%(channel_id, channel_file, args.temperature))

                        pylab.xlabel('Membrane potential (V)')
                        pylab.ylabel('Time Course - tau (s)')
                        pylab.grid('on')
                        for g in gates:
                            g_tau = "rampCellPop0[0]/test/%s/%s/tau"%(channel_id, g)
                            col=get_state_color(g)
                            pylab.plot(results[v], results[g_tau], color=col, linestyle='-', label="%s %s tau"%(channel_id, g))
                            pylab.gca().autoscale(enable=True, axis='x', tight=True)

                        pylab.legend()

                        if args.html:
                            pylab.savefig('html/%s.tau.png'%channel_id)

                        fig = pylab.figure()
                        fig.canvas.set_window_title("Steady state(s) of activation variables of %s from %s at %sdegC"%(channel_id, channel_file, args.temperature))
                        pylab.xlabel('Membrane potential (V)')
                        pylab.ylabel('Steady state - inf')
                        pylab.grid('on')
                        for g in gates:
                            g_inf = "rampCellPop0[0]/test/%s/%s/inf"%(channel_id, g)
                            #print("Plotting %s"%(g_inf))
                            col=get_state_color(g)
                            pylab.plot(results[v], results[g_inf], color=col, linestyle='-', label="%s %s inf"%(channel_id, g))
                            pylab.gca().autoscale(enable=True, axis='x', tight=True)
                        pylab.legend()

                        if args.html:
                            pylab.savefig('html/%s.inf.png'%channel_id)
                            
                        if args.ivCurve:
                            # Based on work by Rayner Lucas here: https://github.com/openworm/BlueBrainProjectShowcase/blob/master/Channelpedia/iv_analyse.py
                            fig = pylab.figure()
                            fig.canvas.set_window_title("Currents through voltage clamp for %s from %s at %sdegC, erev: %sV"%(channel_id, channel_file, args.temperature, erev))
                            pylab.xlabel('Time (s)')
                            pylab.ylabel('Current (A)')
                            pylab.grid('on')
                            filenames = glob.glob('./%s.i_*.lems.dat'%channel_id)
                            
                            i_peaks = {}
                            i_steady = {}
                            hold_v = []
                            currents = {}
                            
                            for name in filenames:
                                times = []
                                v_match = re.match("\./%s.i_(.*)\.lems\.dat"%channel_id, name)
                                voltage = v_match.group(1)
                                voltage = voltage.replace("min", "-")
                                voltage = float(voltage)/1000
                                hold_v.append(voltage)
                                currents[voltage] = []
                                
                                i_file  = open(name)
                                i_max = -1*sys.float_info.min
                                i_min = sys.float_info.min
                                
                                for line in i_file:
                                    t = float(line.split()[0])
                                    times.append(t)
                                    i = float(line.split()[1])
                                    currents[voltage].append(i)
                                    if i>i_max: i_max = i
                                    if i<i_min: i_min = i
                                    
                                i_peak = i_max if abs(i_max) > abs(i_min) else i_min
                                i_peaks[voltage] = -1 * i_peak
                                i_steady[voltage] = -1 * i
                                    
                                
                            hold_v.sort()
                            
                            for v in hold_v:
                                col = get_colour_hex(float(hold_v.index(v))/len(hold_v))
                                pylab.plot(times, currents[v], color=col, linestyle='-', label="%s V"%(v))
                                
                            pylab.legend()
                            
                            
                            fig = pylab.figure()
                            fig.canvas.set_window_title("Currents vs. holding potentials at erev %sV"%erev)
                            pylab.xlabel('Membrane potential (V)')
                            pylab.ylabel('Current (A)')
                            pylab.grid('on')
                        
                            pylab.plot(hold_v, [i_peaks[v] for v in hold_v], 'ko-', label="Peak currents")
                            pylab.legend()
                            
                            # Save to file...
                            iv_file = open('%s.i_peak.dat'%channel_id,'w')
                            for v in hold_v:
                                iv_file.write("%s\t%s\n"%(v,i_peaks[v]))
                            iv_file.close()
                            
                            fig = pylab.figure()
                            fig.canvas.set_window_title("Currents vs. holding potentials at erev %sV"%erev)
                            pylab.xlabel('Membrane potential (V)')
                            pylab.ylabel('Current (A)')
                            pylab.grid('on')
                            
                            pylab.plot(hold_v, [i_steady[v] for v in hold_v], 'ko-', label="Steady state currents")
                                
                            pylab.legend()
                            
                            # Save to file...
                            iv_file = open('%s.i_steady.dat'%channel_id,'w')
                            for v in hold_v:
                                iv_file.write("%s\t%s\n"%(v,i_steady[v]))
                            iv_file.close()


        
    if not args.html:
        pylab.show()
    else:
        pp.pprint(info)
        merged = merge_with_template(info, HTML_TEMPLATE_FILE)
        print(merged)
        new_html_file = "html/ChannelInfo.html"
        lf = open(new_html_file, 'w')
        lf.write(merged)
        lf.close()
        print('Written HTML info to: %s'%new_html_file)


if __name__ == '__main__':
    main()
