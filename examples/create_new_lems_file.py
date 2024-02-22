"""

Example to create some new LEMS files for running NML2 models

"""

from pyneuroml.lems import LEMSSimulation
from pyneuroml.lems import generate_lems_file_for_neuroml
import os
import sys
import pprint

pp = pprint.PrettyPrinter(depth=6)


if __name__ == "__main__":
    ############################################
    #  Create a LEMS file "manually"...

    sim_id = "HHSim"
    ls = LEMSSimulation(sim_id, 500, 0.05, "net1")
    ls.include_neuroml2_file("NML2_SingleCompHHCell.nml")

    disp0 = "display0"
    ls.create_display(disp0, "Voltages", "-90", "50")

    ls.add_line_to_display(disp0, "v", "hhpop[0]/v", "1mV", "#ffffff")

    of0 = "Volts_file"
    ls.create_output_file(of0, "%s.v.dat" % sim_id)
    ls.add_column_to_output_file(of0, "v", "hhpop[0]/v")

    eof0 = "Events_file"
    ls.create_event_output_file(eof0, "%s.v.spikes" % sim_id, format="ID_TIME")

    ls.add_selection_to_event_output_file(eof0, "0", "hhpop[0]", "spike")

    ls.set_report_file("report.txt")

    print("Using information to generate LEMS: ")
    pp.pprint(ls.lems_info)
    print("\nLEMS: ")
    print(ls.to_xml())

    ls.save_to_file()
    assert os.path.isfile("LEMS_%s.xml" % sim_id)

    ############################################
    #  Create the LEMS file with helper method
    sim_id = "Simple"
    neuroml_file = "test_data/simplenet.nml"
    target = "simplenet"
    duration = 1000
    dt = 0.025
    lems_file_name = "LEMS_%s.xml" % sim_id
    target_dir = "test_data"

    generate_lems_file_for_neuroml(
        sim_id,
        neuroml_file,
        target,
        duration,
        dt,
        lems_file_name,
        target_dir,
        include_extra_files=[],
        gen_plots_for_all_v=True,
        plot_all_segments=False,
        gen_plots_for_quantities={},  # Dict with displays vs lists of quantity paths
        gen_plots_for_only_populations=[],  # List of populations, all pops if = []
        gen_saves_for_all_v=True,
        save_all_segments=False,
        gen_saves_for_only_populations=[],  # List of populations, all pops if = []
        gen_saves_for_quantities={},  # Dict with file names vs lists of quantity paths
        gen_spike_saves_for_all_somas=True,
        report_file_name="report.txt",
        copy_neuroml=True,
        verbose=True,
    )

    if "-test" in sys.argv:
        neuroml_file = "test_data/HHCellNetwork.net.nml"
        lems_file_name = "LEMS_%s2.xml" % sim_id
        target = "HHCellNetwork"
        target_dir = "test_data/tmp"
        if not os.path.isdir(target_dir):
            os.mkdir(target_dir)

        generate_lems_file_for_neuroml(
            sim_id,
            neuroml_file,
            target,
            duration,
            dt,
            lems_file_name,
            target_dir,
            copy_neuroml=True,
            verbose=True,
        )
