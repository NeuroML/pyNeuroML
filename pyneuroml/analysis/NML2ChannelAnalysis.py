#!/usr/bin/env python
#
#   A script which can be run to generate a LEMS file to analyse the behaviour
#   of channels in NeuroML 2
#

import argparse
import logging
import os
import os.path
import pprint
import sys
import typing

import airspeed
import matplotlib.pyplot as plt
import neuroml

from pyneuroml.pynml import read_neuroml2_file, run_lems_with_jneuroml
from pyneuroml.utils import get_colour_hex, get_ion_color, get_state_color
from pyneuroml.utils.cli import build_namespace

logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(depth=4)

OUTPUT_DIR = os.getcwd()
TEMPLATE_FILE = "%s/LEMS_Test_TEMPLATE.xml" % (os.path.dirname(__file__))

HTML_TEMPLATE_FILE = "%s/ChannelInfo_TEMPLATE.html" % (os.path.dirname(__file__))
MD_TEMPLATE_FILE = "%s/ChannelInfo_TEMPLATE.md" % (os.path.dirname(__file__))

V = "rampCellPop0[0]/v"  # Key for voltage trace in results dictionary.

DEFAULTS = {
    "v": False,
    "minV": -100,
    "maxV": 100,
    "temperature": 6.3,
    "duration": 100,
    "clampDelay": 10,
    "clampDuration": 80,
    "clampBaseVoltage": -70,
    "stepTargetVoltage": 20,
    "erev": 0,
    "scaleDt": 1,
    "caConc": 5e-5,
    "datSuffix": "",
    "ivCurve": False,
    "norun": False,
    "nogui": False,
    "html": False,
    "md": False,
}


def process_args():
    """Parse command-line arguments.

    :returns: None
    """
    parser = argparse.ArgumentParser(
        description=(
            "A script which can be run to generate a LEMS "
            "file to analyse the behaviour of channels in "
            "NeuroML 2"
        )
    )

    parser.add_argument(
        "channelFiles",
        type=str,
        nargs="+",
        metavar="<NeuroML 2 Channel file>",
        help="Name of the NeuroML 2 file(s)",
    )

    parser.add_argument(
        "-v", action="store_true", default=DEFAULTS["v"], help="Verbose output"
    )

    parser.add_argument(
        "-minV",
        type=int,
        metavar="<min v>",
        default=DEFAULTS["minV"],
        help="Minimum voltage to test (integer, mV), default: %smV" % DEFAULTS["minV"],
    )

    parser.add_argument(
        "-maxV",
        type=int,
        metavar="<max v>",
        default=DEFAULTS["maxV"],
        help="Maximum voltage to test (integer, mV), default: %smV" % DEFAULTS["maxV"],
    )

    parser.add_argument(
        "-temperature",
        type=float,
        metavar="<temperature>",
        default=DEFAULTS["temperature"],
        help="Temperature (float, celsius), default: %sdegC" % DEFAULTS["temperature"],
    )

    parser.add_argument(
        "-duration",
        type=float,
        metavar="<duration>",
        default=DEFAULTS["duration"],
        help="Duration of simulation in ms, default: %sms" % DEFAULTS["duration"],
    )

    parser.add_argument(
        "-clampDelay",
        type=float,
        metavar="<clamp delay>",
        default=DEFAULTS["clampDelay"],
        help="Delay before voltage clamp is activated in ms, default: %sms"
        % DEFAULTS["clampDelay"],
    )

    parser.add_argument(
        "-clampDuration",
        type=float,
        metavar="<clamp duration>",
        default=DEFAULTS["clampDuration"],
        help="Duration of voltage clamp in ms, default: %sms"
        % DEFAULTS["clampDuration"],
    )

    parser.add_argument(
        "-clampBaseVoltage",
        type=float,
        metavar="<clamp base voltage>",
        default=DEFAULTS["clampBaseVoltage"],
        help="Clamp base (starting/finishing) voltage in mV, default: %smV"
        % DEFAULTS["clampBaseVoltage"],
    )

    parser.add_argument(
        "-stepTargetVoltage",
        type=float,
        metavar="<step target voltage>",
        default=DEFAULTS["stepTargetVoltage"],
        help=(
            "Voltage in mV through which to step voltage clamps, default: %smV"
            % DEFAULTS["stepTargetVoltage"]
        ),
    )

    parser.add_argument(
        "-erev",
        type=float,
        metavar="<reversal potential>",
        default=DEFAULTS["erev"],
        help="Reversal potential of channel for currents, default: %smV"
        % DEFAULTS["erev"],
    )

    parser.add_argument(
        "-scaleDt",
        type=float,
        metavar="<scale dt in generated LEMS>",
        default=DEFAULTS["scaleDt"],
        help="Scale dt in generated LEMS, default: %s" % DEFAULTS["scaleDt"],
    )

    parser.add_argument(
        "-caConc",
        type=float,
        metavar="<Ca2+ concentration>",
        default=DEFAULTS["caConc"],
        help=(
            "Internal concentration of Ca2+ (float, "
            "concentration in mM), default: %smM" % DEFAULTS["caConc"]
        ),
    )

    parser.add_argument(
        "-datSuffix",
        type=str,
        metavar="<dat suffix>",
        default=DEFAULTS["datSuffix"],
        help="String to add to dat file names (before .dat)",
    )

    parser.add_argument(
        "-norun",
        action="store_true",
        default=DEFAULTS["norun"],
        help=("If used, just generate the LEMS file, " "don't run it"),
    )

    parser.add_argument(
        "-nogui",
        action="store_true",
        default=DEFAULTS["nogui"],
        help=("Supress plotting of variables and only save " "data to file"),
    )

    parser.add_argument(
        "-html",
        action="store_true",
        default=DEFAULTS["html"],
        help=("Generate a HTML page featuring the plots for the " "channel"),
    )

    parser.add_argument(
        "-md",
        action="store_true",
        default=DEFAULTS["md"],
        help=(
            "Generate a (GitHub flavoured) Markdown page featuring the plots for the "
            "channel"
        ),
    )

    parser.add_argument(
        "-ivCurve",
        action="store_true",
        default=DEFAULTS["ivCurve"],
        help=(
            "Save currents through voltage clamp at each "
            "level & plot current vs voltage for ion "
            "channel"
        ),
    )

    return parser.parse_args()


