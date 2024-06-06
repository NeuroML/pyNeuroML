# A parser for XPPAUT files. The dictionary structure of the XPP can then be
# mapped to other formats such as LEMS

import argparse
import logging
import os
import typing
from pprint import pprint

from pyneuroml.utils.cli import build_namespace

XPP_TIME = "xpp_time"
LEMS_TIME = "t"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

verbose = False

temp_var_count = 0


def get_new_temp_var():
    global temp_var_count
    tv = "TMP__%i" % temp_var_count
    temp_var_count += 1
    return tv


def _closing_bracket_index(expr, open_bracket_index):
    depth = 0
    logger.debug(
        "Looking for closing bracket of %s from %i, i.e. %s"
        % (expr, open_bracket_index, expr[open_bracket_index:])
    )
    for i in range(open_bracket_index + 1, len(expr)):
        if expr[i] == "(":
            depth += 1
        if expr[i] == ")":
            if depth == 0:
                if verbose:
                    logger.debug(
                        "++++++found at %i: %s" % (i, expr[open_bracket_index : i + 1])
                    )
                return i
            else:
                depth -= 1
    raise Exception("Not found!")


def _split_if_then_else(expr):
    logger.debug("Splitting: %s" % expr)
    cond_end = _closing_bracket_index(expr, 2)
    condition = expr[3:cond_end]
    true_start = cond_end + 5
    true_end = _closing_bracket_index(expr, true_start)
    value_true = expr[true_start + 1 : true_end]
    false_start = true_end + 5
    false_end = _closing_bracket_index(expr, false_start)
    value_false = expr[false_start + 1 : false_end]

    return {
        "condition": condition,
        "value_true": value_true,
        "value_false": value_false,
    }


def _add_cond_deriv_var():
    pass


INBUILT = {"pi": 3.14159265359}


def parse_script(file_path):
    data = {
        "comments": [],
        "parameters": dict(INBUILT),
        "functions": {},
        "derived_variables": {},
        "conditional_derived_variables": {},
        "time_derivatives": {},
        "initial_values": {},
        "settings": {},
        "unhandled": [],
    }

    with open(file_path, "r") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            logger.debug("--- Parsing line: %s" % line)

            # Handle comments
            if line.startswith("#"):
                c = line[1:].strip()
                if len(c) > 0:
                    data["comments"].append(c)

            # Handle parameter declarations
            elif line.startswith(("number", "p", "par", "param")):
                params = (
                    line.replace("number ", "")
                    .replace("par ", "")
                    .replace("p ", "")
                    .replace("param ", "")
                )  # Skip the first word ('number', 'p', 'param' or 'par')
                for pp1 in params.split(","):
                    pp1 = (
                        pp1.replace(" = ", "=").replace("= ", "=").replace(" =", "=")
                    )  # better solution required...
                    for pp2 in pp1.split(" "):
                        if len(pp2) > 0:
                            key, value = pp2.split("=")
                            data["parameters"][key.strip()] = float(value.strip())

            # Handle init declarations
            elif line.startswith(("init")):
                inits = line[5:]
                for pp in inits.split(","):
                    if len(pp) > 0:
                        key, value = pp.split("=")
                        data["initial_values"][key.strip()] = float(value.strip())

            # Handle function and initial value declarations
            elif "=" in line and not line.startswith("@"):
                key, value = line.split("=", 1)

                logger.debug("  --- Parsing equality: %s = %s" % (key, value))

                if "'" in key:
                    # derivative
                    var_name = key.split("'")[0].strip()
                    data["time_derivatives"][var_name] = value.strip()
                elif "/dt" in key:
                    # derivative
                    var_name = key.strip()[1:-3]
                    data["time_derivatives"][var_name] = value.strip()
                    logger.debug(var_name)
                elif "[0]" in key or "(0)" in key:
                    # Initial value
                    var_name = key.split("[")[0].split("(")[0].strip()
                    data["initial_values"][var_name] = float(value.strip())
                elif "(" in key:
                    # Function definition
                    func_name = key.split("(")[0].strip()
                    func_args = key.split("(")[1].split(")")[0].strip().split(",")
                    data["functions"][func_name] = {}
                    data["functions"][func_name]["arguments"] = func_args
                    data["functions"][func_name]["value"] = value.strip()
                else:
                    # "Normal" variable...
                    expr = value.strip()

                    #### This should be refactored to make it 'infinitely' recursive...
                    if "if" in expr and "else" in expr:
                        var_0 = key.strip()
                        ite_0 = _split_if_then_else(expr)

                        if "if" in ite_0["value_true"]:
                            ite_1 = _split_if_then_else(ite_0["value_true"])
                            new_var_name1 = get_new_temp_var()

                            if "if" in ite_1["value_false"]:
                                ite_2 = _split_if_then_else(ite_1["value_false"])
                                new_var_name2 = get_new_temp_var()

                                if "if" in ite_2["value_true"]:
                                    ite_3 = _split_if_then_else(ite_2["value_true"])
                                    new_var_name3 = get_new_temp_var()

                                    data["conditional_derived_variables"][
                                        new_var_name3
                                    ] = ite_3
                                    ite_2["value_true"] = new_var_name3

                                data["conditional_derived_variables"][new_var_name2] = (
                                    ite_2
                                )
                                ite_1["value_false"] = new_var_name2

                            data["conditional_derived_variables"][var_0] = ite_0
                            data["conditional_derived_variables"][new_var_name1] = ite_1
                            ite_0["value_true"] = new_var_name1

                        data["conditional_derived_variables"][var_0] = ite_0
                    else:
                        k = key.strip()
                        if " " in k:
                            ks = k.split()
                            if ks[0] == "aux":
                                k = ks[1]
                            else:
                                raise ValueError(f"Unable to parse line: {line}")

                        if not k == expr:
                            data["derived_variables"][k] = expr

            # Handle done
            elif line == "done":
                pass

            # Handle settings
            elif line.startswith("@"):
                settings = line[1:].strip()
                for sss in settings.split(" "):
                    for ss in sss.split(","):
                        if len(ss) > 0:
                            key, value = ss.split("=")
                            data["settings"][key.strip().lower()] = value.strip()

            else:
                data["unhandled"].append(line)

    return data


