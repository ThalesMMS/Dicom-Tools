#
# test_dicom_numpy.py
# Dicom-Tools-py
#
# Verifies dicom-numpy stacking under shuffles, duplicates, multi-echo groupings, and compares with SimpleITK.
#
# Thales Matheus Mendonça Santos - November 2025

import numpy as np
import pytest
from pydicom.uid import generate_uid

dicom_numpy = pytest.importorskip("dicom_numpy")


def test_dicom_numpy_combine_slices(synthetic_datasets):
    # combine_slices should honor slice count and shape from the synthetic fixtures
    voxel_array, affine = dicom_numpy.combine_slices(synthetic_datasets)

    assert sorted(voxel_array.shape) == sorted((len(synthetic_datasets), 32, 32))
    assert affine.shape == (4, 4)
    assert np.allclose(affine[2, 2], 1.0)


def test_dicom_numpy_handles_shuffled_instance_numbers(synthetic_datasets):
    shuffled = list(reversed(synthetic_datasets))
    voxel_array, _ = dicom_numpy.combine_slices(shuffled)
    assert sorted(voxel_array.shape) == sorted((len(shuffled), 32, 32))


def test_dicom_numpy_duplicate_slice_raises_clear_error(synthetic_datasets):
    duplicated = synthetic_datasets + [synthetic_datasets[-1]]
    with pytest.raises(dicom_numpy.DicomImportException):
        dicom_numpy.combine_slices(duplicated)


def test_dicom_numpy_multi_echo_groups_stack_into_extra_axis(synthetic_datasets):
    # Create two echoes by copying datasets and assigning EchoNumbers/UIDs
    echo1 = []
    echo2 = []
    for ds in synthetic_datasets:
        ds1 = ds.copy()
        ds1.EchoNumbers = 1
        ds1.SOPInstanceUID = generate_uid()
        ds2 = ds.copy()
        ds2.EchoNumbers = 2
        ds2.SOPInstanceUID = generate_uid()
        echo1.append(ds1)
        echo2.append(ds2)

    volume1, affine1 = dicom_numpy.combine_slices(echo1)
    volume2, affine2 = dicom_numpy.combine_slices(echo2)
    stacked = np.stack([volume1, volume2], axis=0)

    assert stacked.shape[0] == 2
    assert stacked.shape[1:3] == (32, 32)
    assert stacked.shape[3] == len(synthetic_datasets)
    assert np.allclose(affine1, affine2)


def test_dicom_numpy_affine_matches_simpleitk_spacing(synthetic_series, synthetic_datasets):
    sitk = pytest.importorskip("SimpleITK")

    voxel_array, affine = dicom_numpy.combine_slices(synthetic_datasets)
    spacing_from_affine = np.linalg.norm(affine[:3, :3], axis=0)

    paths, _ = synthetic_series
    image = sitk.ReadImage([str(p) for p in paths])
    sitk_spacing = np.array(image.GetSpacing())

    assert voxel_array.shape[0:2] == (32, 32)
    assert voxel_array.shape[2] == len(synthetic_datasets)
    assert np.allclose(sorted(spacing_from_affine), sorted(sitk_spacing))