def merge_with_template(
    model: typing.Dict[typing.Any, typing.Any], templfile: str
) -> str:
    """Merge model information with airspeed template.

    :param model: model information
    :type model: dict
    :param templfile: name of airspeed template file
    :type templfile: string
    :returns: merged template string
    :rtype: str
    """
    if not os.path.isfile(templfile):
        templfile = os.path.join(os.path.dirname(sys.argv[0]), templfile)
    with open(templfile) as f:
        templ = airspeed.Template(f.read())
    return templ.merge(model)


def generate_lems_channel_analyser(
    channel_file: str,
    channel: str,
    min_target_voltage: float,
    step_target_voltage: float,
    max_target_voltage: float,
    clamp_delay: float,
    clamp_duration: float,
    clamp_base_voltage: float,
    duration: float,
    erev: float,
    gates: typing.List[str],
    temperature: float,
    ca_conc: float,
    iv_curve: bool,
    scale_dt: float = 1,
    dat_suffix: str = "",
    verbose: bool = True,
):
    """Generate analysis simulation LEMS file.

    :param channel_file: path to channel file
    :type channel_file: str
    :param channel: name of channel
    :type channel: string
    :param min_target_voltage: magnitude of minimum target voltage in mV
    :type min_target_voltage: float
    :param max_target_voltage: magnitude of maximum target voltage in mV
    :type max_target_voltage: float
    :param clamp_delay: magnitude of delay for clamp in ms
    :type clamp_delay: float
    :param clamp_duration: magnitude of duration of clamp in ms
    :type clamp_delay: float
    :param clamp_base_voltage: magnitude of base voltage of clamp in mV
    :type clamp_base_voltage: float
    :param duration: magnitude of duration of simulation in ms
    :type duration: float
    :param erev: magnitude of reversal potential in mV
    :type erev: float
    :param gates: list of gates
    :type gates: list of str
    :param temperature: magnitude of temperature in degC
    :type temperature: float
    :param ca_conc: magnitude of calcium concentration in mM
    :type ca_conc: float
    :param iv_curve: toggle whether to plot iv curve
    :type iv_curve: bool
    :param scale_dt: magnitude to scale dt by in ms
    :type scale_dt: float
    :param dat_suffix: suffix of data file
    :type dat_suffix: str
    :param verbose: toggle verbosity
    :type verbose: bool
    """

    logger.info(
        ("Generating LEMS file to investigate %s in %s, %smV->%smV, " "%sdegC")
        % (channel, channel_file, min_target_voltage, max_target_voltage, temperature)
    )

    target_voltages = []
    v = min_target_voltage
    while v <= max_target_voltage:
        target_voltages.append(v)
        v += step_target_voltage

    target_voltages_map = []
    for t in target_voltages:
        fract = float(target_voltages.index(t)) / (len(target_voltages) - 1)
        info = {}  # type: typing.Dict[typing.Any, typing.Any]
        info["v"] = t
        info["v_str"] = str(t).replace("-", "min")
        info["col"] = get_colour_hex(fract)
        target_voltages_map.append(info)

    includes = get_includes_from_channel_file(channel_file)
    includes_relative = []
    base_path = os.path.dirname(channel_file)
    for inc in includes:
        includes_relative.append(os.path.abspath(base_path + "/" + inc))

    model = {
        "channel_file": channel_file,
        "includes": includes_relative,
        "channel": channel,
        "target_voltages": target_voltages_map,
        "clamp_delay": clamp_delay,
        "clamp_duration": clamp_duration,
        "clamp_base_voltage": clamp_base_voltage,
        "min_target_voltage": min_target_voltage,
        "max_target_voltage": max_target_voltage,
        "duration": duration,
        "scale_dt": scale_dt,
        "erev": erev,
        "gates": gates,
        "temperature": temperature,
        "ca_conc": ca_conc,
        "iv_curve": iv_curve,
        "dat_suffix": dat_suffix,
    }

    # pp.pprint(model)

    merged = merge_with_template(model, TEMPLATE_FILE)

    return merged


