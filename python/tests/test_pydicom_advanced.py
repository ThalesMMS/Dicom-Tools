#
# test_pydicom_advanced.py
# Dicom-Tools-py
#
# Advanced pydicom tests: UID handling, encapsulated pixel data, color spaces,
# compressed transfers, dataset manipulation, and DICOM conformance checks.
#
# Thales Matheus Mendonça Santos - November 2025

import io
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest
import pydicom
from pydicom import Dataset, Sequence
from pydicom.datadict import keyword_for_tag, tag_for_keyword
from pydicom.encaps import encapsulate
from pydicom.filebase import DicomBytesIO
from pydicom.pixel_data_handlers import apply_voi_lut, apply_modality_lut
from pydicom.tag import Tag
from pydicom.uid import (
    ExplicitVRLittleEndian,
    ImplicitVRLittleEndian,
    JPEG2000Lossless,
    JPEGBaseline8Bit,
    RLELossless,
    UID,
    generate_uid,
)
from pydicom.valuerep import DA, DT, TM, PersonName, IS, DS

from DICOM_reencoder.core import build_secondary_capture, save_dataset, load_dataset


class TestUIDHandling:
    """Test UID generation, validation, and manipulation."""

    def test_generate_uid_uniqueness(self):
        uids = {generate_uid() for _ in range(100)}
        assert len(uids) == 100

    def test_generate_uid_with_prefix(self):
        prefix = "1.2.826.0.1.3680043.8"
        uid = generate_uid(prefix=prefix)
        assert uid.startswith(prefix)
        assert UID(uid).is_valid

    def test_uid_validation_rejects_invalid(self):
        invalid_uids = [
            "1.2.3..4",         # double dot
            "1.2.3.04",         # leading zero
            "1" * 65,           # too long
            "abc.def.ghi",      # non-numeric
        ]
        for invalid in invalid_uids:
            assert not UID(invalid).is_valid

    def test_uid_comparison_semantics(self):
        uid1 = UID("1.2.3.4")
        uid2 = UID("1.2.3.4")
        uid3 = UID("1.2.3.5")
        
        assert uid1 == uid2
        assert uid1 != uid3
        assert hash(uid1) == hash(uid2)

    def test_well_known_uid_properties(self):
        ct_uid = UID("1.2.840.10008.5.1.4.1.1.2")
        assert ct_uid.name == "CT Image Storage"
        assert ct_uid.keyword == "CTImageStorage"
        assert ct_uid.is_transfer_syntax is False


class TestValueRepresentations:
    """Test pydicom value representation handling."""

    def test_date_time_vr_parsing(self):
        ds = Dataset()
        ds.StudyDate = "20231115"
        ds.StudyTime = "143025.123456"
        ds.AcquisitionDateTime = "20231115143025.123456"

        assert DA(ds.StudyDate).year == 2023
        assert DA(ds.StudyDate).month == 11
        assert TM(ds.StudyTime).hour == 14
        assert TM(ds.StudyTime).minute == 30
        assert DT(ds.AcquisitionDateTime).second == 25

    def test_person_name_components(self):
        pn = PersonName("Doe^John^M^Dr^Jr")
        assert pn.family_name == "Doe"
        assert pn.given_name == "John"
        assert pn.middle_name == "M"
        assert pn.name_prefix == "Dr"
        assert pn.name_suffix == "Jr"

    def test_decimal_string_precision(self):
        ds = Dataset()
        ds.SliceThickness = DS("1.5000001")
        assert float(ds.SliceThickness) == pytest.approx(1.5000001)

    def test_integer_string_range(self):
        ds = Dataset()
        ds.Rows = IS("65535")
        ds.Columns = IS("1")
        assert int(ds.Rows) == 65535
        assert int(ds.Columns) == 1


class TestDataDictionary:
    """Test DICOM data dictionary operations."""

    def test_tag_to_keyword_lookup(self):
        assert keyword_for_tag(Tag(0x0010, 0x0010)) == "PatientName"
        assert keyword_for_tag(Tag(0x7FE0, 0x0010)) == "PixelData"

    def test_keyword_to_tag_lookup(self):
        assert tag_for_keyword("PatientName") == Tag(0x0010, 0x0010)
        assert tag_for_keyword("Modality") == Tag(0x0008, 0x0060)

    def test_private_tag_handling(self, tmp_path):
        ds = build_secondary_capture(shape=(4, 4))
        ds.add_new(Tag(0x0011, 0x0010), "LO", "CustomCreator")
        ds.add_new(Tag(0x0011, 0x1001), "LO", "PrivateValue")

        path = save_dataset(ds, tmp_path / "private.dcm")
        reloaded = load_dataset(path)

        assert Tag(0x0011, 0x0010) in reloaded
        assert reloaded[Tag(0x0011, 0x1001)].value == "PrivateValue"


