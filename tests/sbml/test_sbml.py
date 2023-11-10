#!/usr/bin/env python3

from pyneuroml import sbml


def test_validate_sbml_files1():
    "ensure it validates a single valid file by returning True"

    fname = "tests/sbml/test_data/valid_doc.sbml"
    result = sbml.validate_sbml_files([fname])
    assert result


def test_validate_sbml_files2():
    "ensure it raises an exception for failing to provide any files"

    try:
        result = sbml.validate_sbml_files([])
    except Exception:
        return

    raise Exception("failed to flag missing input files")


def test_validate_sbml_files3():
    """
    ensure it returns False for all invalid files
    without raising any exception
    """

    fail_count = 0
    n_files = 3

    for i in range(n_files):
        fname = "tests/sbml/test_data/invalid_doc%02d.sbml" % i

        try:
            result = sbml.validate_sbml_files([fname])
            if not result:
                fail_count += 1
        except Exception:
            pass

    assert fail_count == n_files


if __name__ == "__main__":
    test_validate_sbml_files1()
    test_validate_sbml_files2()
    test_validate_sbml_files3()