def get_channels_from_channel_file(
    channel_file: str,
) -> typing.List[typing.Union[neuroml.IonChannelHH, neuroml.IonChannel]]:
    """Get IonChannelHH and IonChannel instances from a NeuroML channel file.

    :param channel_file: complete path to a channel file
    :type channel_file: str
    :returns: list of channels
    :rtype: list
    :raises ValueError: if no channels were found in the file
    """
    doc = read_neuroml2_file(
        channel_file, include_includes=True, verbose=False, already_included=[]
    )
    channels = (
        list(doc.ion_channel_hhs.__iter__())
        + list(doc.ion_channel.__iter__())
        + list(doc.ion_channel_v_shifts.__iter__())
    )

    if len(channels) == 0:
        raise ValueError(f"No channels found in {channel_file}")

    for channel in channels:
        setattr(channel, "file", channel_file)
        if not hasattr(channel, "notes"):
            setattr(channel, "notes", "")

    return channels


def get_includes_from_channel_file(
    channel_file: str,
) -> typing.List[neuroml.IncludeType]:
    """Get includes from a NeuroML channel file

    :param channel_file: complete path to a channel file
    :type channel_file: str
    :returns: list of includes
    :rtype: list
    """
    doc = read_neuroml2_file(channel_file)
    includes = []
    for incl in doc.includes:
        includes.append(incl.href)
    return includes


def process_channel_file(channel_file: str, a) -> typing.List[typing.Any]:
    """Process the channel file.

    :param channel_file: complete path to channel file
    :type channel_file: str
    :param a: argparse.Namespace instance holding all arguments
    :type a: argparse.Namsepace
    :returns: list of channel information
    :rtype: list
    :raises IOError: if channel file could not be found
    """
    # Get name of channel mechanism to test
    if a.v:
        logger.info("Going to test channel from file: " + channel_file)

    if not os.path.isfile(channel_file):
        raise IOError("File could not be found: %s!\n" % channel_file)

    channels = get_channels_from_channel_file(channel_file)

    channels_info = []
    for channel in channels:
        if len(get_channel_gates(channel)) == 0:
            logger.warning(
                "Skipping %s in %s as it has no channels (probably passive conductance)"
                % (channel.id, channel_file)
            )
        else:
            new_lems_file = make_lems_file(channel, a)
            if not a.norun:
                results = run_lems_file(new_lems_file, a.v)

            if a.iv_curve:
                iv_data = compute_iv_curve(channel, a, results)
            else:
                iv_data = None

            if not a.nogui and not a.norun:
                plot_channel(channel, a, results, iv_data=iv_data)

            channel_info = {
                key: getattr(channel, key) for key in ["id", "file", "notes", "species"]
            }

            channel_info["expression"] = get_conductance_expression(channel)
            channel_info["ion_color"] = get_ion_color(channel.species)

            channels_info.append(channel_info)
    return channels_info


