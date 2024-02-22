import sys
from pyneuroml.analysis import generate_current_vs_frequency_curve

nogui = "-nogui" in sys.argv  # Used to supress GUI in tests for Travis-CI

generate_current_vs_frequency_curve(
    "NML2_SingleCompHHCell.nml",
    "hhcell",
    start_amp_nA=-0.1,
    end_amp_nA=0.2,
    step_nA=0.02,
    analysis_duration=1000,
    analysis_delay=50,
    pre_zero_pulse=50,
    post_zero_pulse=50,
    plot_voltage_traces=not nogui,
    plot_if=not nogui,
    plot_iv=not nogui,
    save_if_data_to="if_data.dat",
)
