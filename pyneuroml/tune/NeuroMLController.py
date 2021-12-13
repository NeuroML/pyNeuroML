"""
A Neurotune controller specific to NeuroML.

Please see https://neurotune.readthedocs.io/en/latest/architecture.html for
more information on controllers in Neurotune.
"""

import os.path
import os
import sys
import time
import shutil
import logging
import pprint

import io

if sys.version_info.major == 2:
    from StringIO import StringIO
else:
    from io import StringIO

from collections import OrderedDict
import pyneuroml.pynml
from pyneuroml import print_v
import neuroml


logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=4)


class NeuroMLController:
    """A Neurotune controller specific to NeuroML.

    Please see https://neurotune.readthedocs.io/en/latest/architecture.html for
    more information on controllers in Neurotune.
    """

    def __init__(
        self,
        ref,
        neuroml_file,
        target,
        sim_time=1000,
        dt=0.05,
        simulator="jNeuroML",
        generate_dir="./",
        num_parallel_evaluations=1,
        cleanup=True,
    ):
        """Initialise the NeuroMLController.

        :param ref:
        :type ref:
        :param neuroml_file: NeuroML model file containing model being optimised
        :type neuroml_file: str
        :param target: id of NeuroML target element
        :type target: str
        :param sim_time: simulation time
        :type sim_time: float
        :param dt: integration time step
        :type dt: float
        :param simulator: simulator to use
        :type simulator: str
        :param generate_dir: directory where optimisation simulation files will be generated
        :type generate_dir: str
        :param num_parallel_evaluations: number of parallel evaluations
        :type num_parallel_evaluations: int
        :param cleanup: toggle whether data files should be removed after data is loaded
        :type cleanup: bool
        """

        self.ref = ref
        self.neuroml_file = neuroml_file
        self.target = target
        self.sim_time = sim_time
        self.dt = dt
        self.simulator = simulator
        self.generate_dir = (
            generate_dir if generate_dir.endswith("/") else generate_dir + "/"
        )
        self.num_parallel_evaluations = num_parallel_evaluations
        self.cleanup = cleanup

        if (
            int(num_parallel_evaluations) != num_parallel_evaluations
            or num_parallel_evaluations < 1
        ):
            raise Exception(
                "Error with num_parallel_evaluations = %s\nPlease use an integer value greater than 1."
                % num_parallel_evaluations
            )

        self.nml_doc = pyneuroml.pynml.read_neuroml2_file(
            neuroml_file,
            include_includes=True,
            verbose=True,
            already_included=[],
            check_validity_pre_include=True,
        )

        # Due to the included files not being valid nml2 => libNeuroML can't load them...
        self.still_included = []
        for include in self.nml_doc.includes:
            self.still_included.append(include.href)

        self.count = 0

    def run(self, candidates, parameters):
        """Run simulation for each candidate.

        This run method will loop through each candidate and run the simulation
        corresponding to its parameter values. It will populate an array called
        traces with the resulting voltage traces for the simulation and return it.

        :param candidates: candidate simulations
        :type candidates: list
        :param parameters: parameters for simulations
        :type parameters: list
        :returns: list of [time, voltage] values
        """

        traces = []
        start_time = time.time()

        if self.num_parallel_evaluations == 1:

            for candidate_i in range(len(candidates)):

                candidate = candidates[candidate_i]
                sim_var = dict(zip(parameters, candidate))
                print_v(
                    "\n\n  - RUN %i (%i/%i); variables: %s\n"
                    % (self.count, candidate_i + 1, len(candidates), sim_var)
                )
                self.count += 1
                t, v = self.run_individual(sim_var)
                traces.append([t, v])
        else:
            import pp

            ppservers = ()
            job_server = pp.Server(self.num_parallel_evaluations, ppservers=ppservers)
            logger.info(
                "Running %i candidates across %i local processes"
                % (len(candidates), job_server.get_ncpus())
            )
            jobs = []

            for candidate_i in range(len(candidates)):
                candidate = candidates[candidate_i]
                sim_var = dict(zip(parameters, candidate))
                print_v(
                    "\n\n  - PARALLEL RUN %i (%i/%i of curr candidates); variables: %s\n"
                    % (self.count, candidate_i + 1, len(candidates), sim_var)
                )
                self.count += 1
                cand_dir = self.generate_dir + "/CANDIDATE_%s" % candidate_i
                if not os.path.exists(cand_dir):
                    os.mkdir(cand_dir)
                # We do not pass the nml_doc here because it now uses
                # lxml.etree, which unfortunately cannot be pickled.  Instead
                # we pass it as a StringIO object, and let the run_simulation
                # method read this in to create the nml_doc.  It is perhaps
                # less efficient because the nml_doc needs to be created each
                # time, but this is the only way it will work at the moment.
                nml_doc_text = StringIO()
                neuroml.writers.NeuroMLWriter.write(
                    self.nml_doc, nml_doc_text, close=False
                )
                vars = (
                    sim_var,
                    self.ref,
                    self.neuroml_file,
                    nml_doc_text.getvalue(),
                    self.still_included,
                    cand_dir,
                    self.target,
                    self.sim_time,
                    self.dt,
                    self.simulator,
                )

                job = job_server.submit(
                    run_individual,
                    vars,
                    (),
                    (
                        "pyneuroml",
                        "pyneuroml.pynml",
                        "pyneuroml.tune.NeuroMLSimulation",
                        "shutil",
                        "neuroml",
                        "logging",
                    ),
                )
                jobs.append(job)
                nml_doc_text.close()

            for job_i in range(len(jobs)):
                job = jobs[job_i]
                logger.info(
                    "Checking parallel job %i/%i; set running so far: %i"
                    % (job_i, len(jobs), self.count)
                )
                t, v = job()
                traces.append([t, v])

                # logger.info("Obtained: %s"%result)

            # job_server.print_stats()
            job_server.destroy()
            print("-------------------------------------------")

        end_time = time.time()
        tot = end_time - start_time
        print_v(
            "Ran %i candidates in %s seconds (~%ss per job)"
            % (len(candidates), tot, tot / len(candidates))
        )
        return traces

    def run_individual(self, sim_var, show=False, cleanup=None):
        """Run an individual simulation."""
        return run_individual(
            sim_var,
            self.ref,
            self.neuroml_file,
            self.nml_doc,
            self.still_included,
            self.generate_dir,
            self.target,
            self.sim_time,
            self.dt,
            self.simulator,
            cleanup=self.cleanup if cleanup is None else cleanup,
            show=show,
        )


