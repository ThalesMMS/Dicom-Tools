#
# conftest.py
# Dicom-Tools-py
#
# Provides pytest fixtures that generate synthetic DICOM series and datasets for test cases.
#
# Thales Matheus Mendonça Santos - November 2025

import pytest

from DICOM_reencoder.core import load_dataset
from DICOM_reencoder.core.factories import build_synthetic_series


@pytest.fixture(scope="function")
def synthetic_series(tmp_path):
    # Generate a small, deterministic CT series for downstream tests
    paths = build_synthetic_series(tmp_path / "series")
    datasets = [load_dataset(p) for p in paths]
    return paths, datasets


@pytest.fixture(scope="function")
def synthetic_dicom_path(synthetic_series):
    return synthetic_series[0][0]


@pytest.fixture(scope="function")
def synthetic_datasets(synthetic_series):
    return synthetic_series[1]
