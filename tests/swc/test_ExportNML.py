import glob
import os
import unittest

import pytest

from pyneuroml.io import read_neuroml2_file
from pyneuroml.swc.ExportNML import convert_swc_to_neuroml


@pytest.fixture(scope="class", autouse=True)
def change_test_dir(request):
    # Store the current working directory
    original_dir = os.getcwd()

    # Change to the desired directory
    os.chdir("./tests/swc/")

    # After the test class completes, revert to the original directory
    def teardown():
        os.chdir(original_dir)

    request.addfinalizer(teardown)


# Define a test class for NeuroMLWriter
class TestNeuroMLWriter(unittest.TestCase):
    def compare_to_cvapp_output(self, cvapp_output_file, exported_nml_doc):
        """Compare our export to the CVApp output.

        Ideally, we need to match pretty much exactly---apart from the strings
        that are used in IDs and so on.

        Things we check:

        - same number of segments


        Things we don't currently check:

        - same number of segment groups: CVApp generates ones based on color
          and so on too and our implementation will not match that.

        :param cvapp_output_file: name of CVApp conversion file
        :type cvapp_output_file: str
        :param exported_nml_doc: our NeuroML export
        :type exported_nml_doc: NeuroMLDocument
        """
        cvapp_doc = read_neuroml2_file(cvapp_output_file)

        num_segments_cvapp = len(cvapp_doc.morphology[0].segments)

        num_segments_nml = len(exported_nml_doc.morphology[0].segments)

        self.assertEqual(num_segments_cvapp, num_segments_nml, "Segments do not match")

    def test_case1_single_contour_soma(self):
        "Test case 1: single contour soma"
        swc_file = "Case1_new.swc"
        swc_nml_file = swc_file.replace(".swc", "_cvapp.morph.nml")
        nml_file = swc_file.replace(".swc", "_pynml.morph.nml")
        nml_output = convert_swc_to_neuroml(swc_file, nml_file, True)

        self.compare_to_cvapp_output(swc_nml_file, nml_output)
        os.unlink(nml_file)

    def test_case2_no_soma(self):
        "Test case for a neuron with no soma"
        swc_file = "Case2_new.swc"
        swc_nml_file = swc_file.replace(".swc", "_cvapp.morph.nml")
        nml_file = swc_file.replace(".swc", "_pynml.morph.nml")
        nml_output = convert_swc_to_neuroml(swc_file, nml_file, True)

        self.compare_to_cvapp_output(swc_nml_file, nml_output)
        os.unlink(nml_file)

    def test_case3_multiple_contours_soma(self):
        "Test case for multiple contour soma"
        swc_file = "Case3_new.swc"
        swc_nml_file = swc_file.replace(".swc", "_cvapp.morph.nml")
        nml_file = swc_file.replace(".swc", "_pynml.morph.nml")
        nml_output = convert_swc_to_neuroml(swc_file, nml_file, True)

        self.compare_to_cvapp_output(swc_nml_file, nml_output)
        os.unlink(nml_file)

    def test_case4_multiple_cylinder_soma(self):
        "Test case for multiple cylinder soma"
        swc_file = "Case4_new.swc"
        swc_nml_file = swc_file.replace(".swc", "_cvapp.morph.nml")
        nml_file = swc_file.replace(".swc", "_pynml.morph.nml")
        nml_output = convert_swc_to_neuroml(swc_file, nml_file, True)

        self.compare_to_cvapp_output(swc_nml_file, nml_output)
        os.unlink(nml_file)

    def test_case5_spherical_soma(self):
        "Test case for spherical soma"
        swc_file = "Case5_new.swc"
        swc_nml_file = swc_file.replace(".swc", "_cvapp.morph.nml")
        nml_file = swc_file.replace(".swc", "_pynml.morph.nml")
        nml_output = convert_swc_to_neuroml(swc_file, nml_file, True)

        self.compare_to_cvapp_output(swc_nml_file, nml_output)
        os.unlink(nml_file)


if __name__ == "__main__":
    unittest.main()
