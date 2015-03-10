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
import os.path

from matplotlib import pyplot as plt

TEMPLATE_FILE = "%s/LEMS_Test_TEMPLATE.xml"%(os.path.dirname(__file__))
    
MAX_COLOUR = (255, 0, 0)
MIN_COLOUR = (255, 255, 0)

print("\n") 


def process_args():
    """ 
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="A script which can be run to generate a LEMS file to analyse the behaviour of channels in NeuroML 2")

    parser.add_argument('channelFile', type=str, metavar='<NeuroML 2 Channel file>', 
                        help='Name of the NeuroML 2 file')
                        
    parser.add_argument('channelId', type=str, metavar='<Channel Id>', 
                        help='Id of the channel in the NeuroML 2 file ')
                        
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
                        
                        
    return parser.parse_args()


def get_colour_hex(fract):
    rgb = [ hex(int(x + (y-x)*fract)) for x, y in zip(MIN_COLOUR, MAX_COLOUR) ]
    col = "#"
    for c in rgb: col+= ( c[2:4] if len(c)==4 else "00")
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
                      temperature, ca_conc):
                      
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
             "ca_conc":  ca_conc}

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

    if not os.path.isfile(args.channelFile):
        print("File could not be found: %s!\n"%args.channelFile)
        exit(1)
    doc = loaders.NeuroMLLoader.load(args.channelFile)
    gates = []
    channels = []
    for c in doc.ion_channel_hhs: channels.append(c)
    for c in doc.ion_channel: channels.append(c)
    
    for ic in channels:
        print("Checking channel "+ic.id)
        if ic.id == args.channelId:
            for g in ic.gates:
                gates.append(g.id)
            for g in ic.gate_hh_tau_infs:
                gates.append(g.id)
               
    if len(gates) == 0:
        print("No gates found in a channel with ID %s"%args.channelId)
        exit()
    
    lems_content = generate_lems_channel_analyser(args.channelFile, args.channelId, args.minV, \
                      step_target_voltage, args.maxV, clamp_delay, \
                      clamp_duration, clamp_base_voltage, duration, erev, gates, \
                      args.temperature, args.caConc)
                      
    new_lems_file = "LEMS_Test_%s.xml"%args.channelId

                      
    lf = open(new_lems_file, 'w')
    lf.write(lems_content)
    lf.close()
        
    print("Written generated LEMS file to %s\n"%new_lems_file)
    
    if not args.norun:
        results = pynml.run_lems_with_jneuroml(new_lems_file, nogui=True, load_saved_data=True, plot=False)
    
        #print results.keys()
        
        plt.xlabel('Membrane potential (V)')
        plt.ylabel('Steady state - inf')
        plt.grid('on')
        v = "rampCellPop0[0]/v"
        for g in gates:
            g_inf = "rampCellPop0[0]/test/%s/%s/inf"%(args.channelId, g)
            #print("Plotting %s"%(g_inf))
            plt.plot(results[v], results[g_inf], '-', label="%s %s inf"%(args.channelId, g))
            
        plt.legend()
        plt.figure()
        
        plt.xlabel('Membrane potential (V)')
        plt.ylabel('Time Course - tau (s)')
        for g in gates:
            g_tau = "rampCellPop0[0]/test/%s/%s/tau"%(args.channelId, g)
            plt.plot(results[v], results[g_tau], '-', label="%s %s tau"%(args.channelId, g))
        
        plt.legend()
        
        plt.show()


if __name__ == '__main__':
    main()
