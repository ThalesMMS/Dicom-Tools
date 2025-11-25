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
