#
# test_core_modules.py
# Dicom-Tools-py
#
# Tests for core modules: datasets I/O, images processing, metadata extraction,
# and network utilities.
#
# Thales Matheus Mendonça Santos - November 2025

import json
from pathlib import Path

import numpy as np
import pytest
import pydicom

from DICOM_reencoder.core.datasets import (
    dataset_from_dicom_json,
    dataset_to_dicom_json,
    ensure_pixel_data,
    load_dataset,
    save_dataset,
)
from DICOM_reencoder.core.images import (
    calculate_statistics,
    frame_to_png_bytes,
    get_frame,
    window_frame,
)
from DICOM_reencoder.core.metadata import summarize_metadata


class TestDatasetsIO:
    """Test dataset loading and saving."""

    def test_load_dataset_basic(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)

        assert isinstance(ds, pydicom.dataset.Dataset)
        assert hasattr(ds, "PatientName") or hasattr(ds, "Modality")

    def test_save_dataset_basic(self, synthetic_dicom_path, tmp_path):
        ds = load_dataset(synthetic_dicom_path)
        output = tmp_path / "saved.dcm"

        result = save_dataset(ds, output)

        assert result == output
        assert output.exists()

        # Verify can reload
        reloaded = load_dataset(output)
        assert reloaded.PatientName == ds.PatientName

    def test_save_dataset_creates_parent_dirs(self, synthetic_dicom_path, tmp_path):
        ds = load_dataset(synthetic_dicom_path)
        output = tmp_path / "nested" / "deep" / "saved.dcm"

        save_dataset(ds, output)

        assert output.exists()
        assert output.parent.exists()

    def test_ensure_pixel_data_with_pixels(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)

        # Should not raise
        ensure_pixel_data(ds)

    def test_ensure_pixel_data_without_pixels(self, tmp_path):
        import pydicom
        from pydicom.dataset import Dataset
        from pydicom.uid import generate_uid

        ds = Dataset()
        ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.1"
        ds.SOPInstanceUID = generate_uid()
        # No pixel data

        with pytest.raises(ValueError, match="No pixel data"):
            ensure_pixel_data(ds)


class TestDatasetJSON:
    """Test DICOM JSON serialization."""

    def test_dataset_to_dicom_json_basic(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)

        json_str = dataset_to_dicom_json(ds)

        assert isinstance(json_str, str)
        assert len(json_str) > 0

    def test_dataset_from_dicom_json_roundtrip(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)
        json_str = dataset_to_dicom_json(ds)

        reloaded = dataset_from_dicom_json(json_str)

        assert reloaded.PatientName == ds.PatientName
        assert reloaded.Modality == ds.Modality

    def test_dataset_from_dicom_json_dict(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)
        json_str = dataset_to_dicom_json(ds)
        json_dict = json.loads(json_str)

        reloaded = dataset_from_dicom_json(json_dict)

        assert reloaded.PatientName == ds.PatientName


class TestImagesProcessing:
    """Test image processing functions."""

    def test_get_frame_single_frame(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)

        frame = get_frame(ds, 0)

        assert isinstance(frame, np.ndarray)
        assert frame.ndim == 2

    def test_get_frame_multiframe(self, tmp_path):
        from DICOM_reencoder.core import build_multiframe_dataset, save_dataset

        ds = build_multiframe_dataset(frames=3, shape=(16, 16))
        input_file = tmp_path / "multiframe.dcm"
        save_dataset(ds, input_file)

        ds_loaded = load_dataset(input_file)
        frame = get_frame(ds_loaded, 0)

        assert isinstance(frame, np.ndarray)
        assert frame.ndim == 2
        assert frame.shape == (16, 16)

    def test_get_frame_invalid_index(self, tmp_path):
        from DICOM_reencoder.core import build_multiframe_dataset, save_dataset

        ds = build_multiframe_dataset(frames=2, shape=(16, 16))
        input_file = tmp_path / "multiframe.dcm"
        save_dataset(ds, input_file)

        ds_loaded = load_dataset(input_file)

        with pytest.raises(IndexError):
            get_frame(ds_loaded, 10)

    def test_window_frame_basic(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)

        windowed = window_frame(ds, 0)

        assert isinstance(windowed, np.ndarray)
        assert windowed.dtype == np.uint8
        assert windowed.min() >= 0
        assert windowed.max() <= 255

    def test_window_frame_custom_window(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)

        windowed = window_frame(ds, 0, window_center=40, window_width=400)

        assert isinstance(windowed, np.ndarray)
        assert windowed.dtype == np.uint8

    def test_frame_to_png_bytes(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)

        png_bytes = frame_to_png_bytes(ds, 0)

        assert png_bytes is not None
        assert hasattr(png_bytes, "read")
        # PNG signature
        png_bytes.seek(0)
        header = png_bytes.read(8)
        assert header[:8] == b"\x89PNG\r\n\x1a\n"


class TestMetadataExtraction:
    """Test metadata extraction."""

    def test_summarize_metadata_basic(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)

        summary = summarize_metadata(ds)

        assert isinstance(summary, dict)
        assert "patient" in summary
        assert "study" in summary
        assert "series" in summary
        assert "image" in summary

    def test_summarize_metadata_patient_info(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)

        summary = summarize_metadata(ds)

        patient = summary["patient"]
        assert "name" in patient
        assert "id" in patient
        assert "birth_date" in patient
        assert "sex" in patient

    def test_summarize_metadata_study_info(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)

        summary = summarize_metadata(ds)

        study = summary["study"]
        assert "description" in study
        assert "date" in study
        assert "instance_uid" in study

    def test_summarize_metadata_series_info(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)

        summary = summarize_metadata(ds)

        series = summary["series"]
        assert "modality" in series
        assert "instance_uid" in series

    def test_summarize_metadata_image_info(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)

        summary = summarize_metadata(ds)

        image = summary["image"]
        assert "rows" in image
        assert "columns" in image
        assert "bits_allocated" in image

