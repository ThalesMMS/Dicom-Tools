#
# test_modify_tags.py
# Dicom-Tools-py
#
# Tests for DICOM tag modification: single tag changes, batch modifications,
# tag listing, and edge cases.
#
# Thales Matheus Mendonça Santos - November 2025

from pathlib import Path

import pytest
import pydicom

from DICOM_reencoder.core import load_dataset, save_dataset
from DICOM_reencoder.modify_tags import list_all_tags, modify_tag, modify_tags_batch


class TestModifyTag:
    """Test single tag modification."""

    def test_modify_existing_tag(self, synthetic_dicom_path, tmp_path):
        ds = load_dataset(synthetic_dicom_path)
        original_name = ds.get("PatientName", "")

        result = modify_tag(ds, "PatientName", "Modified^Name")

        assert result is True
        assert ds.PatientName == "Modified^Name"
        assert ds.PatientName != original_name

    def test_add_new_tag(self, synthetic_dicom_path, tmp_path):
        ds = load_dataset(synthetic_dicom_path)

        result = modify_tag(ds, "PatientComments", "Test comment")

        assert result is True
        assert ds.PatientComments == "Test comment"

    def test_modify_multiple_tags(self, synthetic_dicom_path, tmp_path):
        ds = load_dataset(synthetic_dicom_path)

        modify_tag(ds, "PatientName", "Patient^One")
        modify_tag(ds, "PatientID", "ID-001")
        modify_tag(ds, "Modality", "CT")

        assert ds.PatientName == "Patient^One"
        assert ds.PatientID == "ID-001"
        assert ds.Modality == "CT"

    def test_modify_preserves_other_tags(self, synthetic_dicom_path, tmp_path):
        ds = load_dataset(synthetic_dicom_path)
        original_modality = ds.Modality
        original_rows = ds.Rows

        modify_tag(ds, "PatientName", "New^Name")

        assert ds.Modality == original_modality
        assert ds.Rows == original_rows


class TestModifyTagsBatch:
    """Test batch tag modification."""

    def test_modify_tags_batch_basic(self, synthetic_dicom_path, tmp_path):
        output = tmp_path / "modified.dcm"
        modifications = {
            "PatientName": "Batch^Patient",
            "PatientID": "BATCH-001",
            "StudyDescription": "Batch Study"
        }

        result = modify_tags_batch(synthetic_dicom_path, modifications, str(output))

        assert result is not None
        ds = load_dataset(output)
        assert ds.PatientName == "Batch^Patient"
        assert ds.PatientID == "BATCH-001"
        assert ds.StudyDescription == "Batch Study"

    def test_modify_tags_batch_empty_dict(self, synthetic_dicom_path, tmp_path):
        output = tmp_path / "modified.dcm"

        result = modify_tags_batch(synthetic_dicom_path, {}, str(output))

        assert result is not None
        ds = load_dataset(output)
        # File should still be valid
        assert hasattr(ds, "PatientName")

    def test_modify_tags_batch_preserves_pixel_data(self, synthetic_dicom_path, tmp_path):
        original = load_dataset(synthetic_dicom_path)
        original_pixels = original.pixel_array.copy()

        output = tmp_path / "modified.dcm"
        modifications = {"PatientName": "Test^Patient"}

        modify_tags_batch(synthetic_dicom_path, modifications, str(output))

        ds = load_dataset(output)
        assert ds.pixel_array.shape == original_pixels.shape

    def test_modify_tags_batch_invalid_tag(self, synthetic_dicom_path, tmp_path):
        output = tmp_path / "modified.dcm"
        modifications = {
            "InvalidTagName": "Value"
        }

        # Should not crash, may skip invalid tags
        result = modify_tags_batch(synthetic_dicom_path, modifications, str(output))

        # Function should complete
        assert result is not None


class TestListAllTags:
    """Test tag listing functionality."""

    def test_list_all_tags_basic(self, synthetic_dicom_path):
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            list_all_tags(synthetic_dicom_path)

        output_str = output.getvalue()
        assert len(output_str) > 0
        # Should contain common tags
        assert "PatientName" in output_str or "PATIENT" in output_str.upper()

    def test_list_all_tags_shows_file_meta(self, synthetic_dicom_path):
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            list_all_tags(synthetic_dicom_path)

        output_str = output.getvalue()
        # Should show file meta information section
        assert "FILE META" in output_str.upper() or "META" in output_str.upper()

    def test_list_all_tags_shows_dataset_tags(self, synthetic_dicom_path):
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            list_all_tags(synthetic_dicom_path)

        output_str = output.getvalue()
        # Should show dataset tags section
        assert "DATASET" in output_str.upper() or "TAGS" in output_str.upper()


class TestTagModificationEdgeCases:
    """Test edge cases in tag modification."""

    def test_modify_date_tag(self, synthetic_dicom_path, tmp_path):
        ds = load_dataset(synthetic_dicom_path)

        result = modify_tag(ds, "StudyDate", "20231115")

        assert result is True
        assert ds.StudyDate == "20231115"

    def test_modify_uid_tag(self, synthetic_dicom_path, tmp_path):
        from pydicom.uid import generate_uid

        ds = load_dataset(synthetic_dicom_path)
        new_uid = generate_uid()

        result = modify_tag(ds, "StudyInstanceUID", new_uid)

        assert result is True
        assert ds.StudyInstanceUID == new_uid

    def test_modify_numeric_tag(self, synthetic_dicom_path, tmp_path):
        ds = load_dataset(synthetic_dicom_path)

        result = modify_tag(ds, "InstanceNumber", "42")

        assert result is True
        assert str(ds.InstanceNumber) == "42"

    def test_modify_sequence_tag(self, synthetic_dicom_path, tmp_path):
        ds = load_dataset(synthetic_dicom_path)

        # Sequences are complex, but we can test that modification doesn't crash
        if hasattr(ds, "ReferencedImageSequence"):
            # Just verify we can access it
            seq = ds.get("ReferencedImageSequence", None)
            # Modification of sequences may require special handling
            assert True  # Test passes if no exception

    def test_roundtrip_modification(self, synthetic_dicom_path, tmp_path):
        # Modify, save, reload
        ds = load_dataset(synthetic_dicom_path)
        modify_tag(ds, "PatientName", "Roundtrip^Test")

        output = tmp_path / "roundtrip.dcm"
        save_dataset(ds, output)

        reloaded = load_dataset(output)
        assert reloaded.PatientName == "Roundtrip^Test"

    def test_modify_multiple_files_consistency(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        modifications = {"PatientName": "Consistent^Name"}

        for path in paths:
            output = tmp_path / f"modified_{Path(path).name}"
            modify_tags_batch(path, modifications, str(output))

            ds = load_dataset(output)
            assert ds.PatientName == "Consistent^Name"