def substitute_functions(expr, functions):
    import re

    for func_name, func_def in functions.items():
        # logger.debug('  - Function %s, replacing %s in <%s>'%(func_name, func_def,expr))
        # Find all occurrences of the function in the expression
        pattern = rf"{func_name}\(([^)]+)\)"
        matches = re.findall(pattern, expr)

        for match in matches:
            args_in_expr = match.split(",")
            if len(args_in_expr) != len(func_def["arguments"]):
                raise ValueError(
                    f"Incorrect number of arguments for function {func_name}"
                )

            # Map the arguments in the expression to the function definition
            substitution = func_def["value"]
            for def_arg, expr_arg in zip(func_def["arguments"], args_in_expr):
                substitution = substitution.replace(def_arg, expr_arg.strip())
                # logger.debug('    - replacing <%s> by <%s> - <%s>'%(def_arg, expr_arg.strip(), substitution))

            # Replace the function call with the substitution
            expr = expr.replace(f"{func_name}({match})", "(%s)" % substitution)

        # logger.debug('  - Expr now: <%s>'%(expr))
    return expr


def to_xpp(data, new_xpp_filename):
    xpp_ode = ""

    xpp_ode += "\n# Parameters\n"
    for k, v in data["parameters"].items():
        if k not in INBUILT.keys():
            xpp_ode += f"par {k} = {v}\n"

    xpp_ode += "\n# Functions\n"
    for k, v in data["functions"].items():
        xpp_ode += f"{k}("
        for a in v["arguments"]:
            xpp_ode += "%s," % a
        xpp_ode = xpp_ode[:-1]
        xpp_ode += ") = %s\n" % v["value"]

    xpp_ode += "\n# Time derivatives\n"
    for k, v in data["time_derivatives"].items():
        xpp_ode += f"{k}' = {v}\n"

    xpp_ode += "\n# Derived variables\n"
    for k, v in data["derived_variables"].items():
        xpp_ode += f"{k} = {v}\n"

    xpp_ode += "\n# Conditional derived variables\n"
    for k, v in data["conditional_derived_variables"].items():
        xpp_ode += f"{k} = if({v['condition']})then({v['value_true']})else({v['value_false']})\n"

    xpp_ode += "\n# Initial values\n"
    for k, v in data["initial_values"].items():
        xpp_ode += f"init {k} = {v}\n"

    xpp_ode += "\n# Settings\n"
    for k, v in data["settings"].items():
        xpp_ode += f"@ {k.upper()}={v}\n"

    xpp_ode += "\ndone\n"

    with open(new_xpp_filename, "w") as f:
        f.write(xpp_ode)

    logger.info("Written %s" % new_xpp_filename)