def get_channel_gates(
    channel: typing.Union[neuroml.IonChannel, neuroml.IonChannelHH],
) -> typing.List[
    typing.Union[
        neuroml.GateHHUndetermined,
        neuroml.GateHHRates,
        neuroml.GateHHTauInf,
        neuroml.GateHHInstantaneous,
    ]
]:
    """Get gates in a channel

    :param channel: channel object
    :type channel: neuroml.IonChannel, neuroml.IonChannelHH
    :returns: list of gates
    :rtype: list
    """
    channel_gates = []
    for gates in [
        "gates",
        "gate_hh_rates",
        "gate_hh_tau_infs",
        "gate_hh_instantaneouses",
        "gate_fractionals",
    ]:
        if hasattr(channel, gates):
            if gates == "gate_fractionals":
                for g in getattr(channel, gates):
                    for sg in g.sub_gates:
                        channel_gates.append(str("%s/%s" % (g.id, sg.id)))
            else:
                for g in getattr(channel, gates):
                    channel_gates.append(g.id)
    # print('- Found gates: %s'%channel_gates)
    return channel_gates


def get_ks_channel_states(
    channel: neuroml.IonChannelKS,
) -> typing.Dict[str, typing.List[str]]:
    """Get states for a kinetic state style ion channel

    .. versionadded:: 1.2.15

    :param channel: kinetic state style channel to get states from
    :type channel: neuroml.IonChannelKS
    :returns: dict with gate id as key, and list of states as value
    """
    info = {}
    for gate_ks in channel.gate_kses:
        info[gate_ks.id] = [s.id for s in gate_ks.closed_states] + [
            s.id for s in gate_ks.open_states
        ]

    return info


def get_conductance_expression(
    channel: typing.Union[neuroml.IonChannel, neuroml.IonChannelHH],
) -> str:
    """Get expression of conductance in channel.

    :param channel: channel object
    :type channel: neuroml.IonChannel, neuroml.IonChannelHH
    :returns: expression for conductance of channel.
    :rtype: str
    """
    expr = "g = gmax "
    for gates in [
        "gates",
        "gate_hh_rates",
        "gate_hh_tau_infs",
        "gate_hh_instantaneouses",
    ]:
        for g in getattr(channel, gates):
            instances = int(g.instances)
            expr += (
                "* %s<sup>%s</sup> " % (g.id, g.instances)
                if instances > 1
                else "* %s " % (g.id)
            )
    return expr


def make_lems_file(channel, a):
    gates = get_channel_gates(channel)
    lems_content = generate_lems_channel_analyser(
        channel.file,
        channel.id,
        a.min_v,
        a.step_target_voltage,
        a.max_v,
        a.clamp_delay,
        a.clamp_duration,
        a.clamp_base_voltage,
        a.duration,
        a.erev,
        gates,
        a.temperature,
        a.ca_conc,
        a.iv_curve,
        scale_dt=a.scale_dt,
        dat_suffix=a.dat_suffix,
        verbose=a.v,
    )
    new_lems_file = os.path.join(OUTPUT_DIR, "LEMS_Test_%s.xml" % channel.id)
    lf = open(new_lems_file, "w")
    lf.write(lems_content)
    lf.close()
    if a.v:
        logger.info("Written generated LEMS file to %s\n" % new_lems_file)
    return new_lems_file


def run_lems_file(lems_file, verbose):
    results = run_lems_with_jneuroml(
        lems_file, nogui=True, load_saved_data=True, plot=False, verbose=verbose
    )
    return results


def plot_channel(channel, a, results, iv_data=None, grid=True):
    plot_kinetics(channel, a, results, grid=grid)
    plot_steady_state(channel, a, results, grid=grid)
    if iv_data:
        plot_iv_curves(channel, a, iv_data)


def plot_kinetics(channel, a, results, grid=True):
    plt.figure()
    plt.get_current_fig_manager().set_window_title(
        ("Time course(s) of activation variables of " "%s from %s at %s degC")
        % (channel.id, channel.file, a.temperature)
    )

    plt.xlabel("Membrane potential (mV)")
    plt.ylabel("Time Course - tau (ms)")
    plt.grid("on" if grid else "off")

    t0 = 1e6
    t1 = -1e6
    gates = get_channel_gates(channel)

    for g in gates:
        g_tau = "rampCellPop0[0]/test/%s/%s/tau" % (
            channel.id,
            g,
        )  # Key for conductance variable.
        col = get_state_color(g)
        plt.plot(
            [v * 1000 for v in results[V]],
            [t * 1000 for t in results[g_tau]],
            color=col,
            linestyle="-",
            label="%s %s tau" % (channel.id, g),
        )
        plt.xlim([results[V][0] * 1100, results[V][-1] * 1100])
        t0 = min(t0, min(results[g_tau]) * 1000)
        t1 = max(t1, max(results[g_tau]) * 1000)

    if t0 == t1:
        t0 = 0
    plt.ylim([t0 - ((t1 - t0) / 10), t1 + ((t1 - t0) / 10)])

    leg = plt.legend(fancybox=True)
    leg.get_frame().set_alpha(0.5)

    if a.html or a.md:
        save_fig("%s.tau.png" % channel.id)


