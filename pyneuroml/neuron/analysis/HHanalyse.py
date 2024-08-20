#!/usr/bin/env python

"""
Implementation of the pynml-modchananalysis command
"""

import typing
import argparse
import logging
import re
import subprocess
import sys
from math import log

import matplotlib.pyplot as pylab
import neuron
from pylab import *
from pyneuroml.utils import get_state_color
from pyneuroml.utils.cli import build_namespace

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


DEFAULTS = {
    "v": False,
    "nogui": False,
    "minV": -100,
    "maxV": 100,
    "temperature": 6.3,
    "duration": 10000,
    "caConc": 5e-5,
    "dt": 0.01,
    "stepV": 10,
}


def process_args():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="A script which can be run in (Python enabled) NEURON to analyse the rate variables contained in a mod file"
    )

    parser.add_argument(
        "channel",
        type=str,
        metavar="<channel name>",
        help="Name of the channel as used by NEURON (i.e. in SUFFIX statement)",
    )

    parser.add_argument("-v", action="store_true", default=False, help="Verbose output")

    parser.add_argument(
        "-nogui",
        action="store_true",
        default=DEFAULTS["nogui"],
        help="Supress plotting of variables and only save to file",
    )

    parser.add_argument(
        "-savePlots",
        action="store_true",
        default=False,
        help="Export image (.png) of plotted figures to device",
    )

    parser.add_argument(
        "-minV",
        type=int,
        metavar="<min v>",
        default=DEFAULTS["minV"],
        help="Minimum voltage to test (integer, mV)",
    )

    parser.add_argument(
        "-maxV",
        type=int,
        metavar="<max v>",
        default=DEFAULTS["maxV"],
        help="Maximum voltage to test (integer, mV)",
    )

    parser.add_argument(
        "-stepV",
        type=int,
        metavar="<step v>",
        default=DEFAULTS["stepV"],
        help="Voltage step to use (integer, mV)",
    )

    parser.add_argument(
        "-dt",
        type=float,
        metavar="<time step>",
        default=DEFAULTS["dt"],
        help="Timestep for simulations, dt, in ms",
    )  # OR -1 for variable time step')

    parser.add_argument(
        "-duration",
        type=float,
        metavar="<duration>",
        default=DEFAULTS["duration"],
        help="Maximum duration of simulations, in ms",
    )

    parser.add_argument(
        "-temperature",
        type=str,
        metavar="<temperature>",
        default=DEFAULTS["temperature"],
        help="Temperature (float or list, e.g. [22,34], celsius)",
    )

    parser.add_argument(
        "-caConc",
        type=float,
        metavar="<Ca2+ concentration>",
        default=DEFAULTS["caConc"],
        help="Internal concentration of Ca2+ (float, concentration in mM)",
    )

    parser.add_argument(
        "-modFile",
        type=str,
        metavar="<name of mod file>",
        help="Name of the mod file containing the channel",
    )

    return parser.parse_args()


def remove_comments(txt):
    clear_txt = re.sub(r"(:.*)", "", txt)
    return clear_txt


def get_states(txt: str) -> typing.List[str]:
    """Get list of states from mod file text.

    :param txt: mod file text
    :type txt: str
    :returns: list of states (or empty list if no states found)
    :rtype: list(str)
    """
    state_list = []
    clear_txt = remove_comments(txt)
    state_grp = re.search(r"(?<=STATE)\s*\{(?P<st_txt>[^}]+)(?=\})", clear_txt)
    if state_grp is not None:
        state_txt = state_grp.group("st_txt")
        for state in re.finditer(r"(\w+)", state_txt):
            state_list.append(state.group(0))
        state_list = [x for x in state_list if x not in ["FROM", "0", "TO", "1"]]

    return state_list


def get_suffix(txt: str) -> typing.Optional[str]:
    """Get suffix mod file text

    :param txt: mod file text
    :type txt: str
    :returns: suffix string or None if not found
    :rtype: str
    """
    clear_txt = remove_comments(txt)
    res = re.search(r"NEURON\s*\{(\s*[\w+,]\s*)*\s\}?", clear_txt)
    if res is not None:
        nrn_str = res.group()

        res2 = re.search(r"(?<=SUFFIX)\s*(\w+)", nrn_str)
        if res2 is not None:
            sfx_str = res2.group(1)
            return sfx_str

    return None


