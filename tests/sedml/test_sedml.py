#!/usr/bin/env python3

import os
import stat

from pyneuroml import sedml


def test_sedml_validate_a_valid_file():
    "ensure it validates a single valid file by returning True"

    fname = "tests/sedml/test_data/valid_doc.sedml"
    result = sedml.validate_sedml_files([fname])
    assert result


def test_sedml_validate_missing_sourcefile():
    try:
        result = sedml.validate_sedml_files(
            ["tests/sedml/test_data/missing_model_source.sedml"]
        )
        assert not result
        return
    except Exception:
        pass

    raise Exception("failed to properly flag missing source file")


def test_sedml_validate_missing_inputfile():
    try:
        sedml.validate_sedml_files(["tests/sedml/test_data/nonexistent_file"])
    except FileNotFoundError:
        return
    except Exception:
        pass

    raise Exception("failed to properly flag file not found error")


def test_sedml_validate_no_read_access():
    fname = "tests/sedml/test_data/no_read_access.sedml"

    # Remove read permission
    os.chmod(fname, 0)
    try:
        sedml.validate_sedml_files([fname])
    except IOError:
        os.chmod(fname, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        return
    except Exception:
        pass

    os.chmod(
        fname, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH
    )  # Restore permission for git
    raise Exception("failed to properly flag lack of read access")


def test_sedml_validate_valueerror_on_no_inputfiles():
    "ensure it raises a ValueError exception for failing to provide any files"

    try:
        sedml.validate_sedml_files([])
    except ValueError:
        return
    except Exception:
        pass

    raise Exception("failed to properly flag missing input files")


def test_sedml_validate_flag_all_invalid_files():
    """
    ensure it returns False for all invalid files
    without raising any exceptions
    """

    fail_count = 0
    n_files = 2

    for i in range(n_files):
        fname = "tests/sedml/test_data/invalid_doc%02d.sedml" % (i + 1)
        try:
            result = sedml.validate_sedml_files([fname])
            if not result:
                fail_count += 1
        except Exception:
            pass

    assert fail_count == n_files


if __name__ == "__main__":
    test_sedml_validate_a_valid_file()
    test_sedml_validate_flag_all_invalid_files()
    test_sedml_validate_valueerror_on_no_inputfiles()
    test_sedml_validate_missing_inputfile()
    test_sedml_validate_no_read_access()
    test_sedml_validate_missing_sourcefile()
