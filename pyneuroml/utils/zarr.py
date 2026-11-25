#!/usr/bin/env python3
"""
Utilities for storing NeuroML simulation generated data in Zarr format.

File: pyneuroml/utils/zarr.py

Copyright 2026 NeuroML contributors
"""

import logging
import typing
from pathlib import Path

import numpy as np
import zarr

from pyneuroml.utils.simdata import load_traces_from_data_file

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def data_files_to_zarr(
    data_file_names: typing.Union[str, typing.List[str]],
    zarr_file_path: str,
    columns: typing.Optional[typing.List[int]] = None,
    compressor: typing.Any = None,
    overwrite: bool = False,
) -> None:
    """Convert NeuroML simulation generated data from data files to Zarr format.

    .. versionadded:: 1.2.2

    This function reads time series data from NeuroML simulation data files
    and stores it in Zarr format for efficient storage and access.

    :param data_file_names: name/path to data file(s)
    :type data_file_names: str or list of strings
    :param zarr_file_path: path to output Zarr file
    :type zarr_file_path: str
    :param columns: column indices to include (default: all except time column)
    :type columns: list of ints: [1, 2, 3]
    :param compressor: Zarr compressor to use (default: None)
    :type compressor: zarr.Compressor or None
    :param overwrite: whether to overwrite existing Zarr file (default: False)
    :type overwrite: bool
    :returns: None

    """
    # Load data from the data files
    all_traces = load_traces_from_data_file(data_file_names, columns)

    # Create or open the Zarr group
    zarr_path = Path(zarr_file_path)
    if zarr_path.exists() and not overwrite:
        raise FileExistsError(
            f"Zarr file {zarr_file_path} already exists. Set overwrite=True to overwrite."
        )

    # Remove existing file if overwrite is True
    if overwrite and zarr_path.exists():
        import shutil

        shutil.rmtree(zarr_path)

    # Create main zarr group
    zarr_group = zarr.open(zarr_file_path, mode="w")

    # Store each dataset
    for file_name, traces in all_traces.items():
        # Use just the basename as the group name to avoid path nesting
        base_name = Path(file_name).name
        file_group = zarr_group.create_group(base_name)

        # Store time data using direct assignment (the correct way)
        time_data = traces["t"]
        file_group["time"] = time_data

        # Store each data column
        for key, data in traces.items():
            if key != "t":  # Skip the time key as we already stored it
                file_group[key] = data

    logger.info(f"Successfully converted data files to Zarr format at {zarr_file_path}")
