#!/usr/bin/env python

#
#
#   A file which can be run in (Python enabled) NEURON to analyse the rate
#   variables contained in a mod file
#
#

import argparse

import neuron
print("\n\n") 

import matplotlib.pyplot as plt
from pylab import *
from math import log


def process_args():
    """ 
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="A script which can be run in (Python enabled) NEURON to analyse the rate variables contained in a mod file")

    parser.add_argument('channel', type=str, metavar='<channel name>', 
                        help='Name of the channel as used by NEURON (i.e. in SUFFIX statement)')
                        
    parser.add_argument('-v',
                        action='store_true',
                        default=False,
                        help="Verbose output")
                        
    parser.add_argument('-nogui',
                        action='store_true',
                        default=False,
                        help="Supress plotting of variables and only save to file")
                        
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
                        
                        
    parser.add_argument('-stepV', 
                        type=int,
                        metavar='<step v>',
                        default=10,
                        help='Voltage step to use (integer, mV)')
                        
    parser.add_argument('-dt', 
                        type=float,
                        metavar='<time step>',
                        default=0.01,
                        help='Timestep for simulations, dt, in ms') #OR -1 for variable time step')
                        
    parser.add_argument('-temperature', 
                        type=float,
                        metavar='<temperature>',
                        default=6.3,
                        help='Temperature (float, celsius)')
                        
    parser.add_argument('-modFile', 
                        type=str,
                        metavar='<name of mod file>',
                        help='Name of the mod file containing the channel')

    
    return parser.parse_args()

def get_state_color(s):
    col='#000000'
    if s=='m': col='#FF0000'
    if s=='h': col='#00FF00'
    if s=='n': col='#0000FF'
    if s=='a': col='#FF0000'
    if s=='b': col='#00FF00'
    if s=='c': col='#0000FF'
    
    return col

def main():

    args = process_args()
        
    verbose = args.v
    
    ## Get name of channel mechanism to test

    chanToTest = args.channel
    if verbose: print "Going to test channel: "+ chanToTest

    ## Create the standard vars h, p for accessing hoc from Python & vice versa

    print "Starting NEURON in Python mode..."
    h = neuron.h
    h.load_file('stdrun.hoc')
    h('''
    objref p
    p = new PythonObject()
    ''')


    h.celsius = args.temperature
        
    ## Create a section, set size & insert pas, passive channel mechanism

    sec = h.Section()

    secname = sec.name()
    sec.L=10
    sec.nseg=1
    for seg in sec :seg.diam = 5

    sec.insert("pas")
    sec(0.5).g_pas = 0.001
    sec(0.5).e_pas = -65


    ## insert channel into section

    sec.insert(str(chanToTest))


    ## Read state variables from mod file

    modFileName = chanToTest+".mod"
    if args.modFile:
        modFileName = args.modFile
    modFile = open(modFileName, 'r')
    inState = 0
    states = []
    for line in modFile:
        if line.count('STATE') > 0:
            inState = 1

        if inState==1:
            if line.count('}') > 0:
                inState = 0
            chopped = line.split()
            for el in chopped:
                if el != '{' and el != '}' and el != 'STATE': 
                    if el.startswith('{'): states.append(el[1:])
                    elif el.endswith('}'): states.append(el[:-1])
                    else: states.append(el)

    if verbose: print "States found in mod file: " + str(states)


    ## Settings for the voltage clamp test

    minV = args.minV
    maxV = args.maxV
    interval = args.stepV
    volts = range(minV,maxV+interval,interval)

    v0 = -0.5                           # Pre holding potential
    preHold = 50                       # and duration
    postHoldStep = 10                  # Post step holding time between steady state checks
    postHoldMax = postHoldStep * 1000   # Max sim run time
    
    timeToCheckTau = preHold + (10*h.dt)


    steadyStateVals = {}
    timeCourseVals = {}
    for s in states:
        steadyStateVals[s] = []
        timeCourseVals[s] = []




    if verbose: 
        figV = plt.figure()
        figV.suptitle("Membrane potentials")
        plV = figV.add_subplot(111, autoscale_on=True)

        figR = plt.figure()
        figR.suptitle("Rate variables at %s degC"%h.celsius)
        plR = figR.add_subplot(111, autoscale_on=True)


    for vh in volts:

        tstopMax = preHold + postHoldMax

        h('tstop = '+str(tstopMax))
        h.dt = args.dt
        
        if h.dt == -1:
            h.cvode.active(1)
            h.cvode.atol(0.0001)
            
        # Alternatively use a SEClamp obj
        clampobj = h.SEClamp(.5)
        clampobj.dur1=preHold
        clampobj.amp1=v0
        clampobj.dur2=postHoldMax
        clampobj.amp2=vh
        clampobj.rs=0.001


        tRec = []
        vRec = []
        rateRec = {}
        for s in states:
            rateRec[s] = []

        print "Starting simulation with channel %s of max time: %f, with holding potential: %f"%(chanToTest, tstopMax, vh)
        #h.cvode.active(1)
        h.finitialize(v0)
        tolerance = 1e-5
        lastCheckTime = -1
        lastCheckVal = {}
        initSlopeVal = {}
        foundTau = []
        foundInf = []

        for s in states:
            lastCheckVal[s]=-1e-9
            initSlopeVal[s]=1e9


        while (h.t <= tstopMax) and (s not in foundInf or s not in foundTau):

            h.fadvance()
            tRec.append(h.t)
            vRec.append(sec(0.5).v)
            if verbose: print "--- Time: %s; dt: %s; voltage %f; found Tau %s; found Inf %s"%(h.t, h.dt, vh, foundTau, foundInf)
            for s in states:
                rateVal = eval("sec(0.5)."+s+"_"+chanToTest)
                rateRec[s].append(float(rateVal))
                
                if s not in foundTau:
                    if(h.t >= preHold):
                        slope = (rateRec[s][-1] - rateRec[s][-2])/h.dt
                        fractOfInit = slope/initSlopeVal[s]
                        if verbose: print "        Slope of %s: %s (%s -> %s); init slope: %s; fractOfInit: %s; rateVal: %s"%(s, slope, rateRec[s][-2], rateRec[s][-1], initSlopeVal[s], fractOfInit, rateVal)
                        
                        if initSlopeVal[s]==1e9 and h.t >= timeToCheckTau:
                            initSlopeVal[s] = slope
                            if verbose: print "        Init slope of %s: %s at val: %s; timeToCheckTau: %s"%(s, slope, rateVal, timeToCheckTau)
                        elif initSlopeVal[s]!=1e9:

                            if fractOfInit < 0.367879441:
                                tau =  (h.t-timeToCheckTau)  #/ (-1*log(fractOfInit))
                                if verbose: print "        Found! Slope %s: %s, init: %s; at val: %s; time diff %s; fractOfInit: %s; log %s; tau %s"%(s, slope, initSlopeVal[s], rateVal, h.t-timeToCheckTau, fractOfInit, log(fractOfInit), tau)
                                foundTau.append(s)
                                timeCourseVals[s].append(tau)
                            else:
                                if verbose: print "        Not yet fallen by 1/e: %s"% fractOfInit   




            if h.t >= preHold and h.t >= lastCheckTime+postHoldStep:
                
                lastCheckTime = h.t

                for s in states:
                    val = eval("sec(0.5)."+s+"_"+chanToTest)

                    if s not in foundInf:
                        if abs((lastCheckVal[s]-val)/val) > tolerance:
                            if verbose: print "State %s has failed at %f; lastCheckVal[s] = %f; fract = %f; tolerance = %f"%(s,val, lastCheckVal[s], ((lastCheckVal[s]-val)/val), tolerance)
                        else:
                            if verbose: print "State %s has passed at %f"%(s,val)
                            foundInf.append(s)

                        lastCheckVal[s] = val


        if verbose: print "Finished run,  t: %f, v: %f, vh: %f, initSlopeVal: %s, timeCourseVals: %s ---  "%(h.t, sec(0.5).v, vh, str(initSlopeVal), str(timeCourseVals))

        if verbose: plV.plot(tRec, vRec, solid_joinstyle ='round', solid_capstyle ='round', color='#000000', linestyle='-', marker='None')

        for s in states:
            col=get_state_color(s)
            if verbose: plR.plot(tRec, rateRec[s], solid_joinstyle ='round', solid_capstyle ='round', color=col, linestyle='-', marker='None')

        for s in states:
            val = eval("sec(0.5)."+s+"_"+chanToTest)
            steadyStateVals[s].append(val)



    figRates = plt.figure()
    figRates.suptitle("Steady states of rate activation variables")
    plRates = figRates.add_subplot(111, autoscale_on=False, xlim=(minV - 0.1*(maxV-minV), maxV + 0.1*(maxV-minV)), ylim=(-0.1, 1.1))


    figTau = plt.figure()
    figTau.suptitle("Time courses of rate activation variables at %s degC"%h.celsius)
    plTau = figTau.add_subplot(111, autoscale_on=True)

    for s in states:
        col=get_state_color(s)

        plRates.plot(volts, steadyStateVals[s], label='Steady state of %s in %s'%(s,chanToTest), solid_joinstyle ='round', solid_capstyle ='round', color=col, linestyle='-', marker='o')

        plRates.legend(loc='center right')

        if len(timeCourseVals[s])==len(volts):
            plTau.plot(volts, timeCourseVals[s], label='Time course of %s in %s'%(s,chanToTest), solid_joinstyle ='round', solid_capstyle ='round', color=col, linestyle='-', marker='o')

        plTau.legend(loc='center right')


    for s in states:
        file_name = "%s.%s.inf.dat"%(chanToTest, s)
        file = open(file_name, 'w')
        for i in range(len(volts)):
            file.write("%f\t%f\n"%(volts[i], steadyStateVals[s][i]))
        file.close()
        print("Written info to file: %s"%file_name)

        file_name = "%s.%s.tau.dat"%(chanToTest, s)
        file = open(file_name, 'w')
        for i in range(len(volts)):
            file.write("%f\t%f\n"%(volts[i], timeCourseVals[s][i]))
        file.close()
        print("Written info to file: %s"%file_name)
        
        
    if not args.nogui:
        plt.show()

    print "Done!"


if __name__ == '__main__':
    main()