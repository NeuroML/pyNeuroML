import logging
import os
import unittest
from functools import lru_cache

import pytest
from neuroml import Cell
from parameterized import parameterized

from pyneuroml.io import read_neuroml2_file
from pyneuroml.swc.ExportNML import convert_swc_to_neuroml

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
    @lru_cache(maxsize=10000)
    def compare_segment_points(self, cell1, cell2, seg1, seg2):
        """Compare two segments"""
        distal_match = (
            (float(seg1.distal.x) == float(seg2.distal.x))
            and (float(seg1.distal.y) == float(seg2.distal.y))
            and (float(seg1.distal.z) == float(seg2.distal.z))
            and (float(seg1.distal.diameter) == float(seg2.distal.diameter))
        )

        prox1 = cell1.get_actual_proximal(seg1.id)
        prox2 = cell2.get_actual_proximal(seg2.id)

        proximal_match = (
            (float(prox1.x) == float(prox2.x))
            and (float(prox1.y) == float(prox2.y))
            and (float(prox1.z) == float(prox2.z))
            and (float(prox1.diameter) == float(prox2.diameter))
        )

        return distal_match and proximal_match

    def compare_to_cvapp_output(
        self, cvapp_output_file, exported_nml_doc, test_segments
    ):
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
        :param test_segments: toggle whether individual segments should also be
            compared. For larger models, this can take a long time, so we turn
            this off for them
        :type test_segments: bool

        """
        cvapp_doc = read_neuroml2_file(cvapp_output_file)

        num_segments_cvapp = len(cvapp_doc.morphology[0].segments)
        num_segments_nml = len(exported_nml_doc.morphology[0].segments)

        if test_segments:
            # create cells to be able to use cell functions like get_segment
            cell_cvapp = Cell(id="cell_cvapp", morphology=cvapp_doc.morphology[0])
            cell_nml = Cell(id="cell_nml", morphology=exported_nml_doc.morphology[0])

            # Match parents and distal points
            # Do not match proximal points because our exporter does unbranched
            # segment groups differently from CVapp, and adds proximal points to
            # the root segments of all unbranched segment groups.
            matched = []
            for seg_cvapp in cvapp_doc.morphology[0].segments:
                for seg_nml in exported_nml_doc.morphology[0].segments:
                    # already matched, don't bother matching again
                    if seg_nml in matched:
                        continue

                    logger.debug(f"Comparing {seg_cvapp} - {seg_nml}")

                    # compare the distals of the segments
                    if self.compare_segment_points(
                        cell_cvapp, cell_nml, seg_cvapp, seg_nml
                    ):
                        # Parents: we can't just compare the parent segment IDs
                        # because there is no guarantee that the order of the
                        # segments, and thus the segment ids, are the same. So, we
                        # also go and match the distals of the parents

                        # we do not mark parents as matched because we're not
                        # testing their parents too, we'll do that again when we
                        # match the parents explicitly

                        # both none: fine
                        if seg_cvapp.parent is None and seg_nml.parent is None:
                            matched.append(seg_nml)
                            logger.debug("Matched")
                            break

                        # both not None
                        elif seg_cvapp.parent and seg_nml.parent:
                            parent_cvapp = cell_cvapp.get_segment(
                                seg_cvapp.parent.segments
                            )
                            parent_nml = cell_nml.get_segment(seg_nml.parent.segments)

                            if self.compare_segment_points(
                                cell_cvapp, cell_nml, parent_cvapp, parent_nml
                            ):
                                matched.append(seg_nml)
                                logger.debug("Matched")
                                break

                        # one is none, one isn't, no match
                        else:
                            pass

            len_matched = len(list(set(matched)))

            # list of ones that didn't match
            unmatched = set(matched) ^ set(exported_nml_doc.morphology[0].segments)

            self.assertEqual(
                len_matched,
                num_segments_nml,
                f"Number of segments does not match: (cvapp: {num_segments_cvapp} vs nml: {num_segments_nml}): {unmatched}",
            )
        else:
            self.assertEqual(
                num_segments_cvapp,
                num_segments_nml,
                f"Number of segments does not match: (cvapp: {num_segments_cvapp} vs nml: {num_segments_nml})",
            )

    # https://pypi.org/project/parameterized/#description
    @parameterized.expand(
        [
            ("Case1_new.swc", True),
            ("Case2_new.swc", True),
            ("Case3_new.swc", True),
            ("Case4_new.swc", True),
            ("Case5_new.swc", True),
            ("dCH-cobalt.CNG_small.swc", True),
            ("l22_cylsoma.swc", True),
            ("l22_small.swc", True),
            ("l22_sphersoma.swc", True),
            # ("dCH-cobalt.CNG.swc", False), # takes too long to test
            # "l22.swc", # UNKNOWN_PARENT: skip for time being
        ]
    )
    def test_swc_conversions(self, swc_file, test_segments):
        "Test SWC conversions"
        swc_nml_file = swc_file.replace(".swc", "_cvapp.morph.nml")
        nml_file = swc_file.replace(".swc", "_pynml.morph.nml")
        nml_output = convert_swc_to_neuroml(swc_file, nml_file, True)

        self.compare_to_cvapp_output(swc_nml_file, nml_output, test_segments)
        os.unlink(nml_file)


if __name__ == "__main__":
    unittest.main()