def _substitute_single_var(expr, old_var, new_var, pythonic=False):
    import sympy
    from sympy.parsing.sympy_parser import parse_expr

    logger.debug(
        "     -- Substituting <%s> for <%s> in <%s>" % (old_var, new_var, expr)
    )
    if old_var not in expr:
        return expr
    expr = expr.replace("^", "**")
    logger.debug(" -- %s" % expr)

    s_expr = parse_expr(expr, evaluate=False)
    a, b = sympy.symbols("%s %s" % (old_var, new_var))
    s_expr = s_expr.subs(a, b)
    if pythonic:
        new_expr = str(s_expr)
    else:
        new_expr = str(s_expr).replace("**", "^")
    logger.debug("a: %s, b: %s, expr: %s -> %s" % (a, b, s_expr, new_expr))

    return new_expr


def _make_lems_friendly(expr):
    expr = _substitute_single_var(expr, LEMS_TIME, XPP_TIME)

    return expr


def to_lems(data, lems_model_id, lems_model_file):
    import lems.api as lems

    model = lems.Model()

    ct = lems.ComponentType("XPP_model")

    model.add(ct)

    comp = lems.Component("%s_0" % ct.name, ct.name)
    model.add(comp)

    ct.add(lems.Constant("MSEC", "1ms", "time"))

    # ct.dynamics.add(lems.StateVariable(XPP_TIME, "none", XPP_TIME))
    ct.add(lems.Exposure(XPP_TIME, "none"))
    ct.dynamics.add(
        lems.DerivedVariable(
            name=XPP_TIME, exposure=XPP_TIME, dimension="none", value="t/MSEC"
        )
    )

    for k, v in data["parameters"].items():
        ct.add(lems.Parameter(k, "none"))
        comp.set_parameter(k, v)

    os = lems.OnStart()
    ct.dynamics.add(os)

    for k, v in data["initial_values"].items():
        os.add(lems.StateAssignment(k, str(v)))

    for k, v in data["derived_variables"].items():
        ct.add(lems.Exposure(k, "none"))

        dv_expr = substitute_functions(v, data["functions"])
        logger.debug(f"DV: <{v}> -> <{dv_expr}>")

        ct.dynamics.add(
            lems.DerivedVariable(name=k, exposure=k, dimension="none", value=dv_expr)
        )

    for k, v in data["conditional_derived_variables"].items():
        ct.add(lems.Exposure(k, "none"))

        cdv_cond = substitute_functions(v["condition"], data["functions"])
        cdv_cond = _make_lems_friendly(cdv_cond)

        logger.debug(f"CDV: <{v['condition']}> -> <{cdv_cond}>")
        cdv_cond = (
            cdv_cond.replace("<=", ".leq.")
            .replace(">=", ".geq.")
            .replace("<", ".lt.")
            .replace(">", ".gt.")
            .replace("!=", ".neq.")
            .replace("==", ".eq.")
        )

        cdv_opp = (
            cdv_cond.replace(".gt.", ".leq.")
            .replace(".lt.", ".geq.")
            .replace(".geq.", ".lt.")
            .replace(".leq.", ".gt.")
            .replace(".eq.", ".neq.")
            .replace(".neq.", ".eq.")
        )

        cdv_true = substitute_functions(v["value_true"], data["functions"])
        logger.debug(f"CDV: <{v['value_true']}> -> <{cdv_true}>")
        cdv_false = substitute_functions(v["value_false"], data["functions"])
        logger.debug(f"CDV: <{v['value_false']}> -> <{cdv_false}>")

        cdv = lems.ConditionalDerivedVariable(name=k, exposure=k, dimension="none")
        ct.dynamics.add(cdv)
        cdv.add(lems.Case(condition=cdv_cond, value=_make_lems_friendly(cdv_true)))
        cdv.add(lems.Case(condition=cdv_opp, value=_make_lems_friendly(cdv_false)))

    for k, v in data["time_derivatives"].items():
        ct.add(lems.Exposure(k, "none"))
        ct.dynamics.add(lems.StateVariable(k, "none", k))

        td_expr = substitute_functions(v, data["functions"])
        td_expr = _make_lems_friendly(td_expr)
        logger.debug(f"TD: <{v}> -> <{td_expr}>")

        ct.dynamics.add(lems.TimeDerivative(k, "(%s)/MSEC" % td_expr))

    logger.info("Saving LEMS model to: %s" % lems_model_file)
    model.export_to_file(lems_model_file)

    from pyneuroml.lems import LEMSSimulation

    duration = float(data["settings"]["total"]) if "total" in data["settings"] else 1000
    dt = (
        float(data["settings"]["dtmin"])
        if "dtmin" in data["settings"]
        else (float(data["settings"]["dt"]) if "dt" in data["settings"] else 0.025)
    )

    ls = LEMSSimulation(lems_model_id, duration, dt, comp.id)

    ls.include_lems_file(lems_model_file)

    disp0 = "Exposures"

    ls.create_display(disp0, "Params", "-90", "50")

    of0 = "output_file"
    ls.create_output_file(of0, "output.dat")

    from pyneuroml.utils.plot import get_next_hex_color

    for e in ct.exposures:
        if not e.name == XPP_TIME:
            ls.add_line_to_display(
                disp0, e.name, "%s" % (e.name), "1", get_next_hex_color()
            )
            ls.add_column_to_output_file(of0, e.name, "%s" % (e.name))

    """
    eof0 = "Events_file"
    ls.create_event_output_file(eof0, "%s.v.spikes" % lems_model_id, format="ID_TIME")

    ls.add_selection_to_event_output_file(eof0, "0", "hhpop[0]", "spike")"""

    ls.set_report_file("report.txt")

    # print("Using information to generate LEMS: ")
    # pprint(ls.lems_info)
    # print("\nLEMS: ")
    # print(ls.to_xml())

    lems_filename = ls.save_to_file()

    return lems_filename