def run(a=None, **kwargs):
    args = build_namespace(DEFAULTS, a, **kwargs)
    verbose = args.v

    # Get name of channel mechanism to test

    chanToTest = args.channel
    if verbose:
        logger.setLevel(logging.DEBUG)
    logger.info("Going to test channel: " + chanToTest)

    # Create the standard vars h, p for accessing hoc from Python & vice versa

    logger.info("Starting NEURON in Python mode...")
    h = neuron.h
    h.load_file("stdrun.hoc")
    h(
        """
    objref p
    p = new PythonObject()
    """
    )

    temperatures = []
    try:
        temperatures.append(float(args.temperature))
    except ValueError:
        # Assume list of form: [22,30,34]
        for temp in args.temperature[1:-1].split(","):
            temperatures.append(float(temp))

    # Create a section, set size & insert pas, passive channel mechanism

    sec = h.Section()

    sec.L = 10
    sec.nseg = 1
    for seg in sec:
        seg.diam = 5

    sec.insert("pas")
    sec(0.5).g_pas = 0.001
    sec(0.5).e_pas = -65

    ca_present = True
    try:
        sec.insert("ca_ion")
        sec(0.5).cai = args.ca_conc
    except ValueError:
        print("No Ca mechanism present...")
        ca_present = False

    # insert channel into section

    # Read state variables from mod file

    modFileName = chanToTest + ".mod"
    if args.mod_file:
        modFileName = args.mod_file
    with open(modFileName, "r") as handle:
        modFileTxt = handle.read()
    states = get_states(modFileTxt)
    logger.info("States found in mod file: " + str(states))

    if chanToTest != get_suffix(modFileTxt):
        logger.error("Channel name does not match suffix")
        quit()

    try:
        sec.insert(str(chanToTest))
    except ValueError:
        logger.info(
            f"{chanToTest} mechanism has not been compiled yet. Trying to run `nrnivmodl`."
        )
        try:
            subprocess.run("nrnivmodl", check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.error(
                f"Could not compile {modFileName}. nrivmodl returned {e.returncode}."
            )
            # print(e.stderr.decode())
            logger.error("Try running nrnivmodl manually and checking its output.")
            logger.error("Exiting...")
            return 1
        h.nrn_load_dll("x86_64/.libs/libnrnmech.so")
        sec.insert(str(chanToTest))

    for temperature in temperatures:
        h.celsius = temperature
        logger.info("Set temperature for simulation to: %s" % h.celsius)
        if ca_present:
            logger.info("[Ca2+] in section: %s" % sec(0.5).cai)

        # Settings for the voltage clamp test

        minV = args.min_v
        maxV = args.max_v
        interval = args.step_v
        volts = range(minV, maxV + interval, interval)

        v0 = -0.5  # Pre holding potential
        preHold = 50  # and duration
        postHoldStep = 10  # Post step holding time between steady state checks
        postHoldMax = args.duration  # Max sim run time

        timeToCheckTau = preHold + (10 * h.dt)

        steadyStateVals = {}
        timeCourseVals = {}
        for s in states:
            steadyStateVals[s] = []
            timeCourseVals[s] = []

        if verbose:
            figV = pylab.figure()
            pylab.get_current_fig_manager().set_window_title(
                "Membrane potentials for %s at %s degC" % (chanToTest, h.celsius)
            )
            plV = figV.add_subplot(111, autoscale_on=True)

            figR = pylab.figure()
            pylab.get_current_fig_manager().set_window_title(
                "Rate variables for %s at %s degC" % (chanToTest, h.celsius)
            )
            plR = figR.add_subplot(111, autoscale_on=True)

        for vh in volts:
            tstopMax = preHold + postHoldMax

            h("tstop = " + str(tstopMax))
            h.dt = args.dt

            if h.dt == -1:
                h.cvode.active(1)
                h.cvode.atol(0.0001)

            # Alternatively use a SEClamp obj
            clampobj = h.SEClamp(0.5)
            clampobj.dur1 = preHold
            clampobj.amp1 = v0
            clampobj.dur2 = postHoldMax
            clampobj.amp2 = vh
            clampobj.rs = 0.001

            tRec = []
            vRec = []
            rateRec = {}
            for s in states:
                rateRec[s] = []

            logger.info(
                "Starting simulation with channel %s of max time: %f, with holding potential: %f"
                % (chanToTest, tstopMax, vh)
            )
            # h.cvode.active(1)
            h.finitialize(v0)
            tolerance = 1e-5
            lastCheckTime = -1
            lastCheckVal = {}
            initSlopeVal = {}
            foundTau = []
            foundInf = []

            for s in states:
                lastCheckVal[s] = -1e-9
                initSlopeVal[s] = 1e9

            while len(foundInf) < len(states) or len(foundTau) < len(states):
                if h.t > tstopMax:
                    logger.error(
                        "\n**************************************\n*  Error! End of simulation reached before variable %s reached steady state!\n*  Consider using a longer duration (currently %s) with option: -duration\n**************************************\n"
                        % (s, args.duration)
                    )
                    quit()

                h.fadvance()
                tRec.append(h.t)
                vRec.append(sec(0.5).v)
                logger.debug(
                    "--- Time: %s; dt: %s; voltage %f; found Tau %s; found Inf %s"
                    % (h.t, h.dt, vh, foundTau, foundInf)
                )
                for s in states:
                    rateVal = eval("sec(0.5)." + s + "_" + chanToTest)
                    rateRec[s].append(float(rateVal))

                    if s not in foundTau:
                        if h.t >= preHold:
                            slope = (rateRec[s][-1] - rateRec[s][-2]) / h.dt
                            if initSlopeVal[s] == 0:
                                # print("\n**************************************\n*  Error! Initial slope of curve for state %s is 0\n*  Consider using a smaller dt (currently %s) with option: -dt\n**************************************\n"%(s, h.dt))
                                tau = 0
                                logger.debug(
                                    "        Found tau! Slope %s: %s, init: %s; at val: %s; time diff %s; fractOfInit: %s; log: %s; tau: %s"
                                    % (
                                        s,
                                        slope,
                                        initSlopeVal[s],
                                        rateVal,
                                        h.t - timeToCheckTau,
                                        fractOfInit,
                                        log(fractOfInit),
                                        tau,
                                    )
                                )
                                foundTau.append(s)
                                timeCourseVals[s].append(tau)
                            else:
                                fractOfInit = slope / initSlopeVal[s]
                                logger.debug(
                                    "        Slope of %s: %s (%s -> %s); init slope: %s; fractOfInit: %s; rateVal: %s"
                                    % (
                                        s,
                                        slope,
                                        rateRec[s][-2],
                                        rateRec[s][-1],
                                        initSlopeVal[s],
                                        fractOfInit,
                                        rateVal,
                                    )
                                )

                                if initSlopeVal[s] == 1e9 and h.t >= timeToCheckTau:
                                    initSlopeVal[s] = slope
                                    logger.debug(
                                        "        Init slope of %s: %s at val: %s; timeToCheckTau: %s"
                                        % (s, slope, rateVal, timeToCheckTau)
                                    )
                                elif initSlopeVal[s] != 1e9:
                                    if fractOfInit < 0.367879441:
                                        tau = (
                                            h.t - timeToCheckTau
                                        )  # / (-1*log(fractOfInit))
                                        logger.debug(
                                            "        Found tau! Slope %s: %s, init: %s; at val: %s; time diff %s; fractOfInit: %s; log: %s; tau: %s"
                                            % (
                                                s,
                                                slope,
                                                initSlopeVal[s],
                                                rateVal,
                                                h.t - timeToCheckTau,
                                                fractOfInit,
                                                log(fractOfInit),
                                                tau,
                                            )
                                        )
                                        foundTau.append(s)
                                        timeCourseVals[s].append(tau)
                                    else:
                                        logger.debug(
                                            "        Not yet fallen by 1/e: %s"
                                            % fractOfInit
                                        )

                if h.t >= preHold and h.t >= lastCheckTime + postHoldStep:
                    logger.debug(
                        "  - Time: %s; dt: %s; voltage %f; found Tau %s; found Inf %s"
                        % (h.t, h.dt, vh, foundTau, foundInf)
                    )

                    lastCheckTime = h.t

                    for s in states:
                        val = eval("sec(0.5)." + s + "_" + chanToTest)

                        if s not in foundInf:
                            rel_dif = (
                                (lastCheckVal[s] - val) / val
                                if val > sys.float_info.epsilon
                                else lastCheckVal[s]
                            )
                            if abs(rel_dif) > tolerance:
                                logger.debug(
                                    "  State %s has failed at %f; lastCheckVal[s] = %f; fract = %f; tolerance = %f"
                                    % (
                                        s,
                                        val,
                                        lastCheckVal[s],
                                        rel_dif,
                                        tolerance,
                                    )
                                )
                            else:
                                logger.debug(
                                    "  State %s has passed at %f; lastCheckVal[s] = %f; fract = %f; tolerance = %f"
                                    % (
                                        s,
                                        val,
                                        lastCheckVal[s],
                                        rel_dif,
                                        tolerance,
                                    )
                                )
                                foundInf.append(s)

                            lastCheckVal[s] = val

            logger.info(
                "    Finished run; t: %f, v: %f, vhold: %f, initSlopeVal: %s, timeCourses: %s ---  \n"
                % (h.t, sec(0.5).v, vh, str(initSlopeVal), str(timeCourseVals))
            )

            if verbose:
                plV.plot(
                    tRec,
                    vRec,
                    solid_joinstyle="round",
                    solid_capstyle="round",
                    color="#000000",
                    linestyle="-",
                    marker="None",
                )

            for s in states:
                col = get_state_color(s)
                if verbose:
                    plR.plot(
                        tRec,
                        rateRec[s],
                        solid_joinstyle="round",
                        solid_capstyle="round",
                        color=col,
                        linestyle="-",
                        marker="None",
                    )

            for s in states:
                val = eval("sec(0.5)." + s + "_" + chanToTest)
                steadyStateVals[s].append(val)

        figRates = pylab.figure()
        plRates = figRates.add_subplot(111, autoscale_on=True)
        pylab.get_current_fig_manager().set_window_title(
            "Steady state(s) of activation variables in %s at %s degC"
            % (chanToTest, h.celsius)
        )
        plRates.set_xlabel("Membrane potential (mV)")
        plRates.set_ylabel("Steady state - inf")
        pylab.grid("on")

        figTau = pylab.figure()
        pylab.get_current_fig_manager().set_window_title(
            "Time course(s) of activation variables in %s at %s degC"
            % (chanToTest, h.celsius)
        )
        plTau = figTau.add_subplot(111, autoscale_on=True)
        plTau.set_xlabel("Membrane potential (mV)")
        plTau.set_ylabel("Time Course - tau (ms)")
        pylab.grid("on")

        for s in states:
            col = get_state_color(s)
            plRates.plot(
                volts,
                steadyStateVals[s],
                label="%s %s inf" % (chanToTest, s),
                solid_joinstyle="round",
                solid_capstyle="round",
                color=col,
                linestyle="-",
                marker="o",
            )
            plRates.legend()

            if len(timeCourseVals[s]) == len(volts):
                plTau.plot(
                    volts,
                    timeCourseVals[s],
                    label="%s %s tau" % (chanToTest, s),
                    solid_joinstyle="round",
                    solid_capstyle="round",
                    color=col,
                    linestyle="-",
                    marker="o",
                )

            plTau.legend()

        temp_info = ""
        if len(temperatures) > 1:
            if temperature == int(temperature):
                temp_info = ".%i" % temperature
            else:
                temp_info = ".%s" % temperature

        for s in states:
            file_name = "%s.%s.inf%s.dat" % (chanToTest, s, temp_info)
            file = open(file_name, "w")
            for i in range(len(volts)):
                file.write("%f\t%f\n" % (volts[i], steadyStateVals[s][i]))
            file.close()
            logger.info("Written info to file: %s" % file_name)

            file_name = "%s.%s.tau%s.dat" % (chanToTest, s, temp_info)
            file = open(file_name, "w")
            for i in range(len(volts)):
                file.write("%f\t%f\n" % (volts[i], timeCourseVals[s][i]))
            file.close()
            logger.info("Written info to file: %s" % file_name)

    if args.save_plots:
        figs = pylab.get_fignums()

        for fig in figs:
            pylab.figure(fig)
            window_title = pylab.get_current_fig_manager().get_window_title()
            file_name = f"{window_title}.png"
            plt.savefig(file_name)
            logger.info("Exported img to file: %s" % file_name)

    if not args.nogui:
        pylab.show()

    logger.info("Done!")


def main(args=None):
    if args is None:
        args = process_args()
    run(a=args)


if __name__ == "__main__":
    main()
