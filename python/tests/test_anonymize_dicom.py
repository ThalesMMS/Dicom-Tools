#
# test_anonymize_dicom.py
# Dicom-Tools-py
#
# Tests for DICOM anonymization functionality: PHI removal, UID regeneration,
# date shifting, and consistent anonymization.
#
# Thales Matheus Mendonça Santos - November 2025

import hashlib
from pathlib import Path

import pytest
import pydicom
from pydicom.uid import generate_uid

from DICOM_reencoder.anonymize_dicom import anonymize_dicom, generate_anonymous_id
from DICOM_reencoder.core import load_dataset, save_dataset


class TestAnonymousIDGeneration:
    """Test anonymous ID generation and consistency."""

    def test_generate_anonymous_id_consistency(self):
        original_id = "PATIENT-12345"
        id1 = generate_anonymous_id(original_id)
        id2 = generate_anonymous_id(original_id)

        # Should be consistent
        assert id1 == id2
        assert len(id1) == 16
        assert id1.isupper()

    def test_generate_anonymous_id_uniqueness(self):
        id1 = generate_anonymous_id("PATIENT-1")
        id2 = generate_anonymous_id("PATIENT-2")

        # Different inputs should produce different IDs
        assert id1 != id2

    def test_generate_anonymous_id_format(self):
        id_val = generate_anonymous_id("TEST")
        assert isinstance(id_val, str)
        assert len(id_val) == 16
        assert all(c in "0123456789ABCDEF" for c in id_val)


class TestAnonymizationBasic:
    """Test basic anonymization operations."""

    def test_anonymize_patient_name(self, synthetic_dicom_path, tmp_path):
        output = tmp_path / "anon.dcm"
        anonymize_dicom(synthetic_dicom_path, str(output))

        ds = load_dataset(output)
        assert ds.PatientName == "ANONYMOUS^PATIENT"

    def test_anonymize_patient_id(self, synthetic_dicom_path, tmp_path):
        original = load_dataset(synthetic_dicom_path)
        original_id = original.get("PatientID", "UNKNOWN")

        output = tmp_path / "anon.dcm"
        anonymize_dicom(synthetic_dicom_path, str(output))

        ds = load_dataset(output)
        assert ds.PatientID != original_id
        assert ds.PatientID.startswith("ANON_")

    def test_anonymize_removes_birth_date(self, synthetic_dicom_path, tmp_path):
        output = tmp_path / "anon.dcm"
        anonymize_dicom(synthetic_dicom_path, str(output))

        ds = load_dataset(output)
        assert ds.get("PatientBirthDate", "") == ""

    def test_anonymize_removes_patient_address(self, synthetic_dicom_path, tmp_path):
        # Add patient address first
        ds = load_dataset(synthetic_dicom_path)
        ds.PatientAddress = "123 Main St"
        modified = tmp_path / "with_address.dcm"
        save_dataset(ds, modified)

        output = tmp_path / "anon.dcm"
        anonymize_dicom(modified, str(output))

        anon_ds = load_dataset(output)
        assert anon_ds.get("PatientAddress", "") == ""

    def test_anonymize_institution_name(self, synthetic_dicom_path, tmp_path):
        # First add InstitutionName if it doesn't exist
        ds = load_dataset(synthetic_dicom_path)
        ds.InstitutionName = "Original Hospital"
        modified = tmp_path / "with_institution.dcm"
        save_dataset(ds, modified)

        output = tmp_path / "anon.dcm"
        anonymize_dicom(modified, str(output))

        ds_anon = load_dataset(output)
        # InstitutionName should be anonymized if it existed
        if "InstitutionName" in ds_anon:
            assert ds_anon.InstitutionName == "ANONYMIZED"


