#!/usr/bin/env python3

"""
produce a markdown table of the results of running various tests on the SBML Test Suite

get the version of the test suite that includes sedml versions
https://github.com/sbmlteam/sbml-test-suite/releases/download/3.4.0/semantic_tests_with_sedml_and_graphs.v3.4.0.zip


"""

import os
import glob
from pyneuroml.sbml import validate_sbml_files
from pyneuroml.sedml import validate_sedml_files


def parse_arguments():
    "Parse command line arguments"

    import argparse

    parser = argparse.ArgumentParser(
        description="Run various tests on the SBML Test Suite"
    )

    parser.add_argument(
        "--case-path",
        action="store",
        type=str,
        default=".",
        help="Path to cases directory, eg '~/repos/sbml-test-suite/cases/semantic'",
    )

    parser.add_argument(
        "--case-glob",
        action="store",
        type=str,
        default="000*/*-sbml-l3v2.xml",
        help="Shell-style glob matching case file(s) within case_path, eg '000*/*-sbml-l3v2.xml'",
    )

    parser.add_argument(
        "--output-file",
        action="store",
        type=str,
        default="results.md",
        help="Path to file results will be written to, any parent directories must exist, eg ./results.md",
    )

    return parser.parse_args()


def process_cases(args):
    "process the test cases and write results out as a markdown table"

    header = "|case|valid-sbml|valid-sbml-units|valid-sedml|\n"
    row = "|{case}|{valid_sbml}|{valid_sbml_units}|{valid_sedml}|\n"

    with open(args.output_file, "w") as fout:
        os.chdir(args.case_path)
        fout.write(header)
        for fpath in sorted(glob.glob(args.case_glob)):
            sedml_path = fpath.replace(".xml", "-sedml.xml")
            print(fpath)
            assert os.path.isfile(fpath)
            assert os.path.isfile(sedml_path)
            case = os.path.basename(fpath)
            valid_sbml = validate_sbml_files([fpath], strict_units=False)
            valid_sbml_units = validate_sbml_files([fpath], strict_units=True)
            valid_sedml = validate_sedml_files([sedml_path])
            fout.write(row.format(**locals()))


if __name__ == "__main__":
    args = parse_arguments()

    process_cases(args)
