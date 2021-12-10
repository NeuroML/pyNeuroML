"""

    Still under developemnt!!

    Subject to change without notice!!

"""


import sys
from pyneuroml.tune.NeuroMLTuner import run_optimisation


if __name__ == "__main__":
    nogui = "-nogui" in sys.argv

    parameters = [
        "cell:hhcell/channelDensity:naChans/mS_per_cm2",
        "cell:hhcell/channelDensity:kChans/mS_per_cm2",
    ]

    # above parameters will not be modified outside these bounds:
    min_constraints = [50, 10]
    max_constraints = [200, 60]

    known_target_values = {
        "cell:hhcell/channelDensity:naChans/mS_per_cm2": 120,
        "cell:hhcell/channelDensity:kChans/mS_per_cm2": 36,
    }

    max_peak_no = "hhpop[0]/v:max_peak_no"
    average_maximum = "hhpop[0]/v:average_maximum"
    average_minimum = "hhpop[0]/v:average_minimum"

    weights = {max_peak_no: 5, average_maximum: 1, average_minimum: 1}

    target_data = {max_peak_no: 34, average_maximum: 30.72, average_minimum: -75}

    simulator = "jNeuroML_NEURON"
    simulator = "jNeuroML"

    run_optimisation(
        prefix="TestHHpy",
        neuroml_file="test_data/HHCellNetwork.net.nml",
        target="HHCellNetwork",
        parameters=parameters,
        max_constraints=max_constraints,
        min_constraints=min_constraints,
        weights=weights,
        target_data=target_data,
        sim_time=700,
        population_size=20,
        max_evaluations=60,
        num_selected=10,
        num_offspring=10,
        mutation_rate=0.5,
        num_elites=3,
        seed=12345,
        simulator=simulator,
        nogui=nogui,
        known_target_values=known_target_values,
        num_parallel_evaluations=3,
    )