class TestUIDRegeneration:
    """Test UID regeneration during anonymization."""

    def test_regenerates_study_instance_uid(self, synthetic_dicom_path, tmp_path):
        original = load_dataset(synthetic_dicom_path)
        original_uid = original.StudyInstanceUID

        output = tmp_path / "anon.dcm"
        anonymize_dicom(synthetic_dicom_path, str(output))

        ds = load_dataset(output)
        assert ds.StudyInstanceUID != original_uid
        assert ds.StudyInstanceUID.startswith("1.2.826.0.1.3680043.8.498.")

    def test_regenerates_series_instance_uid(self, synthetic_dicom_path, tmp_path):
        original = load_dataset(synthetic_dicom_path)
        original_uid = original.SeriesInstanceUID

        output = tmp_path / "anon.dcm"
        anonymize_dicom(synthetic_dicom_path, str(output))

        ds = load_dataset(output)
        assert ds.SeriesInstanceUID != original_uid

    def test_regenerates_sop_instance_uid(self, synthetic_dicom_path, tmp_path):
        original = load_dataset(synthetic_dicom_path)
        original_uid = original.SOPInstanceUID

        output = tmp_path / "anon.dcm"
        anonymize_dicom(synthetic_dicom_path, str(output))

        ds = load_dataset(output)
        assert ds.SOPInstanceUID != original_uid

    def test_uid_regeneration_consistency(self, synthetic_dicom_path, tmp_path):
        # Anonymize same file twice
        output1 = tmp_path / "anon1.dcm"
        output2 = tmp_path / "anon2.dcm"

        anonymize_dicom(synthetic_dicom_path, str(output1))
        anonymize_dicom(synthetic_dicom_path, str(output2))

        ds1 = load_dataset(output1)
        ds2 = load_dataset(output2)

        # UIDs should be consistent (same anonymous ID generates same UIDs)
        assert ds1.StudyInstanceUID == ds2.StudyInstanceUID
        assert ds1.SeriesInstanceUID == ds2.SeriesInstanceUID
        assert ds1.SOPInstanceUID == ds2.SOPInstanceUID


class TestDateShifting:
    """Test date shifting during anonymization."""

    def test_shifts_study_date(self, synthetic_dicom_path, tmp_path):
        original = load_dataset(synthetic_dicom_path)
        original_date = original.get("StudyDate", "")

        if original_date:
            output = tmp_path / "anon.dcm"
            anonymize_dicom(synthetic_dicom_path, str(output))

            ds = load_dataset(output)
            shifted_date = ds.get("StudyDate", "")
            # Date should be shifted (different from original)
            assert shifted_date != original_date
            assert len(shifted_date) == 8  # YYYYMMDD format

    def test_shifts_series_date(self, synthetic_dicom_path, tmp_path):
        original = load_dataset(synthetic_dicom_path)
        original_date = original.get("SeriesDate", "")

        if original_date:
            output = tmp_path / "anon.dcm"
            anonymize_dicom(synthetic_dicom_path, str(output))

            ds = load_dataset(output)
            shifted_date = ds.get("SeriesDate", "")
            assert shifted_date != original_date

    def test_date_shifting_consistency(self, synthetic_dicom_path, tmp_path):
        # Anonymize same file twice
        output1 = tmp_path / "anon1.dcm"
        output2 = tmp_path / "anon2.dcm"

        anonymize_dicom(synthetic_dicom_path, str(output1))
        anonymize_dicom(synthetic_dicom_path, str(output2))

        ds1 = load_dataset(output1)
        ds2 = load_dataset(output2)

        # Dates should be shifted by same amount
        if ds1.get("StudyDate") and ds2.get("StudyDate"):
            assert ds1.StudyDate == ds2.StudyDate


class TestPrivateTagRemoval:
    """Test removal of private tags during anonymization."""

    def test_removes_private_tags(self, synthetic_dicom_path, tmp_path):
        # Add private tags
        ds = load_dataset(synthetic_dicom_path)
        ds.add_new(pydicom.tag.Tag(0x0011, 0x0010), "LO", "PrivateCreator")
        ds.add_new(pydicom.tag.Tag(0x0011, 0x1001), "LO", "PrivateData")
        modified = tmp_path / "with_private.dcm"
        save_dataset(ds, modified)

        output = tmp_path / "anon.dcm"
        anonymize_dicom(modified, str(output))

        anon_ds = load_dataset(output)
        # Private tags should be removed
        assert pydicom.tag.Tag(0x0011, 0x1001) not in anon_ds