def plot_steady_state(channel, a, results, grid=True):
    plt.figure()
    plt.get_current_fig_manager().set_window_title(
        ("Steady state(s) of activation variables of " "%s from %s at %s degC")
        % (channel.id, channel.file, a.temperature)
    )
    plt.xlabel("Membrane potential (mV)")
    plt.ylabel("Steady state - inf")
    plt.grid("on" if grid else "off")

    gates = get_channel_gates(channel)
    for g in gates:
        g_inf = "rampCellPop0[0]/test/%s/%s/inf" % (channel.id, g)
        col = get_state_color(g)
        plt.plot(
            [v * 1000 for v in results[V]],
            results[g_inf],
            color=col,
            linestyle="-",
            label="%s %s inf" % (channel.id, g),
        )

    plt.xlim([results[V][0] * 1100, results[V][-1] * 1100])
    plt.ylim([-0.05, 1.05])
    leg = plt.legend(fancybox=True, loc="center right")
    leg.get_frame().set_alpha(0.5)

    if a.html or a.md:
        save_fig("%s.inf.png" % channel.id)


def save_fig(name):
    overview_dir = make_overview_dir()
    png_path = os.path.join(overview_dir, name)
    plt.savefig(png_path, bbox_inches="tight")


def make_overview_dir():
    overview_dir = os.path.join(OUTPUT_DIR, "channel_summary")
    if not os.path.isdir(overview_dir):
        os.makedirs(overview_dir)
    return overview_dir


def compute_iv_curve(channel, a, results, grid=True):
    # Based on work by Rayner Lucas here:
    # https://github.com/openworm/
    # BlueBrainProjectShowcase/blob/master/
    # Channelpedia/iv_analyse.py
    end_time_ms = a.clamp_delay + a.clamp_duration
    i_peak = {}
    i_steady = {}
    hold_v = []
    currents = {}
    times = {}

    for r in results:
        # e.g. r = holderCellPop_min10.0[0]/test/i
        if "holderCellPop" in r:
            voltage = r.split("_")[1].split("[")[0]
            voltage = voltage.replace("min", "-")
            voltage = float(voltage) / 1000
            hold_v.append(voltage)
            times[voltage] = []

            currents[voltage] = []
            i_max = -1 * sys.float_info.min
            i_min = sys.float_info.min
            i_steady[voltage] = None
            t_start = a.clamp_delay / 1000.0
            t_steady_end = end_time_ms / 1000.0

            logger.info(
                "Looking at holding voltage %s V, and currents between times %s s and %s s"
                % (voltage, t_start, t_steady_end)
            )

            for index in range(len(results["t"])):
                i = results[r][index]
                t = results["t"][index]
                times[voltage].append(t)
                currents[voltage].append(i)
                if t >= t_start and t <= t_steady_end:
                    if i > i_max:
                        i_max = i
                    if i < i_min:
                        i_min = i

                    i_steady[voltage] = -1 * i  # will be set to last value...

            i_peak_ = i_max if abs(i_max) > abs(i_min) else i_min
            i_peak[voltage] = -1 * i_peak_

    hold_v.sort()

    iv_file = open("%s.i_peak.dat" % channel.id, "w")
    for v in hold_v:
        iv_file.write("%s\t%s\n" % (v, i_peak[v]))
    iv_file.close()

    iv_file = open("%s.i_steady.dat" % channel.id, "w")
    for v in hold_v:
        iv_file.write("%s\t%s\n" % (v, i_steady[v]))
    iv_file.close()

    items = ["hold_v", "times", "currents", "i_steady", "i_peak"]
    locals_ = locals().copy()
    iv_data = {item: locals_[item] for item in items}
    return iv_data


