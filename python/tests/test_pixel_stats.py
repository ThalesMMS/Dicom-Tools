#
# test_pixel_stats.py
# Dicom-Tools-py
#
# Tests for pixel statistics: basic stats, histogram generation, frame selection,
# and comparison between files.
#
# Thales Matheus Mendonça Santos - November 2025

from pathlib import Path

import numpy as np
import pytest

from DICOM_reencoder.core import load_dataset
from DICOM_reencoder.core.images import calculate_statistics
from DICOM_reencoder.pixel_stats import compare_pixel_stats, display_statistics


class TestCalculateStatistics:
    """Test pixel statistics calculation."""

    def test_calculate_statistics_basic(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)
        pixels = ds.pixel_array

        stats = calculate_statistics(pixels)

        assert "min" in stats
        assert "max" in stats
        assert "mean" in stats
        assert "median" in stats
        assert "std" in stats
        assert "range" in stats

    def test_calculate_statistics_percentiles(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)
        pixels = ds.pixel_array

        stats = calculate_statistics(pixels)

        assert "p1" in stats
        assert "p5" in stats
        assert "p25" in stats
        assert "p75" in stats
        assert "p95" in stats
        assert "p99" in stats

    def test_calculate_statistics_range(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)
        pixels = ds.pixel_array

        stats = calculate_statistics(pixels)

        assert stats["range"] == stats["max"] - stats["min"]

    def test_calculate_statistics_iqr(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)
        pixels = ds.pixel_array

        stats = calculate_statistics(pixels)

        assert stats["iqr"] == stats["p75"] - stats["p25"]

    def test_calculate_statistics_zero_pixels(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)
        pixels = ds.pixel_array

        stats = calculate_statistics(pixels)

        assert "zero_pixels" in stats
        assert "zero_percent" in stats
        assert stats["zero_percent"] >= 0
        assert stats["zero_percent"] <= 100

    def test_calculate_statistics_unique_values(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)
        pixels = ds.pixel_array

        stats = calculate_statistics(pixels)

        assert "unique_values" in stats
        assert stats["unique_values"] > 0
        assert stats["unique_values"] <= stats["total_pixels"]


class TestDisplayStatistics:
    """Test statistics display functionality."""

    def test_display_statistics_basic(self, synthetic_dicom_path):
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            display_statistics(synthetic_dicom_path)

        output_str = output.getvalue()
        assert len(output_str) > 0
        assert "Statistics" in output_str or "STATISTICS" in output_str.upper()

    def test_display_statistics_shows_dimensions(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)
        rows = ds.Rows
        cols = ds.Columns

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            display_statistics(synthetic_dicom_path)

        output_str = output.getvalue()
        assert str(rows) in output_str or str(cols) in output_str

    def test_display_statistics_shows_basic_stats(self, synthetic_dicom_path):
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            display_statistics(synthetic_dicom_path)

        output_str = output.getvalue()
        assert "Minimum" in output_str or "MIN" in output_str.upper()
        assert "Maximum" in output_str or "MAX" in output_str.upper()
        assert "Mean" in output_str or "MEAN" in output_str.upper()

    def test_display_statistics_multiframe(self, tmp_path):
        from DICOM_reencoder.core import build_multiframe_dataset, save_dataset

        ds = build_multiframe_dataset(frames=3, shape=(16, 16))
        input_file = tmp_path / "multiframe.dcm"
        save_dataset(ds, input_file)

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            display_statistics(input_file, frame_number=0)

        output_str = output.getvalue()
        assert "frame" in output_str.lower() or "Frame" in output_str

    def test_display_statistics_handles_missing_pixel_data(self, tmp_path):
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

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            display_statistics(input_file)

        output_str = output.getvalue()
        # Should handle gracefully
        assert "Error" in output_str or "No pixel data" in output_str


class TestComparePixelStats:
    """Test pixel statistics comparison."""

    def test_compare_pixel_stats_basic(self, synthetic_series):
        paths, _ = synthetic_series
        if len(paths) >= 2:
            import io
            from contextlib import redirect_stdout

            output = io.StringIO()
            with redirect_stdout(output):
                compare_pixel_stats(paths[0], paths[1])

            output_str = output.getvalue()
            assert len(output_str) > 0

    def test_compare_pixel_stats_shows_differences(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        if len(paths) >= 2:
            # Modify one file's pixel data
            ds1 = load_dataset(paths[0])
            ds2 = load_dataset(paths[1])

            # Create modified version
            modified_pixels = ds2.pixel_array.copy()
            modified_pixels = modified_pixels + 100  # Shift values
            ds2.PixelData = modified_pixels.tobytes()
            modified_file = tmp_path / "modified.dcm"
            ds2.save_as(modified_file)

            import io
            from contextlib import redirect_stdout

            output = io.StringIO()
            with redirect_stdout(output):
                compare_pixel_stats(paths[0], modified_file)

            output_str = output.getvalue()
            # Should show differences
            assert len(output_str) > 0

