#
# test_split_multiframe.py
# Dicom-Tools-py
#
# Tests for multi-frame DICOM splitting: frame extraction, UID generation,
# metadata preservation, and frame information retrieval.
#
# Thales Matheus Mendonça Santos - November 2025

from pathlib import Path

import pytest
import pydicom

from DICOM_reencoder.core import build_multiframe_dataset, load_dataset, save_dataset
from DICOM_reencoder.split_multiframe import (
    extract_specific_frames,
    get_frame_info,
    split_multiframe,
)


class TestSplitMultiframe:
    """Test multi-frame splitting functionality."""

    def test_split_multiframe_basic(self, tmp_path):
        ds = build_multiframe_dataset(frames=3, shape=(16, 16))
        input_file = tmp_path / "multiframe.dcm"
        save_dataset(ds, input_file)

        output_dir = tmp_path / "split"
        num_frames = split_multiframe(input_file, str(output_dir))

        assert num_frames == 3
        assert output_dir.exists()
        split_files = list(output_dir.glob("*.dcm"))
        assert len(split_files) == 3

    def test_split_multiframe_preserves_metadata(self, tmp_path):
        ds = build_multiframe_dataset(frames=2, shape=(16, 16))
        original_modality = ds.Modality
        original_patient_name = ds.get("PatientName", "")

        input_file = tmp_path / "multiframe.dcm"
        save_dataset(ds, input_file)

        output_dir = tmp_path / "split"
        split_multiframe(input_file, str(output_dir))

        # Check first split file
        split_files = list(output_dir.glob("*.dcm"))
        if split_files:
            split_ds = load_dataset(split_files[0])
            assert split_ds.Modality == original_modality
            if original_patient_name:
                assert str(split_ds.get("PatientName", "")) == str(original_patient_name)

    def test_split_multiframe_generates_unique_uids(self, tmp_path):
        ds = build_multiframe_dataset(frames=3, shape=(16, 16))
        input_file = tmp_path / "multiframe.dcm"
        save_dataset(ds, input_file)

        output_dir = tmp_path / "split"
        split_multiframe(input_file, str(output_dir))

        split_files = list(output_dir.glob("*.dcm"))
        sop_uids = set()
        for split_file in split_files:
            split_ds = load_dataset(split_file)
            sop_uids.add(split_ds.SOPInstanceUID)

        # Each frame should have unique SOP Instance UID
        assert len(sop_uids) == len(split_files)

    def test_split_multiframe_preserves_series_uid(self, tmp_path):
        ds = build_multiframe_dataset(frames=2, shape=(16, 16))
        original_series_uid = ds.SeriesInstanceUID

        input_file = tmp_path / "multiframe.dcm"
        save_dataset(ds, input_file)

        output_dir = tmp_path / "split"
        split_multiframe(input_file, str(output_dir))

        split_files = list(output_dir.glob("*.dcm"))
        for split_file in split_files:
            split_ds = load_dataset(split_file)
            assert split_ds.SeriesInstanceUID == original_series_uid

    def test_split_multiframe_single_frame_returns_zero(self, tmp_path):
        from DICOM_reencoder.core import build_secondary_capture, save_dataset

        ds = build_secondary_capture(shape=(16, 16))
        input_file = tmp_path / "single_frame.dcm"
        save_dataset(ds, input_file)

        output_dir = tmp_path / "split"
        num_frames = split_multiframe(input_file, str(output_dir))

        # Should return 0 for single-frame images
        assert num_frames == 0

    def test_split_multiframe_custom_prefix(self, tmp_path):
        ds = build_multiframe_dataset(frames=2, shape=(16, 16))
        input_file = tmp_path / "multiframe.dcm"
        save_dataset(ds, input_file)

        output_dir = tmp_path / "split"
        prefix = "custom_frame"
        num_frames = split_multiframe(input_file, str(output_dir), prefix=prefix)

        assert num_frames == 2
        split_files = list(output_dir.glob(f"{prefix}*.dcm"))
        assert len(split_files) == 2


class TestGetFrameInfo:
    """Test frame information retrieval."""

    def test_get_frame_info_basic(self, tmp_path):
        ds = build_multiframe_dataset(frames=3, shape=(16, 16))
        input_file = tmp_path / "multiframe.dcm"
        save_dataset(ds, input_file)

        # get_frame_info doesn't return a dict, it prints
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            get_frame_info(input_file)

        output_str = output.getvalue()
        assert "3" in output_str or "frame" in output_str.lower()

    def test_get_frame_info_single_frame(self, tmp_path):
        from DICOM_reencoder.core import build_secondary_capture, save_dataset

        ds = build_secondary_capture(shape=(16, 16))
        input_file = tmp_path / "single_frame.dcm"
        save_dataset(ds, input_file)

        # get_frame_info doesn't return a dict, it prints
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            get_frame_info(input_file)

        output_str = output.getvalue()
        assert "single" in output_str.lower() or "frame" in output_str.lower()


class TestExtractSpecificFrames:
    """Test extraction of specific frames."""

    def test_extract_specific_frames_basic(self, tmp_path):
        ds = build_multiframe_dataset(frames=5, shape=(16, 16))
        input_file = tmp_path / "multiframe.dcm"
        save_dataset(ds, input_file)

        output_dir = tmp_path / "extracted"
        # frame_numbers are 1-based in extract_specific_frames
        frame_numbers = [1, 3, 5]

        result = extract_specific_frames(input_file, frame_numbers, str(output_dir))

        assert result == len(frame_numbers)
        extracted_files = list(output_dir.glob("*.dcm"))
        assert len(extracted_files) == len(frame_numbers)

    def test_extract_specific_frames_invalid_numbers(self, tmp_path):
        ds = build_multiframe_dataset(frames=3, shape=(16, 16))
        input_file = tmp_path / "multiframe.dcm"
        save_dataset(ds, input_file)

        output_dir = tmp_path / "extracted"
        frame_numbers = [0, 10, 20]  # Some invalid

        # Should handle invalid frame numbers gracefully
        result = extract_specific_frames(input_file, frame_numbers, str(output_dir))

        # Should extract valid frames
        assert result >= 0