def plot_iv_curves(channel, a, iv_data, grid=True):
    x = iv_data
    plot_iv_curve_vm(channel, a, x["hold_v"], x["times"], x["currents"], grid=grid)
    plot_iv_curve(a, x["hold_v"], x["i_peak"], grid=grid, label="Peak currents")
    plot_iv_curve(
        a, x["hold_v"], x["i_steady"], grid=grid, label="Steady state currents"
    )


def plot_iv_curve_vm(channel, a, hold_v, times, currents, grid=True):
    # Holding potentials
    plt.figure()
    ax = plt.subplot(111)
    plt.get_current_fig_manager().set_window_title(
        ("Currents through voltage clamp for %s " "from %s at %s degC, erev: %s V")
        % (channel.id, channel.file, a.temperature, a.erev)
    )
    plt.xlabel("Time (ms)")
    plt.ylabel("Current (pA)")
    plt.grid("on" if grid else "off")
    for v in hold_v:
        col = get_colour_hex(float(hold_v.index(v)) / len(hold_v))

        plt.plot(
            [t * 1000 for t in times[v]],
            [i * 1e12 for i in currents[v]],
            color=col,
            linestyle="-",
            label="%s mV" % (v * 1000),
        )

    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    # Put a legend to the right of the current axis
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))


def make_iv_curve_fig(a, grid=True):
    plt.figure()
    plt.get_current_fig_manager().set_window_title(
        "Currents vs. holding potentials at erev = %s V" % a.erev
    )
    plt.xlabel("Membrane potential (mV)")
    plt.ylabel("Current (pA)")
    plt.grid("on" if grid else "off")


def plot_iv_curve(a, hold_v, i, *plt_args, **plt_kwargs):
    """A single IV curve"""
    grid = plt_kwargs.pop("grid", True)
    same_fig = plt_kwargs.pop("same_fig", False)
    if not len(plt_args):
        plt_args = ("ko-",)
    if "label" not in plt_kwargs:
        plt_kwargs["label"] = "Current"
    if not same_fig:
        make_iv_curve_fig(a, grid=grid)
    if isinstance(i, dict):
        i = [i[v] for v in hold_v]
    plt.plot(
        [v * 1e3 for v in hold_v], [ii * 1e12 for ii in i], *plt_args, **plt_kwargs
    )
    plt.legend(loc=2)


def make_html_file(info):
    merged = merge_with_template(info, HTML_TEMPLATE_FILE)
    html_dir = make_overview_dir()
    new_html_file = os.path.join(html_dir, "ChannelInfo.html")
    lf = open(new_html_file, "w")
    lf.write(merged)
    lf.close()
    logger.info("Written HTML info to: %s" % new_html_file)


def make_md_file(info):
    merged = merge_with_template(info, MD_TEMPLATE_FILE)
    md_dir = make_overview_dir()
    new_md_file = os.path.join(md_dir, "README.md")
    lf = open(new_md_file, "w")
    lf.write(merged)
    lf.close()
    logger.info("Written Markdown info to: %s" % new_md_file)


def main(args=None):
    if args is None:
        args = process_args()
    run(a=args)


def run(a=None, **kwargs):
    a = build_namespace(DEFAULTS, a, **kwargs)

    # if (not a.nogui) or a.html:
    #    print('mpl')

    info = {
        "info": (
            "Channel information at: "
            "T = %s degC, "
            "E_rev = %s mV, "
            "[Ca2+] = %s mM"
        )
        % (a.temperature, a.erev, a.ca_conc),
        "channels": [],
    }

    na_chan_files = []
    k_chan_files = []
    ca_chan_files = []
    other_chan_files = []

    if len(a.channel_files) > 0:
        for channel_file in a.channel_files:
            channels = get_channels_from_channel_file(channel_file)
            # TODO look past 1st channel...
            if channels[0].species == "na":
                na_chan_files.append(channel_file)
            elif channels[0].species == "k":
                k_chan_files.append(channel_file)
            elif channels[0].species == "ca":
                ca_chan_files.append(channel_file)
            else:
                other_chan_files.append(channel_file)

    channel_files = na_chan_files + k_chan_files + ca_chan_files + other_chan_files
    logger.info("\nAnalysing channels from files: %s\n" % channel_files)

    for channel_file in channel_files:
        channels_info = process_channel_file(channel_file, a)
        for channel_info in channels_info:
            info["channels"].append(channel_info)

    if not a.nogui and not a.html and not a.md:
        plt.show()
    else:
        if a.html:
            make_html_file(info)
        if a.md:
            make_md_file(info)


if __name__ == "__main__":
    main()
