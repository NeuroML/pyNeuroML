import os
import unittest
import tempfile
import numpy as np

from .. import BaseTestCase
from collections import defaultdict
import pyneuroml.plot.PlotSpikes as pyplts


class TestPlotSpikes(BaseTestCase):
    """Test suite for the PlotSpikes module."""

    def setUp(self):
        """Set up test data for the test suite."""
        self.spike_data = [
            {"name": "Population1", "times": [1.0, 2.0, 3.0], "ids": [1, 2, 3]},
            {"name": "Population2", "times": [2.5, 3.5], "ids": [4, 5]},
        ]

    def test_plot_spikes_from_data(self):
        """Test the plot_spikes function with spike data."""
        pyplts.plot_spikes(
            spike_data=self.spike_data,
            show_plots_already=False,
            save_spike_plot_to="spike-plot-test.png",
        )
        self.assertIsFile("spike-plot-test.png")
        os.unlink("spike-plot-test.png")

    def test_plot_spikes_from_files(self):
        """Test the plot_spikes function with spike time files."""
        spike_file = tempfile.NamedTemporaryFile(mode="w", delete=False, dir=".")

        # Write spike data to the temporary file
        times = defaultdict(list)
        unique_ids = []
        spike_data = []
        for pop_data in self.spike_data:
            for i, (time, id) in enumerate(zip(pop_data["times"], pop_data["ids"])):
                print(f"{id} {time}", file=spike_file)
                if id not in times:
                    times[id] = []
                times[id].append(time)
                unique_ids.append(id)
        max_time = max(max(times[id]) for id in times)
        max_id = max(unique_ids)
        for id in unique_ids:
            spike_data.append(
                {
                    "name": f"Population_{id}",
                    "times": times[id],
                    "ids": [id] * len(times[id]),
                }
            )

        spike_file.flush()
        spike_file.close()

        # Generate a plot from the spike time file and save it to a file
        pyplts.plot_spikes(
            spike_data,
            show_plots_already=False,
            save_spike_plot_to="spike-plot-from-file-test.png",
        )
        self.assertIsFile("spike-plot-from-file-test.png")

        # Clean up the generated files
        os.unlink("spike-plot-from-file-test.png")
        os.unlink(spike_file.name)

    @unittest.skip("Skipping until write_spike_data_to_hdf5 is implemented")
    def test_plot_spikes_from_sonata_file(self):
        """Test the plot_spikes function with a SONATA-format HDF5 file."""
        spike_data = [
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
            format="sonata",
            show_plots_already=False,
            save_figure_to="spike-plot-from-sonata-test.png",
        )
        self.assertIsFile("spike-plot-from-sonata-test.png")

        # Clean up the generated files
        os.unlink("spike-plot-from-sonata-test.png")
        os.unlink(hdf5_file.name)


if __name__ == "__main__":
    unittest.main()
