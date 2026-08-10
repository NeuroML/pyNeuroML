#!/usr/bin/env python3
"""
Tests related to pyneuroml.utils.zarr module

File: tests/utils/test_zarr.py

Copyright 2026 NeuroML contributors
"""

import logging
import os
import tempfile
import unittest

import pyneuroml.utils.zarr as zarr_utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestZarrModule(unittest.TestCase):
    """Test the zarr module"""

    def test_data_files_to_zarr(self):
        """Test the data_files_to_zarr function"""

        # Create sample data file content
        data_content = """\
0.0     -0.06     0.01
1.0E-4  -0.05993  0.02
2.0E-4  -0.05986  0.03
3.0E-4  -0.05979  0.04
4.0E-4  -0.05972  0.05
5.0E-4  -0.05965  0.06
6.0E-4  -0.05959  0.07
7.0E-4  -0.05952  0.08
8.0E-4  -0.05946  0.09
9.0E-4  -0.05940  0.10
0.001   -0.05934  0.11"""

        # Create temporary data file
        data_file = tempfile.NamedTemporaryFile(mode="w", delete=False, dir=".")
        print(data_content, file=data_file)
        data_file.flush()
        data_file.close()

        # Create temporary directory for zarr (since zarr creates directory structure)
        zarr_dir = tempfile.mkdtemp(suffix="_zarr_test")
        zarr_file = os.path.join(zarr_dir, "test_data.zarr")

        try:
            # Test conversion
            zarr_utils.data_files_to_zarr(data_file.name, zarr_file)

            # Verify zarr directory was created
            self.assertTrue(os.path.exists(zarr_file))
            self.assertTrue(os.path.isdir(zarr_file))

            # Test basic structure - just check that it can be opened
            import zarr

            zarr_group = zarr.open(zarr_file, mode="r")

            # Check that we have the expected structure (basic check)
            file_name = os.path.basename(data_file.name)
            self.assertTrue(file_name in list(zarr_group.keys()))

        finally:
            # Clean up temporary files
            if os.path.exists(data_file.name):
                os.unlink(data_file.name)
            if os.path.exists(zarr_dir):
                import shutil

                shutil.rmtree(zarr_dir)

    def test_data_files_to_zarr_with_columns(self):
        """Test the data_files_to_zarr function with column selection"""

        # Create sample data file content
        data_content = """\
0.0     -0.06     0.01     0.02
1.0E-4  -0.05993  0.02     0.03
2.0E-4  -0.05986  0.03     0.04"""

        # Create temporary data file
        data_file = tempfile.NamedTemporaryFile(mode="w", delete=False, dir=".")
        print(data_content, file=data_file)
        data_file.flush()
        data_file.close()

        # Create temporary directory for zarr
        zarr_dir = tempfile.mkdtemp(suffix="_zarr_test")
        zarr_file = os.path.join(zarr_dir, "test_data.zarr")

        try:
            # Test conversion with column selection (only second column)
            zarr_utils.data_files_to_zarr(data_file.name, zarr_file, columns=[2])

            # Verify zarr directory was created
            self.assertTrue(os.path.exists(zarr_file))
            self.assertTrue(os.path.isdir(zarr_file))

            # Test basic structure - just check that it can be opened
            import zarr

            zarr_group = zarr.open(zarr_file, mode="r")

            # Check that we have the expected structure (basic check)
            file_name = os.path.basename(data_file.name)
            self.assertTrue(file_name in list(zarr_group.keys()))

        finally:
            # Clean up temporary files
            if os.path.exists(data_file.name):
                os.unlink(data_file.name)
            if os.path.exists(zarr_dir):
                import shutil

                shutil.rmtree(zarr_dir)

    def test_data_files_to_zarr_overwrite(self):
        """Test the data_files_to_zarr function with overwrite option"""

        # Create sample data file content
        data_content = """\
0.0     -0.06
1.0E-4  -0.05993"""

        # Create temporary data file
        data_file = tempfile.NamedTemporaryFile(mode="w", delete=False, dir=".")
        print(data_content, file=data_file)
        data_file.flush()
        data_file.close()

        # Create temporary directory for zarr
        zarr_dir = tempfile.mkdtemp(suffix="_zarr_test")
        zarr_file = os.path.join(zarr_dir, "test_data.zarr")

        try:
            # Create initial zarr file
            zarr_utils.data_files_to_zarr(data_file.name, zarr_file, overwrite=False)

            # Try to create again without overwrite - should raise exception
            with self.assertRaises(FileExistsError):
                zarr_utils.data_files_to_zarr(
                    data_file.name, zarr_file, overwrite=False
                )

            # Try with overwrite=True - should succeed
            zarr_utils.data_files_to_zarr(data_file.name, zarr_file, overwrite=True)

            # Verify the file still exists
            self.assertTrue(os.path.exists(zarr_file))
            self.assertTrue(os.path.isdir(zarr_file))

        finally:
            # Clean up temporary files
            if os.path.exists(data_file.name):
                os.unlink(data_file.name)
            if os.path.exists(zarr_dir):
                import shutil

                shutil.rmtree(zarr_dir)


if __name__ == "__main__":
    unittest.main()