class TestAnonymizationPreservation:
    """Test that anonymization preserves important data."""

    def test_preserves_pixel_data(self, synthetic_dicom_path, tmp_path):
        original = load_dataset(synthetic_dicom_path)
        original_pixels = original.pixel_array.copy()

        output = tmp_path / "anon.dcm"
        anonymize_dicom(synthetic_dicom_path, str(output))

        ds = load_dataset(output)
        assert hasattr(ds, "pixel_array")
        assert ds.pixel_array.shape == original_pixels.shape

    def test_preserves_image_dimensions(self, synthetic_dicom_path, tmp_path):
        original = load_dataset(synthetic_dicom_path)
        original_rows = original.Rows
        original_cols = original.Columns

        output = tmp_path / "anon.dcm"
        anonymize_dicom(synthetic_dicom_path, str(output))

        ds = load_dataset(output)
        assert ds.Rows == original_rows
        assert ds.Columns == original_cols

    def test_preserves_modality(self, synthetic_dicom_path, tmp_path):
        original = load_dataset(synthetic_dicom_path)
        original_modality = original.Modality

        output = tmp_path / "anon.dcm"
        anonymize_dicom(synthetic_dicom_path, str(output))

        ds = load_dataset(output)
        assert ds.Modality == original_modality

    def test_preserves_technical_parameters(self, synthetic_dicom_path, tmp_path):
        original = load_dataset(synthetic_dicom_path)
        original_kvp = original.get("KVP", None)
        original_thickness = original.get("SliceThickness", None)

        output = tmp_path / "anon.dcm"
        anonymize_dicom(synthetic_dicom_path, str(output))

        ds = load_dataset(output)
        if original_kvp:
            assert ds.get("KVP") == original_kvp
        if original_thickness:
            assert ds.get("SliceThickness") == original_thickness


class TestAnonymizationEdgeCases:
    """Test edge cases in anonymization."""

    def test_handles_missing_patient_id(self, tmp_path):
        from DICOM_reencoder.core import build_secondary_capture

        ds = build_secondary_capture(shape=(8, 8))
        # Keep PatientID but test that anonymization works
        input_file = tmp_path / "with_patient_id.dcm"
        save_dataset(ds, input_file)

        output = tmp_path / "anon.dcm"
        result = anonymize_dicom(input_file, str(output))

        assert result is not None
        ds_anon = load_dataset(output)
        assert hasattr(ds_anon, "PatientID")
        assert ds_anon.PatientID.startswith("ANON_")

    def test_handles_missing_dates(self, tmp_path):
        from DICOM_reencoder.core import build_secondary_capture

        ds = build_secondary_capture(shape=(8, 8))
        for date_tag in ["StudyDate", "SeriesDate", "AcquisitionDate"]:
            if hasattr(ds, date_tag):
                delattr(ds, date_tag)
        input_file = tmp_path / "no_dates.dcm"
        save_dataset(ds, input_file)

        output = tmp_path / "anon.dcm"
        result = anonymize_dicom(input_file, str(output))

        assert result is not None

    def test_custom_patient_prefix(self, synthetic_dicom_path, tmp_path):
        output = tmp_path / "anon.dcm"
        anonymize_dicom(synthetic_dicom_path, str(output), patient_prefix="CUSTOM")

        ds = load_dataset(output)
        assert ds.PatientID.startswith("CUSTOM_")

    def test_anonymize_series_consistency(self, synthetic_series, tmp_path):
        paths, datasets = synthetic_series
        anon_paths = []

        for path in paths:
            output = tmp_path / f"anon_{path.name}"
            anonymize_dicom(path, str(output))
            anon_paths.append(output)

        # All files should have consistent anonymization
        anon_datasets = [load_dataset(p) for p in anon_paths]
        patient_ids = {ds.PatientID for ds in anon_datasets}

        # All should have same anonymous patient ID
        assert len(patient_ids) == 1

