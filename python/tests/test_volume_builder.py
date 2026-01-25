#
# test_volume_builder.py
# Dicom-Tools-py
#
# Tests for 3D volume building: slice combination, affine matrix generation,
# metadata extraction, and dicom-numpy integration.
#
# Thales Matheus Mendonça Santos - November 2025

from pathlib import Path

import numpy as np
import pytest

dicom_numpy = pytest.importorskip("dicom_numpy")

from DICOM_reencoder.volume_builder import build_volume, _load_sorted_datasets


class TestLoadSortedDatasets:
    """Test dataset loading and sorting."""

    def test_load_sorted_datasets_basic(self, synthetic_series):
        paths, _ = synthetic_series
        dicom_dir = Path(paths[0]).parent

        datasets = _load_sorted_datasets(dicom_dir)

        assert len(datasets) >= len(paths)
        assert all(isinstance(ds, type(datasets[0])) for ds in datasets)

    def test_load_sorted_datasets_sorted_by_instance(self, synthetic_series):
        paths, _ = synthetic_series
        dicom_dir = Path(paths[0]).parent

        datasets = _load_sorted_datasets(dicom_dir)

        # Should be sorted by InstanceNumber
        instance_numbers = [getattr(ds, "InstanceNumber", 0) for ds in datasets]
        assert instance_numbers == sorted(instance_numbers)

    def test_load_sorted_datasets_empty_directory(self, tmp_path):
        with pytest.raises(RuntimeError):
            _load_sorted_datasets(tmp_path)


class TestBuildVolume:
    """Test 3D volume building."""

    def test_build_volume_basic(self, synthetic_series):
        paths, _ = synthetic_series
        dicom_dir = Path(paths[0]).parent

        volume, affine, metadata = build_volume(dicom_dir)

        assert volume.ndim == 3
        assert volume.shape[2] >= len(paths)  # z dimension
        assert affine.shape == (4, 4)
        assert isinstance(metadata, dict)

    def test_build_volume_affine_properties(self, synthetic_series):
        paths, _ = synthetic_series
        dicom_dir = Path(paths[0]).parent

        volume, affine, metadata = build_volume(dicom_dir)

        # Affine should have last row [0, 0, 0, 1]
        assert np.allclose(affine[3, :], [0, 0, 0, 1])

        # Affine should be invertible
        det = np.linalg.det(affine)
        assert not np.isclose(det, 0)

    def test_build_volume_metadata_structure(self, synthetic_series):
        paths, _ = synthetic_series
        dicom_dir = Path(paths[0]).parent

        volume, affine, metadata = build_volume(dicom_dir)

        assert "shape" in metadata
        assert "dtype" in metadata
        assert "affine" in metadata
        assert "spacing_mm" in metadata
        assert "stats" in metadata

    def test_build_volume_metadata_stats(self, synthetic_series):
        paths, _ = synthetic_series
        dicom_dir = Path(paths[0]).parent

        volume, affine, metadata = build_volume(dicom_dir)

        stats = metadata["stats"]
        assert "min" in stats
        assert "max" in stats
        assert "mean" in stats
        assert "std" in stats

        # Stats should match volume
        assert stats["min"] == float(volume.min())
        assert stats["max"] == float(volume.max())
        assert stats["mean"] == pytest.approx(float(volume.mean()))
        assert stats["std"] == pytest.approx(float(volume.std()))

    def test_build_volume_spacing(self, synthetic_series):
        paths, _ = synthetic_series
        dicom_dir = Path(paths[0]).parent

        volume, affine, metadata = build_volume(dicom_dir)

        spacing = metadata["spacing_mm"]
        assert len(spacing) == 3  # x, y, z spacing
        assert all(s > 0 for s in spacing)

    def test_build_volume_shape_matches_metadata(self, synthetic_series):
        paths, _ = synthetic_series
        dicom_dir = Path(paths[0]).parent

        volume, affine, metadata = build_volume(dicom_dir)

        assert metadata["shape"] == list(volume.shape)
        assert metadata["dtype"] == str(volume.dtype)

    def test_build_volume_series_uid_preserved(self, synthetic_series):
        paths, _ = synthetic_series
        dicom_dir = Path(paths[0]).parent

        # Get original series UID
        import pydicom
        original_ds = pydicom.dcmread(paths[0], force=True)
        original_series_uid = original_ds.SeriesInstanceUID

        volume, affine, metadata = build_volume(dicom_dir)

        assert metadata["series_uid"] == original_series_uid

    def test_build_volume_handles_single_slice(self, tmp_path):
        from DICOM_reencoder.core import build_synthetic_series

        # Create series with single slice
        paths = build_synthetic_series(tmp_path / "single", slices=1)
        dicom_dir = Path(paths[0]).parent

        volume, affine, metadata = build_volume(dicom_dir)

        # Should still produce 3D volume with depth 1
        assert volume.ndim == 3
        assert volume.shape[2] == 1

