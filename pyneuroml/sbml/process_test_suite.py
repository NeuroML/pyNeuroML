#!/usr/bin/env python3

"""
produce a markdown table of the results of running various tests on the SBML Test Suite
"""

import os
import glob
from pyneuroml.sbml import validate_sbml_files


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
        help="Path to cases directory, eg '~/repos/sbml-test-suite/cases'",
    )

    parser.add_argument(
        "--case-glob",
        action="store",
        type=str,
        default="semantic/000*/*-sbml-l3v2.xml",
        help="Shell-style glob matching case file(s) within case_path, eg 'semantic/000*/*-sbml-l3v2.xml'",
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

    header = "|case|valid|strict-units valid|\n"
    row = "|{case}|{valid}|{strict}|\n"

    with open(args.output_file, "w") as fout:
        os.chdir(args.case_path)
        fout.write(header)
        for fpath in glob.glob(args.case_glob):
            print(fpath)
            assert os.path.isfile(fpath)
            case = os.path.basename(fpath)
            valid = validate_sbml_files([fpath], strict_units=False)
            strict = validate_sbml_files([fpath], strict_units=True)
            fout.write(row.format(**locals()))


if __name__ == "__main__":
    args = parse_arguments()

    process_cases(args)
