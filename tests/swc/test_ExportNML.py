import os
import unittest

import pytest
from parameterized import parameterized

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
        - proximals and distals of segments

        Things we do not check

        - same number of segment groups and their composition because there are
          different ways of creating "unbranched segment groups". The way we do
          it in PyNeuroML is to create a new one from each branching point, but
          CVApp treats the soma as a special case. From a modelling
          perspective, both are correct because a simulator will be able to
          create sections (in NEURON) for example that result in the same
          biophysics.

        :param cvapp_output_file: name of CVApp conversion file
        :type cvapp_output_file: str
        :param exported_nml_doc: our NeuroML export
        :type exported_nml_doc: NeuroMLDocument
        """
        cvapp_doc = read_neuroml2_file(cvapp_output_file)

        num_segments_cvapp = len(cvapp_doc.morphology[0].segments)
        num_segments_nml = len(exported_nml_doc.morphology[0].segments)
        self.assertEqual(
            num_segments_cvapp, num_segments_nml, "Number of segments does not match"
        )

        # Match parents and distal points
        # Do not match proximal points because our exporter does unbranched
        # segment groups differently from CVapp, and adds proximal points to
        # the root segments of all unbranched segment groups.
        matched = []
        for seg in cvapp_doc.morphology[0].segments:
            for seg_nml in exported_nml_doc.morphology[0].segments:
                print(f"Comparing {seg} - {seg_nml}")
                if (
                    (float(seg.distal.x) == float(seg_nml.distal.x))
                    and (float(seg.distal.y) == float(seg_nml.distal.y))
                    and (float(seg.distal.z) == float(seg_nml.distal.z))
                    and (float(seg.distal.diameter) == float(seg_nml.distal.diameter))
                ):
                    if seg.parent and seg_nml.parent:
                        if seg.parent.segments == seg_nml.parent.segments:
                            matched.append(seg_nml)
                            print("Matched")
                            break
                    else:
                        matched.append(seg_nml)
                        print("Matched")
                        break

        self.assertEqual(len(matched), num_segments_nml, "All segments do not match")

    # https://pypi.org/project/parameterized/#description
    @parameterized.expand(
        [
            "Case1_new.swc",
            "Case2_new.swc",
            "Case3_new.swc",
            "Case4_new.swc",
            "Case5_new.swc",
        ]
    )
    def test_swc_conversions(self, swc_file):
        "Test SWC conversions"
        swc_nml_file = swc_file.replace(".swc", "_cvapp.morph.nml")
        nml_file = swc_file.replace(".swc", "_pynml.morph.nml")
        nml_output = convert_swc_to_neuroml(swc_file, nml_file, True)

        self.compare_to_cvapp_output(swc_nml_file, nml_output)
        os.unlink(nml_file)


if __name__ == "__main__":
    unittest.main()