def to_brian2(data, brian_file):
    logger.warning("WARNING: Work in progress...")

    brian_script = "from brian2 import *\n\n"

    eqns = ""
    post = ""
    save = "all_data = np.array( [ "

    for k, v in data["time_derivatives"].items():
        td_expr = substitute_functions(v, data["functions"])
        td_expr = _substitute_single_var(td_expr, LEMS_TIME, XPP_TIME, pythonic=True)
        logger.debug(f"TD: <{v}> -> <{td_expr}>")

        eqns += "    d%s/dt = %s : 1\n" % (k, "(%s)/MSEC" % td_expr)

        post += "record_%s = StateMonitor(pop,'%s',record=[0])\n\n" % (k, k)

        if ".t," not in save:
            save += "record_%s.t" % k

        save += ", record_%s.%s[0]" % (k, k)

    save += """ ])

all_data = all_data.transpose()
file_of1 = open("output.dat", 'w')
for l in all_data:
    line = ''
    for c in l:
        line = line + ('\\t%s'%c if len(line)>0 else '%s'%c)
    file_of1.write(line+'\\n')

file_of1.close()"""

    eqns += "    MSEC = 1*msecond : second\n"

    eqns += "    %s = t/MSEC : 1\n" % XPP_TIME

    for k, v in data["parameters"].items():
        if not k == "pi":
            eqns += "    %s = %s : 1\n" % (k, v)

    for k, v in data["derived_variables"].items():
        dv_expr = substitute_functions(v, data["functions"]).replace("^", "**")
        logger.debug(f"DV: <{v}> -> <{dv_expr}>")

        eqns += "    %s = %s : 1\n" % (k, dv_expr)

    """
    os = lems.OnStart()
    ct.dynamics.add(os)

    for k,v in data["initial_values"].items():
        os.add(lems.StateAssignment(k,str(v)))


    for k,v in data["conditional_derived_variables"].items():
        ct.add(lems.Exposure(k, "none"))

        cdv_cond = substitute_functions(v['condition'], data["functions"])
        cdv_cond = _make_lems_friendly(cdv_cond)

        logger.debug(f"CDV: <{v['condition']}> -> <{cdv_cond}>")
        cdv_cond = cdv_cond.replace('<=','.leq.').replace('>=','.geq.').replace('<','.lt.').replace('>','.gt.').replace('!=','.neq.').replace('==','.eq.')

        cdv_opp = cdv_cond.replace('.gt.','.leq.').replace('.lt.','.geq.').replace('.geq.','.lt.').replace('.leq.','.gt.').replace('.eq.','.neq.').replace('.neq.','.eq.')

        cdv_true = substitute_functions(v['value_true'], data["functions"])
        logger.debug(f"CDV: <{v['value_true']}> -> <{cdv_true}>")
        cdv_false = substitute_functions(v['value_false'], data["functions"])
        logger.debug(f"CDV: <{v['value_false']}> -> <{cdv_false}>")

        cdv = lems.ConditionalDerivedVariable(name=k, exposure=k, dimension='none')
        ct.dynamics.add(cdv)
        cdv.add(lems.Case(condition=cdv_cond, value=_make_lems_friendly(cdv_true)))
        cdv.add(lems.Case(condition=cdv_opp, value=_make_lems_friendly(cdv_false)))
    """

    brian_script += "eqns = Equations('''\n%s''')\n\n" % eqns

    duration = float(data["settings"]["total"]) if "total" in data["settings"] else 1000
    dt = (
        float(data["settings"]["dtmin"])
        if "dtmin" in data["settings"]
        else (float(data["settings"]["dt"]) if "dt" in data["settings"] else 0.025)
    )

    brian_script += "defaultclock.dt = %s*msecond\n" % dt
    brian_script += "duration = %s*msecond\n" % duration
    brian_script += "steps = int(duration/defaultclock.dt)+1\n\n"

    brian_script += "pop = NeuronGroup(1, model=eqns)\n\n"

    brian_script += "%s\n\n" % post

    brian_script += (
        "run(duration) # Run a simulation from t=0 to just before t=duration \n\n"
    )

    brian_script += "%s\n\n" % save

    brian_script += (
        "print('Finished Brian 2 simulation of duration %s ms') \n\n" % duration
    )

    logger.info("Saving Brain model to: %s" % brian_file)

    with open(brian_file, "w") as f:
        f.write(brian_script)

    logger.info("Written %s" % brian_file)

    """
    from pyneuroml.lems import LEMSSimulation


    ls = LEMSSimulation(lems_model_id, duration, dt, comp.id)

    ls.include_lems_file(lems_model_file)


    disp0 = "Exposures"

    ls.create_display(disp0, "Params", "-90", "50")

    from pyneuroml.utils.plot import get_next_hex_color
    for e in ct.exposures:
        if not e.name == XPP_TIME:
            ls.add_line_to_display(disp0, e.name, "%s"%(e.name), "1", get_next_hex_color())

    '''
    of0 = "Volts_file"
    ls.create_output_file(of0, "%s.v.dat" % lems_model_id)
    ls.add_column_to_output_file(of0, "v", "hhpop[0]/v")

    eof0 = "Events_file"
    ls.create_event_output_file(eof0, "%s.v.spikes" % lems_model_id, format="ID_TIME")

    ls.add_selection_to_event_output_file(eof0, "0", "hhpop[0]", "spike")'''

    ls.set_report_file("report.txt")

    #print("Using information to generate LEMS: ")
    #pprint(ls.lems_info)
    #print("\nLEMS: ")
    #print(ls.to_xml())

    ls.save_to_file()"""


