#!/usr/bin/env python3

import os
import stat

from pyneuroml import sbml


def test_sbml_validate_a_valid_file():
    "ensure it validates a single valid file by returning True"

    fname = "tests/sbml/test_data/valid_doc.sbml"
    result = sbml.validate_sbml_files([fname])
    assert result


def test_sbml_validate_missing_inputfile():
    try:
        sbml.validate_sbml_files(["tests/sbml/test_data/nonexistent_file"])
    except FileNotFoundError:
        return
    except Exception:
        pass

    raise Exception("failed to properly flag file not found error")


def test_sbml_validate_no_read_access():
    fname = "tests/sbml/test_data/no_read_access.sbml"

    # Remove read permission
    os.chmod(fname, 0)
    try:
        sbml.validate_sbml_files([fname])
    except IOError:
        os.chmod(fname, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        return
    except Exception:
        pass

    os.chmod(
        fname, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH
    )  # Restore permission for git
    raise Exception("failed to properly flag lack of read access")


def test_sbml_validate_valueerror_on_no_inputfiles():
    "ensure it raises a ValueError exception for failing to provide any files"

    try:
        sbml.validate_sbml_files([])
    except ValueError:
        return
    except Exception:
        pass

    raise Exception("failed to properly flag missing input files")


def test_sbml_validate_unit_consistency_check():
    """
    ensure it fails a unit inconsistency in strict mode
    ensure it only warns about a unit inconsistency when not in strict mode
    """

    try:
        result = sbml.validate_sbml_files(
            ["tests/sbml/test_data/inconsistent_units_doc.sbml"], strict_units=True
        )
        assert not result
    except Exception:
        raise Exception("failed to flag inconsistent units as an error")

    try:
        result = sbml.validate_sbml_files(
            ["tests/sbml/test_data/inconsistent_units_doc.sbml"], strict_units=False
        )
        assert result
    except Exception:
        raise Exception("failed to flag inconsistent units as an error")


def test_sbml_validate_flag_all_invalid_files():
    """
    ensure it returns False for all invalid files
    without raising any exceptions
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
    test_sbml_validate_valueerror_on_no_inputfiles()
    test_sbml_validate_missing_inputfile()
    test_sbml_validate_flag_all_invalid_files()
    test_sbml_validate_unit_consistency_check()
    test_sbml_validate_no_read_access()
