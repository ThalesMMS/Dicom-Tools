#
# test_simpleitk.py
# Dicom-Tools-py
#
# Validates SimpleITK series IO, registration, masking, and NIfTI roundtrips.
#
# Thales Matheus Mendonça Santos - November 2025

from pathlib import Path

import numpy as np
import pytest

sitk = pytest.importorskip("SimpleITK")


def _write_dicom_series(image: "sitk.Image", output_dir: Path) -> list[str]:
    writer = sitk.ImageSeriesWriter()
    file_names = [str(output_dir / f"slice_{i}.dcm") for i in range(image.GetDepth())]
    writer.SetFileNames(file_names)
    writer.SetImageIO("GDCMImageIO")
    try:
        writer.Execute(image, file_names, False, 0)
    except RuntimeError as exc:
        if "does not support writing a DICOM series" in str(exc):
            pytest.skip("SimpleITK build lacks DICOM series write support")
        raise
    return file_names


def test_simpleitk_filter_preserves_shape(synthetic_series):
    # SimpleITK filters should not alter voxel counts or basic dtype expectations
    paths, _ = synthetic_series
    image = sitk.ReadImage([str(p) for p in paths])
    smoothed = sitk.SmoothingRecursiveGaussian(image, sigma=1.5)

    array = sitk.GetArrayFromImage(smoothed)
    assert array.shape[0] == len(paths)
    assert array.shape[-2:] == (32, 32)
    assert array.dtype.kind in {"i", "u", "f"}


def test_simpleitk_series_io_preserves_spacing_and_direction(synthetic_series, tmp_path):
    paths, _ = synthetic_series
    image = sitk.ReadImage([str(p) for p in paths])
    output_dir = tmp_path / "dicom_output"
    output_dir.mkdir()

    file_names = _write_dicom_series(image, output_dir)
    reloaded = sitk.ReadImage(file_names)

    assert reloaded.GetSize() == image.GetSize()
    assert np.allclose(reloaded.GetSpacing(), image.GetSpacing())
    assert np.allclose(reloaded.GetDirection(), image.GetDirection())


def test_simpleitk_registration_recovers_translation(synthetic_series):
    paths, _ = synthetic_series
    fixed = sitk.Cast(sitk.ReadImage([str(p) for p in paths]), sitk.sitkFloat32)
    true_transform = sitk.TranslationTransform(3, (1.0, -1.0, 0.0))
    moving = sitk.Resample(fixed, true_transform, sitk.sitkLinear, 0.0, fixed.GetPixelID())

    registration = sitk.ImageRegistrationMethod()
    registration.SetMetricAsMeanSquares()
    registration.SetOptimizerAsRegularStepGradientDescent(
        learningRate=1.5, minStep=0.01, numberOfIterations=40, relaxationFactor=0.5
    )
    registration.SetInterpolator(sitk.sitkLinear)
    registration.SetInitialTransform(sitk.TranslationTransform(3))

    result = registration.Execute(fixed, moving)
    offset = np.array(result.GetOffset())
    expected = np.array(true_transform.GetOffset())
    assert np.linalg.norm(offset - expected) < 4.0


def test_simpleitk_label_statistics_with_mask(synthetic_series):
    paths, _ = synthetic_series
    image = sitk.ReadImage([str(p) for p in paths])
    mask = sitk.Cast(image > 10, sitk.sitkUInt8)

    stats = sitk.LabelStatisticsImageFilter()
    stats.Execute(image, mask)

    assert stats.HasLabel(1)
    assert stats.GetCount(1) > 0
    assert stats.GetMaximum(1) >= stats.GetMinimum(1)


def test_simpleitk_nifti_roundtrip_preserves_geometry(synthetic_series, tmp_path):
    paths, _ = synthetic_series
    image = sitk.ReadImage([str(p) for p in paths])

    nifti_path = tmp_path / "series.nii.gz"
    sitk.WriteImage(image, str(nifti_path))

    nifti_image = sitk.ReadImage(str(nifti_path))
    export_dir = tmp_path / "dicom_roundtrip"
    export_dir.mkdir()
    file_names = _write_dicom_series(nifti_image, export_dir)

    reloaded = sitk.ReadImage(file_names)
    assert np.allclose(reloaded.GetSpacing(), image.GetSpacing())
    assert np.allclose(reloaded.GetDirection(), image.GetDirection())


def test_simpleitk_segmentation_filters_match_expected_region():
    array = np.zeros((64, 64), dtype=np.uint8)
    array[20:44, 20:44] = 180
    image = sitk.GetImageFromArray(array)

    region_grow = sitk.ConnectedThreshold(image, seedList=[(32, 32)], lower=100, upper=255)
    mask = sitk.GetArrayFromImage(region_grow)
    assert np.count_nonzero(mask) == 24 * 24

    gradient = sitk.GradientMagnitude(image)
    watershed = sitk.MorphologicalWatershed(gradient, level=5.0, markWatershedLine=False)
    watershed_arr = sitk.GetArrayFromImage(watershed)
    assert watershed_arr.max() >= 1


def test_simpleitk_label_statistics_on_4d_and_multilabel_export(tmp_path):
    # Build a 4D volume with two time points to exercise LabelStatistics
    data = np.zeros((2, 2, 8, 8), dtype=np.float32)
    data[0, 0, 2:6, 2:6] = 5.0
    data[1, 1, 1:5, 1:5] = 9.0

    total_count = 0
    max_seen = 0
    for t in range(data.shape[0]):
        frame = sitk.GetImageFromArray(data[t])
        mask = sitk.GetImageFromArray((data[t] > 0).astype(np.uint8))
        stats = sitk.LabelStatisticsImageFilter()
        stats.Execute(frame, mask)

        assert stats.HasLabel(1)
        total_count += stats.GetCount(1)
        max_seen = max(max_seen, stats.GetMaximum(1))

    assert total_count == 2 * 16  # two labeled cubes of 4x4 voxels
    assert max_seen == 9.0

    # Multi-label mask export: generate one DICOM series per label
    multilabel = np.zeros((3, 8, 8), dtype=np.uint8)
    multilabel[0, 2:5, 2:5] = 1
    multilabel[1, 3:7, 3:7] = 2
    label_image = sitk.GetImageFromArray(multilabel)
    for label in (1, 2):
        binary = sitk.Equal(label_image, label)
        out_dir = tmp_path / f"label_{label}"
        out_dir.mkdir()
        file_names = _write_dicom_series(binary, out_dir)
        assert file_names