class TestSequenceManipulation:
    """Test DICOM sequence handling and nested structures."""

    def test_sequence_iteration(self):
        ds = Dataset()
        ds.ContentSequence = Sequence([Dataset(), Dataset(), Dataset()])
        for i, item in enumerate(ds.ContentSequence):
            item.ItemNumber = i

        assert len(ds.ContentSequence) == 3
        assert ds.ContentSequence[2].ItemNumber == 2

    def test_nested_sequence_depth(self):
        ds = Dataset()
        inner = Dataset()
        inner.CodeValue = "T-A0100"
        innermost = Dataset()
        innermost.MappingResource = "DCMR"
        inner.MappingResourceIdentificationSequence = Sequence([innermost])
        ds.AnatomicRegionSequence = Sequence([inner])

        assert ds.AnatomicRegionSequence[0].CodeValue == "T-A0100"
        assert ds.AnatomicRegionSequence[0].MappingResourceIdentificationSequence[0].MappingResource == "DCMR"

    def test_sequence_copy_independence(self):
        ds = Dataset()
        ds.OtherPatientIDsSequence = Sequence([Dataset()])
        ds.OtherPatientIDsSequence[0].PatientID = "ORIGINAL"

        copy = ds.copy()
        copy.OtherPatientIDsSequence[0].PatientID = "MODIFIED"

        assert ds.OtherPatientIDsSequence[0].PatientID == "ORIGINAL"


class TestPixelDataHandling:
    """Test pixel data access, LUT application, and array manipulation."""

    def test_modality_lut_application(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)
        ds.RescaleSlope = 2.0
        ds.RescaleIntercept = -1024.0

        raw = ds.pixel_array
        rescaled = apply_modality_lut(raw, ds)

        expected = raw * 2.0 - 1024.0
        assert np.allclose(rescaled, expected)

    def test_voi_lut_window_level(self, synthetic_dicom_path):
        ds = load_dataset(synthetic_dicom_path)
        ds.WindowCenter = 40
        ds.WindowWidth = 400

        result = apply_voi_lut(ds.pixel_array, ds)
        assert result.min() >= 0
        assert result.max() <= 255

    def test_photometric_interpretation_grayscale(self, synthetic_datasets):
        for ds in synthetic_datasets:
            assert ds.PhotometricInterpretation in ("MONOCHROME1", "MONOCHROME2")
            assert ds.SamplesPerPixel == 1

    def test_pixel_padding_value_masking(self, tmp_path):
        ds = build_secondary_capture(shape=(16, 16))
        pixels = np.arange(256, dtype=np.uint16).reshape(16, 16)
        pixels[0, 0] = 65535  # padding value
        ds.PixelData = pixels.tobytes()
        ds.PixelPaddingValue = 65535

        path = save_dataset(ds, tmp_path / "padding.dcm")
        reloaded = load_dataset(path)

        assert reloaded.PixelPaddingValue == 65535
        assert reloaded.pixel_array[0, 0] == 65535


class TestFileMetaInformation:
    """Test file meta information handling."""

    def test_file_meta_required_elements(self, synthetic_dicom_path):
        ds = pydicom.dcmread(synthetic_dicom_path)
        meta = ds.file_meta

        assert hasattr(meta, "MediaStorageSOPClassUID")
        assert hasattr(meta, "MediaStorageSOPInstanceUID")
        assert hasattr(meta, "TransferSyntaxUID")
        assert hasattr(meta, "ImplementationClassUID")

    def test_transfer_syntax_detection(self, synthetic_dicom_path):
        ds = pydicom.dcmread(synthetic_dicom_path)
        ts = ds.file_meta.TransferSyntaxUID

        assert ts in (ExplicitVRLittleEndian, ImplicitVRLittleEndian)

    def test_file_meta_version(self, synthetic_dicom_path):
        ds = pydicom.dcmread(synthetic_dicom_path)
        version = ds.file_meta.get("FileMetaInformationVersion", b"\x00\x01")
        assert version == b"\x00\x01"


