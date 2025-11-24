#
# test_dicom_numpy.py
# Dicom-Tools-py
#
# Verifies dicom-numpy can combine synthetic slices into volumes with expected affine.
#
# Thales Matheus Mendonça Santos - November 2025

import pytest
import numpy as np

dicom_numpy = pytest.importorskip("dicom_numpy")


def test_dicom_numpy_combine_slices(synthetic_datasets):
    # combine_slices should honor slice count and shape from the synthetic fixtures
    voxel_array, affine = dicom_numpy.combine_slices(synthetic_datasets)

    assert sorted(voxel_array.shape) == sorted((len(synthetic_datasets), 32, 32))
    assert affine.shape == (4, 4)
    assert np.allclose(affine[2, 2], 1.0)
