#
# test_extract_metadata.py
# Dicom-Tools-py
#
# Tests for metadata extraction: patient, study, series, image, equipment,
# and pixel data information extraction.
#
# Thales Matheus Mendonça Santos - November 2025

from pathlib import Path

import pytest

from DICOM_reencoder.core import load_dataset
from DICOM_reencoder.extract_metadata import extract_metadata, format_value


class TestFormatValue:
    """Test value formatting utilities."""

    def test_format_value_string(self):
        result = format_value("Simple String")
        assert result == "Simple String"

    def test_format_value_multivalue(self):
        import pydicom
        mv = pydicom.multival.MultiValue(int, [1, 2, 3])
        result = format_value(mv)
        assert "1" in result
        assert "2" in result
        assert "3" in result

    def test_format_value_bytes(self):
        result = format_value(b"Binary Data")
        assert isinstance(result, str)

    def test_format_value_none(self):
        result = format_value(None)
        assert result == "None" or result == ""


class TestExtractMetadata:
    """Test metadata extraction from DICOM files."""

    def test_extract_metadata_basic(self, synthetic_dicom_path):
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            result = extract_metadata(synthetic_dicom_path)

        assert result is not None
        output_str = output.getvalue()
        assert len(output_str) > 0

    def test_extract_metadata_patient_info(self, synthetic_dicom_path):
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            extract_metadata(synthetic_dicom_path)

        output_str = output.getvalue()
        assert "PATIENT" in output_str.upper()
        assert "PatientName" in output_str or "PATIENT NAME" in output_str.upper()

    def test_extract_metadata_study_info(self, synthetic_dicom_path):
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            extract_metadata(synthetic_dicom_path)

        output_str = output.getvalue()
        assert "STUDY" in output_str.upper()

    def test_extract_metadata_series_info(self, synthetic_dicom_path):
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            extract_metadata(synthetic_dicom_path)

        output_str = output.getvalue()
        assert "SERIES" in output_str.upper()

    def test_extract_metadata_image_info(self, synthetic_dicom_path):
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            extract_metadata(synthetic_dicom_path)

        output_str = output.getvalue()
        assert "IMAGE" in output_str.upper()

    def test_extract_metadata_equipment_info(self, synthetic_dicom_path):
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            extract_metadata(synthetic_dicom_path)

        output_str = output.getvalue()
        assert "EQUIPMENT" in output_str.upper()

    def test_extract_metadata_pixel_data_info(self, synthetic_dicom_path):
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            extract_metadata(synthetic_dicom_path)

        output_str = output.getvalue()
        assert "PIXEL" in output_str.upper() or "Rows" in output_str

    def test_extract_metadata_transfer_syntax(self, synthetic_dicom_path):
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            extract_metadata(synthetic_dicom_path)

        output_str = output.getvalue()
        assert "TRANSFER" in output_str.upper() or "SYNTAX" in output_str.upper()

    def test_extract_metadata_returns_dataset(self, synthetic_dicom_path):
        result = extract_metadata(synthetic_dicom_path)

        assert result is not None
        assert hasattr(result, "PatientName") or hasattr(result, "Modality")


class TestExtractMetadataFields:
    """Test extraction of specific metadata fields."""

    def test_extracts_patient_name(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)
        expected_name = str(ds.get("PatientName", "N/A"))

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            extract_metadata(synthetic_dicom_path)

        output_str = output.getvalue()
        # Patient name should appear in output
        assert "PatientName" in output_str or expected_name in output_str

    def test_extracts_modality(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)
        expected_modality = str(ds.get("Modality", "N/A"))

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            extract_metadata(synthetic_dicom_path)

        output_str = output.getvalue()
        assert "Modality" in output_str or expected_modality in output_str

    def test_extracts_image_dimensions(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)
        rows = ds.get("Rows", 0)
        cols = ds.get("Columns", 0)

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            extract_metadata(synthetic_dicom_path)

        output_str = output.getvalue()
        if rows and cols:
            assert str(rows) in output_str or str(cols) in output_str

    def test_extracts_study_instance_uid(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)
        study_uid = str(ds.get("StudyInstanceUID", "N/A"))

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            extract_metadata(synthetic_dicom_path)

        output_str = output.getvalue()
        assert "StudyInstanceUID" in output_str or study_uid[:20] in output_str


class TestExtractMetadataEdgeCases:
    """Test edge cases in metadata extraction."""

    def test_handles_missing_optional_fields(self, tmp_path):
        from DICOM_reencoder.core import build_secondary_capture

        ds = build_secondary_capture(shape=(8, 8))
        # Remove some optional fields
        for tag in ["PatientWeight", "PatientSize", "InstitutionName"]:
            if hasattr(ds, tag):
                delattr(ds, tag)

        input_file = tmp_path / "minimal.dcm"
        from DICOM_reencoder.core import save_dataset
        save_dataset(ds, input_file)

        result = extract_metadata(input_file)
        assert result is not None

    def test_handles_missing_pixel_data(self, tmp_path):
        import pydicom
        from pydicom.dataset import Dataset, FileDataset
        from pydicom.uid import generate_uid, ExplicitVRLittleEndian

        ds = FileDataset(str(tmp_path / "no_pixels.dcm"), {}, file_meta=pydicom.dataset.FileMetaDataset())
        ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.1"  # CR Image Storage
        ds.SOPInstanceUID = generate_uid()
        ds.StudyInstanceUID = generate_uid()
        ds.SeriesInstanceUID = generate_uid()
        ds.PatientName = "Test^Patient"
        ds.Modality = "CR"

        input_file = tmp_path / "no_pixels.dcm"
        ds.save_as(input_file)

        result = extract_metadata(input_file)
        assert result is not None

    def test_handles_multiframe(self, tmp_path):
        from DICOM_reencoder.core import build_multiframe_dataset, save_dataset

        ds = build_multiframe_dataset(frames=3, shape=(8, 8))
        input_file = tmp_path / "multiframe.dcm"
        save_dataset(ds, input_file)

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            extract_metadata(input_file)

        output_str = output.getvalue()
        assert "NumberOfFrames" in output_str or "3" in output_str

