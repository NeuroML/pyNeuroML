"""

    Still under developemnt!!

    Subject to change without notice!!

"""


from pyneuroml.tune.NeuroMLTuner import run_optimisation
import sys

from pyneuroml.tune.NeuroMLController import NeuroMLController
from collections import OrderedDict

from pyelectro import analysis

import pprint

pp = pprint.PrettyPrinter(indent=4)

if __name__ == "__main__":
    nogui = "-nogui" in sys.argv

    neuroml_file = "OnePyr.net.nml"
    sim_time = 700

    known_target_values = {
        "cell:pyr_4_sym/channelDensity:Na_pyr_soma_group/mS_per_cm2": 120,
        "cell:pyr_4_sym/channelDensity:Kdr_pyr_soma_group/mS_per_cm2": 80,
    }
    if "-tune" in sys.argv:
        parameters = [
            "cell:pyr_4_sym/channelDensity:Na_pyr_soma_group/mS_per_cm2",
            "cell:pyr_4_sym/channelDensity:Kdr_pyr_soma_group/mS_per_cm2",
        ]

        # above parameters will not be modified outside these bounds:
        min_constraints = [50, 10]
        max_constraints = [200, 100]

        mean_spike_frequency = "pyramidals/0/pyr_4_sym/v:mean_spike_frequency"
        average_maximum = "pyramidals/0/pyr_4_sym/v:average_maximum"
        average_minimum = "pyramidals/0/pyr_4_sym/v:average_minimum"

        weights = {mean_spike_frequency: 1, average_maximum: 1, average_minimum: 1}

        target_data = {
            mean_spike_frequency: 32.49,
            average_maximum: 22.50,
            average_minimum: -62.82,
        }

        simulator = "jNeuroML_NEURON"

        run_optimisation(
            prefix="TestPyr",
            neuroml_file=neuroml_file,
            target="network",
            parameters=parameters,
            max_constraints=max_constraints,
            min_constraints=min_constraints,
            weights=weights,
            target_data=target_data,
            sim_time=sim_time,
            population_size=20,
            max_evaluations=100,
            num_selected=10,
            num_offspring=10,
            mutation_rate=0.5,
            num_elites=3,
            seed=12345,
            simulator=simulator,
            nogui=nogui,
            known_target_values=known_target_values,
        )
    else:
        simulator = "jNeuroML_NEURON"

        cont = NeuroMLController(
            "RunOnePyr",
            neuroml_file,
            "network",
            sim_time,
            0.01,
            simulator,
            generate_dir="./temp",
        )

        sim_vars = OrderedDict(known_target_values)

        t, v = cont.run_individual(sim_vars, show=(not nogui))
        print("Have run individual instance...")

        peak_threshold = 0

        analysis_var = {
            "peak_delta": 0,
            "baseline": 0,
            "dvdt_threshold": 0,
            "peak_threshold": peak_threshold,
        }

        example_run_analysis = analysis.NetworkAnalysis(
            v, t, analysis_var, start_analysis=0, end_analysis=sim_time
        )

        analysis = example_run_analysis.analyse()

        pp.pprint(analysis)