DEFAULTS = {
    "lems": False,
    "xpp": False,
    "brian2": False,
    "run": False,
    "plot": False,
}  # type: typing.Dict[str, typing.Any]


def process_args():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=("A script to interact with XPPAUT ode files")
    )

    parser.add_argument(
        "ode_filename",
        type=str,
        metavar="<XPPAUT ode file>",
        help="XPPAUT ode file",
    )

    parser.add_argument(
        "-xpp",
        action="store_true",
        default=DEFAULTS["xpp"],
        help="Regenerate XPP ode file from loaded XPP file (for testing purposes)",
    )
    parser.add_argument(
        "-lems",
        action="store_true",
        default=DEFAULTS["lems"],
        help="Generate LEMS equivalent of XPP file",
    )
    parser.add_argument(
        "-brian2",
        action="store_true",
        default=DEFAULTS["brian2"],
        help="Generate Brian 2 equivalent of XPP file",
    )
    parser.add_argument(
        "-run",
        action="store_true",
        default=DEFAULTS["lems"],
        help="Run generated file",
    )
    parser.add_argument(
        "-plot",
        action="store_true",
        default=DEFAULTS["plot"],
        help="Plot saved variables",
    )

    return parser.parse_args()


def main(args=None):
    """Main runner method"""
    if args is None:
        args = process_args()

    cli(a=args)