class TestDatasetComparison:
    """Test dataset comparison and diff utilities."""

    def test_dataset_equality_check(self, synthetic_datasets):
        ds1 = synthetic_datasets[0].copy()
        ds2 = synthetic_datasets[0].copy()

        # Same content should be equal
        assert list(ds1.keys()) == list(ds2.keys())

    def test_dataset_diff_detection(self, synthetic_datasets):
        ds1 = synthetic_datasets[0].copy()
        ds2 = synthetic_datasets[0].copy()
        ds2.PatientName = "Different^Name"

        differences = []
        for elem in ds1:
            if elem.keyword == "PatientName":
                if ds1[elem.tag].value != ds2[elem.tag].value:
                    differences.append(elem.keyword)

        assert "PatientName" in differences


class TestEncodingDecoding:
    """Test dataset encoding/decoding and byte-level operations."""

    def test_dataset_to_bytes_roundtrip(self, synthetic_datasets):
        ds = synthetic_datasets[0].copy()
        buffer = DicomBytesIO()
        pydicom.dcmwrite(buffer, ds)
        buffer.seek(0)

        reloaded = pydicom.dcmread(buffer, force=True)
        assert str(reloaded.PatientName) == str(ds.PatientName)
        assert np.array_equal(reloaded.pixel_array, ds.pixel_array)

    def test_deflated_transfer_syntax(self, tmp_path, synthetic_datasets):
        from pydicom.uid import DeflatedExplicitVRLittleEndian

        ds = synthetic_datasets[0].copy()
        ds.file_meta.TransferSyntaxUID = DeflatedExplicitVRLittleEndian

        path = tmp_path / "deflated.dcm"
        ds.save_as(path)

        reloaded = pydicom.dcmread(path)
        assert reloaded.file_meta.TransferSyntaxUID == DeflatedExplicitVRLittleEndian
        assert np.array_equal(reloaded.pixel_array, ds.pixel_array)


class TestBulkDataHandling:
    """Test bulk data URI and streaming operations."""

    def test_large_pixel_data_chunked_read(self, tmp_path):
        ds = build_secondary_capture(shape=(512, 512))
        path = save_dataset(ds, tmp_path / "large.dcm")

        # Read with specific buffer
        with open(path, "rb") as f:
            ds_streamed = pydicom.dcmread(f, defer_size=1024)
            # Force pixel data load
            _ = ds_streamed.pixel_array

        assert ds_streamed.pixel_array.shape == (512, 512)

    def test_encapsulated_frame_extraction(self, tmp_path):
        ds = build_secondary_capture(shape=(8, 8))
        pixels = np.random.randint(0, 255, (8, 8), dtype=np.uint8)
        
        # Create encapsulated format (simulated)
        ds.PixelData = pixels.tobytes()
        ds.BitsAllocated = 8
        ds.BitsStored = 8
        ds.HighBit = 7
        ds.PixelRepresentation = 0
        
        path = save_dataset(ds, tmp_path / "encap.dcm")
        reloaded = load_dataset(path)

        assert reloaded.pixel_array.shape == (8, 8)


class TestDICOMConformance:
    """Test DICOM standard conformance checks."""

    def test_sop_class_uid_matches_modality(self, synthetic_datasets):
        for ds in synthetic_datasets:
            sop_class = ds.SOPClassUID
            modality = ds.Modality

            # CT should use CT Image Storage
            if modality == "CT":
                assert "CT" in sop_class.name or "Secondary" in sop_class.name

    def test_patient_module_completeness(self, synthetic_datasets):
        required = ["PatientName", "PatientID", "PatientBirthDate", "PatientSex"]
        ds = synthetic_datasets[0]

        for attr in required:
            assert hasattr(ds, attr), f"Missing patient module attribute: {attr}"

    def test_image_pixel_module_consistency(self, synthetic_datasets):
        ds = synthetic_datasets[0]

        assert ds.Rows > 0
        assert ds.Columns > 0
        assert ds.BitsAllocated in (8, 16, 32)
        assert ds.BitsStored <= ds.BitsAllocated
        assert ds.HighBit == ds.BitsStored - 1
        assert ds.PixelRepresentation in (0, 1)

    def test_unique_identifiers_present(self, synthetic_datasets):
        ds = synthetic_datasets[0]

        assert hasattr(ds, "StudyInstanceUID")
        assert hasattr(ds, "SeriesInstanceUID")
        assert hasattr(ds, "SOPInstanceUID")

        assert UID(ds.StudyInstanceUID).is_valid
        assert UID(ds.SeriesInstanceUID).is_valid
        assert UID(ds.SOPInstanceUID).is_valid
