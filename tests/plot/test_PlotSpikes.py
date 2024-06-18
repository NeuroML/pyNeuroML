import os
import random
import tempfile
import unittest

import numpy as np

import pyneuroml.plot.PlotSpikes as pyplts

from .. import BaseTestCase


class TestPlotSpikes(BaseTestCase):
    """Test suite for the PlotSpikes module."""

    def setUp(self):
        """Set up test data for the test suite."""
        self.spike_data = []

        spike_time_end = 1000
        num_neurons_pop1 = 1000
        num_spikes_pop1 = 5000
        population1_times = [
            random.uniform(0, spike_time_end) for _ in range(num_spikes_pop1)
        ]
        population1_ids = [
            random.randint(0, num_neurons_pop1 - 1) for _ in range(num_spikes_pop1)
        ]
        self.spike_data.append(
            {"name": "Population1", "times": population1_times, "ids": population1_ids}
        )

        num_neurons_pop2 = 500
        num_spikes_pop2 = 5000
        population2_times = [
            random.uniform(0, spike_time_end) for _ in range(num_spikes_pop2)
        ]
        population2_ids = [
            random.randint(0, num_neurons_pop2 - 1) for _ in range(num_spikes_pop2)
        ]
        self.spike_data.append(
            {"name": "Population2", "times": population2_times, "ids": population2_ids}
        )

    def test_plot_spikes_from_data_single(self):
        """Test the plot_spikes function with spike data."""
        # plot individuals
        for data in self.spike_data:
            pyplts.plot_spikes(
                title=f"spikes from data - {data['name']}",
                spike_data=[data],
                show_plots_already=False,
                save_spike_plot_to=f"spike-plot-test-{data['name']}.png",
            )
            self.assertIsFile(f"spike-plot-test-{data['name']}.png")
            os.unlink(f"spike-plot-test-{data['name']}.png")

    def test_plot_spikes_from_data_multi(self):
        """Test the plot_spikes function with spike data."""
        # plot individuals
        # plot together
        pyplts.plot_spikes(
            title="spikes from data",
            spike_data=self.spike_data,
            show_plots_already=False,
            save_spike_plot_to="spike-plot-test-multi.png",
        )
        self.assertIsFile("spike-plot-test-multi.png")
        os.unlink("spike-plot-test-multi.png")

    def test_plot_spikes_from_files(self, max_spikes_per_population=100):
        """Test the plot_spikes function with spike time files."""

        filelist = []
        for pop_data in self.spike_data:
            spike_file = tempfile.NamedTemporaryFile(
                mode="w",
                delete=False,
                dir=".",
                prefix=f"{pop_data['name']}_",
                suffix=".spikes",
            )
            filelist.append(spike_file.name)
            times = pop_data["times"]
            ids = pop_data["ids"]
            for time, gid in zip(times, ids):
                print(f"{gid} {time}", file=spike_file)

            spike_file.flush()
            spike_file.close()

        pyplts.plot_spikes_from_data_files(
            filelist,
            format_="id_t",
            title="spikes from data files",
            show_plots_already=False,
            save_spike_plot_to="spike-plot-from-file-test.png",
        )

        self.assertIsFile("spike-plot-from-file-test.png")

        os.unlink("spike-plot-from-file-test.png")
        for f in filelist:
            os.unlink(f)

    def test_plot_spikes_from_lems_file(self):
        """Test plot_spikes_from_lems_file function"""

        spike_time_end = 1000
        spike_file1 = tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            dir=".",
            prefix="izpop0_",
            suffix=".spikes",
        )
        for j in range(500):
            print(
                f"{random.uniform(0, spike_time_end)} {random.randint(0, 5)}",
                file=spike_file1,
            )
        spike_file1.flush()
        spike_file1.close()

        spike_file2 = tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            dir=".",
            prefix="izpop0_",
            suffix=".spikes",
        )
        for j in range(500):
            print(
                f"{random.uniform(0, spike_time_end)} {random.randint(6, 10)}",
                file=spike_file2,
            )
        spike_file2.flush()
        spike_file2.close()

        lems_contents = f"""
<Lems>

    <!--

        This LEMS file has been automatically generated using PyNeuroML v1.1.13 (libNeuroML v0.5.8)

     -->

    <!-- Specify which component to run -->
    <Target component="example_izhikevich2007network_sim"/>

    <!-- Include core NeuroML2 ComponentType definitions -->
    <Include file="Cells.xml"/>
    <Include file="Networks.xml"/>
    <Include file="Simulation.xml"/>

    <Include file="izhikevich2007_network.nml"/>

    <Simulation id="example_izhikevich2007network_sim" length="1000ms" step="0.1ms" target="IzNet" seed="123">  <!-- Note seed: ensures same random numbers used every run -->
        <EventOutputFile id="Spikes_file__IzhPop0" fileName="{spike_file1.name}" format="TIME_ID">
            <EventSelection id="0" select="IzhPop0[0]" eventPort="spike">
            </EventSelection>
            <EventSelection id="1" select="IzhPop0[1]" eventPort="spike">
            </EventSelection>
            <EventSelection id="2" select="IzhPop0[2]" eventPort="spike">
            </EventSelection>
            <EventSelection id="3" select="IzhPop0[3]" eventPort="spike">
            </EventSelection>
            <EventSelection id="4" select="IzhPop0[4]" eventPort="spike">
            </EventSelection>
            <EventSelection id="5" select="IzhPop0[5]" eventPort="spike">
            </EventSelection>
        </EventOutputFile>
        <EventOutputFile id="Spikes_file__IzhPop1" fileName="{spike_file2.name}" format="TIME_ID">
            <EventSelection id="6" select="IzhPop1[0]" eventPort="spike">
            </EventSelection>
            <EventSelection id="7" select="IzhPop1[1]" eventPort="spike">
            </EventSelection>
            <EventSelection id="8" select="IzhPop1[2]" eventPort="spike">
            </EventSelection>
            <EventSelection id="9" select="IzhPop1[3]" eventPort="spike">
            </EventSelection>
            <EventSelection id="10" select="IzhPop1[4]" eventPort="spike">
            </EventSelection>
        </EventOutputFile>



    </Simulation>

</Lems>
    """

        lems_file = tempfile.NamedTemporaryFile(mode="w", delete=False, dir=".")
        print(lems_contents, file=lems_file)
        lems_file.flush()
        lems_file.close()

        pyplts.plot_spikes_from_lems_file(
            lems_file_name=lems_file.name,
            base_dir=".",
            show_plots_already=False,
            save_spike_plot_to="spikes-test-from-lems-file.png",
            rates=False,
            # rate_window=50,
            # rate_bins=500,
        )
        self.assertIsFile("spikes-test-from-lems-file.png")

        os.unlink("spikes-test-from-lems-file.png")
        os.unlink(spike_file1.name)
        os.unlink(spike_file2.name)
        os.unlink(lems_file.name)

    @unittest.skip("Skipping until write_spike_data_to_hdf5 is implemented")
    def test_plot_spikes_from_sonata_file(self):
        """Test the plot_spikes function with a SONATA-format HDF5 file."""
        spike_data = [  # noqa
            {
                "name": "Population1",
                "times": np.array([1.0, 2.0, 3.0]),
                "ids": np.array([1, 2, 3]),
            },
            {
                "name": "Population2",
                "times": np.array([2.5, 3.5]),
                "ids": np.array([4, 5]),
            },
        ]

        # Create a temporary HDF5 file
        hdf5_file = tempfile.NamedTemporaryFile(delete=False, dir=".", suffix=".h5")
        hdf5_file.close()

        # write_spike_data_to_hdf5(hdf5_file.name, spike_data)

        # Generate a plot from the SONATA HDF5 file and save it to a file
        pyplts.plot_spikes(
            spiketime_files=[hdf5_file.name],
            format_="sonata",
            show_plots_already=False,
            save_figure_to="spike-plot-from-sonata-test.png",
        )
        self.assertIsFile("spike-plot-from-sonata-test.png")

        # Clean up the generated files
        os.unlink("spike-plot-from-sonata-test.png")
        os.unlink(hdf5_file.name)


if __name__ == "__main__":
    unittest.main()