def run_xpp_file(filename, plot, show_plot_already=True, plot_separately={}):
    import subprocess as sp

    cmds = ["%s/xppaut" % os.environ["XPP_HOME"], filename, "-silent"]
    cwd = os.getcwd()
    try:
        ret_string = sp.check_output(
            cmds, cwd=cwd, shell=False, stderr=sp.STDOUT
        ).decode("utf-8")

        xpp_error_phrases = ["Error allocating", "illegal expression"]
        for err in xpp_error_phrases:
            if err in ret_string:
                raise Exception(
                    "Command: %s failed! Full output from XPP: \n==========================\n%s\n=========================="
                    % (cmds, ret_string)
                )
        logger.info("Commands: %s completed successfully" % (cmds))
        if isinstance(ret_string, bytes):
            ret_string = ret_string.decode("utf-8")  # For Python 3...

    except sp.CalledProcessError as err:
        logger.error(
            "CalledProcessError running commands: %s in %s (return code: %s), output:\n%s"
            % (cmds, cwd, err.returncode, err.output),
        )
        raise err
    except Exception as err:
        logger.info("Error running commands: %s in (%s)!" % (cmds, cwd))
        logger.info("Error: %s" % (err))
        raise err

    if plot:
        parsed_data = parse_script(filename)

        from pyneuroml.pynml import reload_standard_dat_file

        result_file = "output.dat"
        data, indices = reload_standard_dat_file(result_file)
        logger.info("Loading data: %s" % (data.keys()))
        default_figure = "Data loaded from: %s after running %s" % (
            result_file,
            filename,
        )  # Title
        ts = {default_figure: []}
        xs = {default_figure: []}
        labels = {default_figure: []}
        for new_fig in plot_separately:
            ts[new_fig] = []
            xs[new_fig] = []
            labels[new_fig] = []

        tds = list(parsed_data["time_derivatives"].keys())
        cdvs = ["%s??" % c for c in parsed_data["conditional_derived_variables"].keys()]
        outputs = tds + cdvs
        logger.info(
            "Loading data: %s, assuming these represent %s (%i values)"
            % (data.keys(), outputs, len(outputs))
        )
        for i in indices:
            label = outputs[i] if i < len(outputs) else "???"

            fig = default_figure
            for new_fig in plot_separately:
                if label in plot_separately[new_fig]:
                    fig = new_fig
            ts[fig].append(data["t"])
            xs[fig].append(data[i])
            labels[fig].append(label)

        from pyneuroml.plot.Plot import generate_plot

        axes = {}
        for fig_title in ts:
            ax = generate_plot(
                ts[fig_title],
                xs[fig_title],
                title=fig_title,
                labels=labels[fig_title],
                xaxis="Time (?)",  # x axis legend
                yaxis="??",  # y axis legend
                show_plot_already=show_plot_already,  # Show or wait for plt.show()?
            )
            axes[fig_title] = ax
        return axes


def cli(a: typing.Optional[typing.Any] = None, **kwargs: str):
    """Main cli caller method"""
    a = build_namespace(DEFAULTS, a, **kwargs)

    file_path = a.ode_filename
    parsed_data = parse_script(file_path)
    pprint(parsed_data)

    logger.info("Loaded XPP file: %s" % a.ode_filename)

    lems_model_id = file_path.replace(".ode", "").split("/")[-1]
    lems_model_file = file_path.replace(".ode", ".model.xml")

    if a.run and not a.lems and not a.xpp and not a.brian2:
        logger.info("Running %s with XPP (plotting: %s)..." % (a.ode_filename, a.plot))

        run_xpp_file(a.ode_filename, a.plot)

    if a.lems:
        lems_filename = to_lems(parsed_data, lems_model_id, lems_model_file)
        logger.info("Generated LEMS file: %s" % lems_filename)
        if a.run:
            logger.info(
                "Running %s with jNeuroML (plotting: %s)..." % (lems_filename, a.plot)
            )

            from pyneuroml.runners import run_lems_with_jneuroml

            run_lems_with_jneuroml(
                lems_filename,
                nogui=True,
                plot=a.plot,
                verbose=True,
                load_saved_data=True,
            )

    if a.xpp:
        new_xppfile = file_path.replace(".ode", "_2.ode")
        to_xpp(parsed_data, new_xppfile)

        if a.run:
            run_xpp_file(new_xppfile, a.plot)

    if a.brian2:
        to_brian2(parsed_data, file_path.replace(".ode", "_brian2.py"))
        if a.run or a.plot:
            raise NotImplementedError(
                "Running Brian generated from XPP not yet implemented!"
            )


if __name__ == "__main__":
    main()