# This needs to be a separate function for the ppft job server
def run_individual(
    sim_var,
    reference,
    neuroml_file,
    nml_doc,
    still_included,
    generate_dir,
    target,
    sim_time,
    dt,
    simulator,
    cleanup=True,
    show=False,
):
    """
    Run an individual simulation.

    The candidate data has been flattened into the sim_var dict. The
    sim_var dict contains parameter:value key value pairs, which are
    applied to the model before it is simulated.

    :param sim_var:
    :type sim_var:
    :param reference:
    :type reference:
    :param neuroml_file: path to main NeuroML model file
    :type neuroml_file: str
    :param nml_doc: NeuroMLDocument or its str export
    :type nml_doc: NeuroMLDocument or str
    :param still_included:
    :type still_included:
    :param generate_dir: directory to generate simulation NeuroML file in
    :type generate_dir: str
    :param target: id of target NeuroML component
    :type target: str
    :param sim_time: length of simulation
    :type sim_time: float
    :param dt: simulation time step
    :type dt: float
    :param simulator: simulator to use ("jNeuroML", "jNeuroML_NEURON")
    :type simulator: str
    :param cleanup: toggle if temporary files should be removed after simulation
    :type cleanup: bool
    :param show:
    :type show: bool

    :returns: list of simulation times and voltages at each time: [time, volts]

    """
    # Needs to be redefined here for the jobserver
    logger = logging.getLogger(__name__)

    if isinstance(nml_doc, str):
        nml_doc = neuroml.loaders.read_neuroml2_string(nml_doc)

    for var_name in sim_var.keys():

        individual_var_names = var_name.split("+")

        for individual_var_name in individual_var_names:
            words = individual_var_name.split("/")
            type, id1 = words[0].split(":")
            if ":" in words[1]:
                variable, id2 = words[1].split(":")
            else:
                variable = words[1]
                id2 = None

            units = words[2]
            value = sim_var[var_name]

            # needs to be fully qualified because only pyneuroml is in the
            # module table for pp jobs
            pyneuroml.print_v(
                "  Changing value of %s (%s) in %s (%s) to: %s %s"
                % (variable, id2, type, id1, value, units)
            )

            if type == "channel":
                channel = nml_doc.get_by_id(id1)

                if channel:
                    print("Setting channel %s" % (channel))
                    if variable == "vShift":
                        channel.v_shift = "%s %s" % (value, units)
                else:
                    raise KeyError(
                        "Could not find channel with id %s from expression: %s"
                        % (id1, individual_var_name)
                    )
            elif type == "cell":
                cell = None
                for c in nml_doc.cells:
                    if c.id == id1:
                        cell = c

                if variable == "channelDensity":
                    chanDens = None
                    for cd in (
                        cell.biophysical_properties.membrane_properties.channel_densities
                        + cell.biophysical_properties.membrane_properties.channel_density_v_shifts
                    ):
                        if cd.id == id2:
                            chanDens = cd

                    chanDens.cond_density = "%s %s" % (value, units)
                elif variable == "vShift_channelDensity":
                    chanDens = None
                    for (
                        cd
                    ) in (
                        cell.biophysical_properties.membrane_properties.channel_density_v_shifts
                    ):
                        if cd.id == id2:
                            chanDens = cd

                    chanDens.v_shift = "%s %s" % (value, units)
                elif variable == "channelDensityNernst":
                    chanDens = None
                    for (
                        cd
                    ) in (
                        cell.biophysical_properties.membrane_properties.channel_density_nernsts
                    ):
                        if cd.id == id2:
                            chanDens = cd

                    chanDens.cond_density = "%s %s" % (value, units)
                elif (
                    variable == "erev_id"
                ):  # change all values of erev in channelDensity elements with only this id
                    chanDens = None
                    for cd in (
                        cell.biophysical_properties.membrane_properties.channel_densities
                        + cell.biophysical_properties.membrane_properties.channel_density_v_shifts
                    ):
                        if cd.id == id2:
                            chanDens = cd

                    chanDens.erev = "%s %s" % (value, units)
                elif (
                    variable == "erev_ion"
                ):  # change all values of erev in channelDensity elements with this ion
                    chanDens = None
                    for cd in (
                        cell.biophysical_properties.membrane_properties.channel_densities
                        + cell.biophysical_properties.membrane_properties.channel_density_v_shifts
                    ):
                        if cd.ion == id2:
                            chanDens = cd

                    chanDens.erev = "%s %s" % (value, units)
                elif variable == "specificCapacitance":
                    specCap = None
                    for (
                        sc
                    ) in (
                        cell.biophysical_properties.membrane_properties.specific_capacitances
                    ):
                        if (
                            sc.segment_groups is None and id2 == "all"
                        ) or sc.segment_groups == id2:
                            specCap = sc

                    specCap.value = "%s %s" % (value, units)
                elif variable == "resistivity":
                    resistivity = None
                    for (
                        rs
                    ) in (
                        cell.biophysical_properties.intracellular_properties.resistivities
                    ):
                        if (
                            rs.segment_groups is None and id2 == "all"
                        ) or rs.segment_groups == id2:
                            resistivity = rs
                    resistivity.value = "%s %s" % (value, units)
                else:
                    raise KeyError(
                        "Unknown variable (%s) in variable expression: %s"
                        % (variable, individual_var_name)
                    )
            elif type == "izhikevich2007Cell":
                izhcell = None
                for c in nml_doc.izhikevich2007_cells:
                    if c.id == id1:
                        izhcell = c

                izhcell.__setattr__(variable, "%s %s" % (value, units))
            else:
                raise TypeError(
                    "Unknown type (%s) in variable expression: %s"
                    % (type, individual_var_name)
                )

    new_neuroml_file = "%s/%s" % (generate_dir, os.path.basename(neuroml_file))
    if new_neuroml_file == neuroml_file:
        raise RuntimeError(
            "Cannot use a directory for generating into (%s) which is the same location of the NeuroML file (%s)!"
            % (neuroml_file, generate_dir)
        )

    pyneuroml.pynml.write_neuroml2_file(nml_doc, new_neuroml_file)

    for include in still_included:
        inc_loc = "%s/%s" % (os.path.dirname(os.path.abspath(neuroml_file)), include)
        logger.info(
            "Copying non included file %s to %s (%s) beside %s"
            % (inc_loc, generate_dir, os.path.abspath(generate_dir), new_neuroml_file)
        )
        shutil.copy(inc_loc, generate_dir)

    from pyneuroml.tune.NeuroMLSimulation import NeuroMLSimulation

    sim = NeuroMLSimulation(
        reference,
        neuroml_file=new_neuroml_file,
        target=target,
        sim_time=sim_time,
        dt=dt,
        simulator=simulator,
        generate_dir=generate_dir,
        cleanup=cleanup,
        nml_doc=nml_doc,
    )

    sim.go()

    if show:
        sim.show()

    return sim.t, sim.volts


