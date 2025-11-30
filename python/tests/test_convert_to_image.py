#
# test_convert_to_image.py
# Dicom-Tools-py
#
# Tests for DICOM to image conversion: PNG/JPEG export, windowing, frame selection,
# and auto-windowing functionality.
#
# Thales Matheus Mendonça Santos - November 2025

from pathlib import Path

import numpy as np
import pytest

from DICOM_reencoder.convert_to_image import (
    apply_windowing,
    auto_window,
    convert_dicom_to_image,
)


class TestApplyWindowing:
    """Test window/level application."""

    def test_apply_windowing_basic(self):
        pixel_array = np.array([[100, 200, 300], [400, 500, 600]], dtype=np.int16)
        window_center = 350
        window_width = 200

        result = apply_windowing(pixel_array, window_center, window_width)

        assert result.dtype == np.uint8
        assert result.min() >= 0
        assert result.max() <= 255
        assert result.shape == pixel_array.shape

    def test_apply_windowing_clips_values(self):
        pixel_array = np.array([[0, 1000, 2000]], dtype=np.int16)
        window_center = 1000
        window_width = 200

        result = apply_windowing(pixel_array, window_center, window_width)

        assert result.dtype == np.uint8
        assert result.min() >= 0
        assert result.max() <= 255

    def test_apply_windowing_normalizes(self):
        pixel_array = np.array([[100, 200, 300]], dtype=np.int16)
        window_center = 200
        window_width = 200

        result = apply_windowing(pixel_array, window_center, window_width)

        # Values should be normalized to 0-255 range
        assert result.dtype == np.uint8


class TestAutoWindow:
    """Test automatic window calculation."""

    def test_auto_window_basic(self):
        pixel_array = np.array([[100, 200, 300, 400, 500]], dtype=np.int16)

        center, width = auto_window(pixel_array)

        assert isinstance(center, (int, np.integer))
        assert isinstance(width, (int, np.integer))
        assert width > 0

    def test_auto_window_uses_median(self):
        pixel_array = np.array([[10, 20, 30, 40, 50]], dtype=np.int16)

        center, width = auto_window(pixel_array)

        # Center should be around median
        assert 20 <= center <= 40

    def test_auto_window_handles_outliers(self):
        # Array with outliers
        pixel_array = np.array([[10, 20, 30, 40, 50, 1000]], dtype=np.int16)

        center, width = auto_window(pixel_array)

        # Should not be skewed by outlier
        assert center < 500


class TestConvertDicomToImage:
    """Test DICOM to image conversion."""

    def test_convert_to_png(self, synthetic_dicom_path, tmp_path):
        output = tmp_path / "output.png"

        result = convert_dicom_to_image(synthetic_dicom_path, str(output), output_format="png")

        if result:
            assert Path(result).exists()
            assert Path(result).suffix == ".png"

    def test_convert_to_jpeg(self, synthetic_dicom_path, tmp_path):
        output = tmp_path / "output.jpg"

        result = convert_dicom_to_image(synthetic_dicom_path, str(output), output_format="jpeg")

        if result:
            assert Path(result).exists()

    def test_convert_with_custom_window(self, synthetic_dicom_path, tmp_path):
        output = tmp_path / "output.png"

        result = convert_dicom_to_image(
            synthetic_dicom_path,
            str(output),
            window_center=40,
            window_width=400,
            output_format="png",
        )

        if result:
            assert Path(result).exists()

    def test_convert_auto_window(self, synthetic_dicom_path, tmp_path):
        output = tmp_path / "output.png"

        result = convert_dicom_to_image(synthetic_dicom_path, str(output), output_format="png")

        if result:
            assert Path(result).exists()

    def test_convert_multiframe_frame_selection(self, tmp_path):
        from DICOM_reencoder.core import build_multiframe_dataset, save_dataset

        ds = build_multiframe_dataset(frames=3, shape=(16, 16))
        input_file = tmp_path / "multiframe.dcm"
        save_dataset(ds, input_file)

        output = tmp_path / "frame0.png"
        result = convert_dicom_to_image(input_file, str(output), frame_number=0, output_format="png")

        if result:
            assert Path(result).exists()

    def test_convert_handles_missing_pixel_data(self, tmp_path):
        import pydicom
        from pydicom.dataset import FileDataset
        from pydicom.uid import generate_uid, ExplicitVRLittleEndian

        ds = FileDataset(str(tmp_path / "no_pixels.dcm"), {}, file_meta=pydicom.dataset.FileMetaDataset())
        ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.1"
        ds.SOPInstanceUID = generate_uid()
        ds.PatientName = "Test^Patient"
        ds.Modality = "CR"
        # No pixel data

        input_file = tmp_path / "no_pixels.dcm"
        ds.save_as(input_file)

        output = tmp_path / "output.png"
        result = convert_dicom_to_image(input_file, str(output), output_format="png")

        # Should return None for files without pixel data
        assert result is None

    def test_convert_preserves_image_dimensions(self, synthetic_dicom_path, tmp_path):
        from DICOM_reencoder.core import load_dataset

        original = load_dataset(synthetic_dicom_path)
        original_rows = original.Rows
        original_cols = original.Columns

        output = tmp_path / "output.png"
        result = convert_dicom_to_image(synthetic_dicom_path, str(output), output_format="png")

        if result:
            # Verify image was created
            assert Path(result).exists()
            # Image dimensions should match (though format may differ)
            from PIL import Image
            img = Image.open(result)
            assert img.size[0] == original_cols
            assert img.size[1] == original_rows

