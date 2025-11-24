#
# datasets.py
# Dicom-Tools-py
#
# Handles reading and writing of DICOM datasets with basic pixel presence checks.
#
# Thales Matheus Mendonça Santos - November 2025

"""Dataset I/O helpers used across the toolkit."""

from pathlib import Path
from typing import Union

import pydicom
from pydicom.dataset import Dataset


def load_dataset(path: Union[str, Path], *, force: bool = True) -> Dataset:
    """Load a DICOM dataset from disk."""
    # `force=True` allows us to open partially non-compliant files without failing early
    return pydicom.dcmread(str(path), force=force)


def save_dataset(dataset: Dataset, path: Union[str, Path]) -> Path:
    """Persist a dataset to disk, ensuring the parent directory exists."""
    # Protect against missing parent directories before writing to disk
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.save_as(output_path)
    return output_path


def ensure_pixel_data(dataset: Dataset) -> None:
    """Raise if the dataset does not contain pixel data."""
    # Many utilities assume pixel data is present; fail fast with a clear message
    if "PixelData" not in dataset:
        raise ValueError("No pixel data present in the dataset")