if __name__ == "__main__":
    sim_time = 700
    dt = 0.05

    import logging

    logging.basicConfig(level=logging.WARNING)

    nogui = "-nogui" in sys.argv

    sim_vars = OrderedDict(
        [
            ("cell:hhcell/channelDensity:naChans/mS_per_cm2", 100),
            ("cell:hhcell/channelDensity:kChans/mS_per_cm2", 20),
        ]
    )

    cont = NeuroMLController(
        "TestHH",
        "../../examples/test_data/HHCellNetwork.net.nml",
        "HHCellNetwork",
        sim_time,
        dt,
        "jNeuroML_NEURON",
        "temp/",
        num_parallel_evaluations=1,
    )

    num_cands = 4

    if "-many" in sys.argv:
        candidates = []
        for i in range(num_cands):
            candidates.append([100 + i, 20 + i])

        parameters = sim_vars.keys()
        print("Using %s & %s" % (parameters, candidates))

        traces = cont.run(candidates, parameters)
    elif "-manyp" in sys.argv:
        candidates = []
        for i in range(num_cands):
            candidates.append([100 + i, 20 + i])

        parameters = sim_vars.keys()
        print("Using %s & %s" % (parameters, candidates))

        cont.num_parallel_evaluations = num_cands
        traces = cont.run(candidates, parameters)
    else:
        t, v = cont.run_individual(sim_vars, show=(not nogui))

        from pyelectro import analysis

        analysis_var = {
            "peak_delta": 0,
            "baseline": 0,
            "dvdt_threshold": 0,
            "peak_threshold": 0,
        }
        data_analysis = analysis.NetworkAnalysis(
            v, t, analysis_var, start_analysis=0, end_analysis=sim_time
        )

        analysed = data_analysis.analyse()
        pp.pprint(analysed)
