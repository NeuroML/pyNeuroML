import sys
import time
import logging

from pyneuroml import pynml, print_v
from pyneuroml.lems import generate_lems_file_for_neuroml


logger = logging.getLogger(__name__)


class NeuroMLSimulation(object):
    """
    A class for running a single instance of a NeuroML model by generating a
    LEMS file and using pyNeuroML to run in a chosen simulator
    """

    def __init__(
        self,
        reference,
        neuroml_file,
        target,
        sim_time=1000,
        dt=0.05,
        simulator="jNeuroML",
        generate_dir="./",
        cleanup=True,
        nml_doc=None,
    ):
        self.sim_time = sim_time
        self.dt = dt
        self.simulator = simulator
        self.generate_dir = (
            generate_dir if generate_dir.endswith("/") else generate_dir + "/"
        )

        self.reference = reference
        self.target = target
        self.neuroml_file = neuroml_file
        self.nml_doc = nml_doc
        self.cleanup = cleanup

        self.already_run = False

    def show(self):
        """
        Plot the result of the simulation once it's been intialized using
        matplotlib.
        """

        from matplotlib import pyplot as plt

        if self.already_run:
            for ref in self.volts.keys():
                plt.plot(self.t, self.volts[ref], label=ref)
                plt.title("Simulation voltage vs time")
                plt.legend()
                plt.xlabel("Time [ms]")
                plt.ylabel("Voltage [mV]")

        else:
            logger.warning("First you have to 'go()' the simulation.", True)
        plt.show()

    def go(self):
        """Run the simulation."""

        lems_file_name = "LEMS_%s.xml" % (self.reference)

        generate_lems_file_for_neuroml(
            self.reference,
            self.neuroml_file,
            self.target,
            self.sim_time,
            self.dt,
            lems_file_name=lems_file_name,
            target_dir=self.generate_dir,
            nml_doc=self.nml_doc,
        )

        logger.info(
            "Running a simulation of %s ms with timestep %s ms: %s"
            % (self.sim_time, self.dt, lems_file_name)
        )

        self.already_run = True

        start = time.time()
        if self.simulator == "jNeuroML":
            results = pynml.run_lems_with_jneuroml(
                lems_file_name,
                nogui=True,
                load_saved_data=True,
                plot=False,
                exec_in_dir=self.generate_dir,
                verbose=False,
                cleanup=self.cleanup,
            )
        elif self.simulator == "jNeuroML_NEURON":
            results = pynml.run_lems_with_jneuroml_neuron(
                lems_file_name,
                nogui=True,
                load_saved_data=True,
                plot=False,
                exec_in_dir=self.generate_dir,
                verbose=False,
                cleanup=self.cleanup,
            )
        else:
            raise RuntimeError("Unsupported simulator: %s" % self.simulator)

        secs = time.time() - start
        print_v(
            "Ran simulation in %s in %f seconds (%f mins)\n\n"
            % (self.simulator, secs, secs / 60.0)
        )
        self.t = [t * 1000 for t in results["t"]]

        self.volts = {}

        for key in results.keys():
            if key != "t":
                self.volts[key] = [v * 1000 for v in results[key]]


if __name__ == "__main__":
    sim_time = 700
    dt = 0.05

    if len(sys.argv) == 2 and sys.argv[1] == "-net":
        sim = NeuroMLSimulation(
            "TestNet",
            "../../examples/test_data/simplenet.nml",
            "simplenet",
            sim_time,
            dt,
            "jNeuroML",
            "temp/",
        )
        sim.go()
        sim.show()
    else:
        sim = NeuroMLSimulation(
            "TestHH",
            "../../examples/test_data/HHCellNetwork.net.nml",
            "HHCellNetwork",
            sim_time,
            dt,
            "jNeuroML",
            "temp",
        )
        sim.go()
        sim.show()
