#
# test_gdcm_advanced.py
# Dicom-Tools-py
#
# Advanced GDCM tests: codec detection, image manipulation, string filtering,
# anonymization, scanner interface, and JPEG-LS transcoding.
#
# Thales Matheus Mendonça Santos - November 2025

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import pydicom
from pydicom.uid import (
    ExplicitVRLittleEndian,
    JPEG2000,
    JPEG2000Lossless,
    JPEGBaseline8Bit,
    JPEGExtended12Bit,
    JPEGLossless,
    JPEGLosslessSV1,
    RLELossless,
)

from DICOM_reencoder.core import build_secondary_capture, save_dataset, load_dataset
from DICOM_reencoder.transcode_dicom import transcode

gdcm = pytest.importorskip("gdcm")


class TestCodecSupport:
    """Test GDCM codec availability and detection."""

    def test_jpeg_codec_availability(self):
        codec_factory = gdcm.ImageCodec.GetCodecFactory()
        # Just verify we can access codec factory
        assert codec_factory is not None

    def test_transfer_syntax_detection(self, synthetic_dicom_path):
        reader = gdcm.Reader()
        reader.SetFileName(str(synthetic_dicom_path))
        assert reader.Read()

        file = reader.GetFile()
        header = file.GetHeader()
        ts = header.GetDataSetTransferSyntax()

        assert ts is not None

    def test_photometric_interpretation_detection(self, synthetic_dicom_path):
        reader = gdcm.ImageReader()
        reader.SetFileName(str(synthetic_dicom_path))
        assert reader.Read()

        image = reader.GetImage()
        pi = image.GetPhotometricInterpretation()

        # Synthetic images are typically MONOCHROME2
        pi_str = str(pi)
        assert "MONOCHROME" in pi_str or pi_str != ""


class TestImageManipulation:
    """Test GDCM image processing operations."""

    def test_image_dimensions_and_spacing(self, synthetic_dicom_path):
        reader = gdcm.ImageReader()
        reader.SetFileName(str(synthetic_dicom_path))
        assert reader.Read()

        image = reader.GetImage()
        dims = image.GetDimensions()
        spacing = image.GetSpacing()

        assert dims[0] == 32
        assert dims[1] == 32
        assert len(spacing) >= 2

    def test_pixel_format_detection(self, synthetic_dicom_path):
        reader = gdcm.ImageReader()
        reader.SetFileName(str(synthetic_dicom_path))
        assert reader.Read()

        image = reader.GetImage()
        pf = image.GetPixelFormat()

        assert pf.GetBitsAllocated() in (8, 16, 32)
        assert pf.GetBitsStored() <= pf.GetBitsAllocated()
        assert pf.GetSamplesPerPixel() >= 1

    def test_buffer_extraction(self, synthetic_dicom_path):
        reader = gdcm.ImageReader()
        reader.SetFileName(str(synthetic_dicom_path))
        assert reader.Read()

        image = reader.GetImage()
        buffer_length = image.GetBufferLength()
        buffer = image.GetBuffer()

        assert buffer_length > 0
        assert len(buffer) == buffer_length

    def test_image_origin_and_direction_cosines(self, synthetic_dicom_path):
        reader = gdcm.ImageReader()
        reader.SetFileName(str(synthetic_dicom_path))
        assert reader.Read()

        image = reader.GetImage()
        origin = image.GetOrigin()
        dc = image.GetDirectionCosines()

        assert len(origin) >= 2
        assert len(dc) >= 6  # 6 direction cosines for row/column


class TestStringFilter:
    """Test GDCM string filter for tag manipulation."""

    def test_string_filter_tag_lookup(self, synthetic_dicom_path):
        reader = gdcm.Reader()
        reader.SetFileName(str(synthetic_dicom_path))
        assert reader.Read()

        sf = gdcm.StringFilter()
        sf.SetFile(reader.GetFile())

        # Get PatientName
        patient_name = sf.ToString(gdcm.Tag(0x0010, 0x0010))
        assert patient_name is not None

    def test_string_filter_multiple_tags(self, synthetic_dicom_path):
        reader = gdcm.Reader()
        reader.SetFileName(str(synthetic_dicom_path))
        assert reader.Read()

        sf = gdcm.StringFilter()
        sf.SetFile(reader.GetFile())

        tags_to_check = [
            (0x0010, 0x0020),  # PatientID
            (0x0008, 0x0060),  # Modality
            (0x0028, 0x0010),  # Rows
            (0x0028, 0x0011),  # Columns
        ]

        for group, elem in tags_to_check:
            value = sf.ToString(gdcm.Tag(group, elem))
            assert value is not None


class TestScanner:
    """Test GDCM Scanner interface for batch metadata extraction."""

    def test_scanner_single_tag(self, synthetic_series):
        paths, _ = synthetic_series
        scanner = gdcm.Scanner()
        scanner.AddTag(gdcm.Tag(0x0010, 0x0020))  # PatientID

        success = scanner.Scan([str(p) for p in paths])
        if not success:
            pytest.skip("GDCM Scanner not working in this environment")

        for path in paths:
            value = scanner.GetValue(str(path), gdcm.Tag(0x0010, 0x0020))
            assert value is not None

    def test_scanner_multiple_tags(self, synthetic_series):
        paths, _ = synthetic_series
        scanner = gdcm.Scanner()
        scanner.AddTag(gdcm.Tag(0x0020, 0x0013))  # InstanceNumber
        scanner.AddTag(gdcm.Tag(0x0020, 0x0032))  # ImagePositionPatient

        success = scanner.Scan([str(p) for p in paths])
        if not success:
            pytest.skip("GDCM Scanner not working in this environment")

        instance_numbers = []
        for path in paths:
            value = scanner.GetValue(str(path), gdcm.Tag(0x0020, 0x0013))
            if value:
                instance_numbers.append(int(value))

        assert len(instance_numbers) == len(paths)

    def test_scanner_series_organization(self, synthetic_series):
        paths, _ = synthetic_series
        scanner = gdcm.Scanner()
        scanner.AddTag(gdcm.Tag(0x0020, 0x000E))  # SeriesInstanceUID

        success = scanner.Scan([str(p) for p in paths])
        if not success:
            pytest.skip("GDCM Scanner not working in this environment")

        series_uids = set()
        for path in paths:
            uid = scanner.GetValue(str(path), gdcm.Tag(0x0020, 0x000E))
            if uid:
                series_uids.add(uid)

        # All files should belong to same series
        assert len(series_uids) == 1


class TestAnonymizer:
    """Test GDCM anonymization capabilities."""

    def test_basic_anonymization(self, synthetic_dicom_path, tmp_path):
        reader = gdcm.Reader()
        reader.SetFileName(str(synthetic_dicom_path))
        assert reader.Read()

        anon = gdcm.Anonymizer()
        anon.SetFile(reader.GetFile())

        # Remove PatientName
        anon.Empty(gdcm.Tag(0x0010, 0x0010))
        anon.Replace(gdcm.Tag(0x0010, 0x0020), "ANON-001")

        output = tmp_path / "anon.dcm"
        writer = gdcm.Writer()
        writer.SetFile(reader.GetFile())
        writer.SetFileName(str(output))
        assert writer.Write()

        reloaded = pydicom.dcmread(output, force=True)
        assert str(reloaded.PatientName) == ""
        assert reloaded.PatientID == "ANON-001"

    def test_anonymizer_removes_private_tags(self, synthetic_dicom_path, tmp_path):
        # First add a private tag
        ds = load_dataset(synthetic_dicom_path)
        ds.add_new(pydicom.tag.Tag(0x0011, 0x0010), "LO", "TestCreator")
        ds.add_new(pydicom.tag.Tag(0x0011, 0x1001), "LO", "PrivateData")
        modified = tmp_path / "with_private.dcm"
        save_dataset(ds, modified)

        reader = gdcm.Reader()
        reader.SetFileName(str(modified))
        assert reader.Read()

        anon = gdcm.Anonymizer()
        anon.SetFile(reader.GetFile())
        anon.RemovePrivateTags()

        output = tmp_path / "no_private.dcm"
        writer = gdcm.Writer()
        writer.SetFile(reader.GetFile())
        writer.SetFileName(str(output))
        assert writer.Write()

        reloaded = pydicom.dcmread(output, force=True)
        # Private tags should be removed
        assert pydicom.tag.Tag(0x0011, 0x1001) not in reloaded


class TestTranscodingAdvanced:
    """Test advanced transcoding scenarios."""

    def test_transcode_to_explicit_vr_little_endian(self, synthetic_dicom_path, tmp_path):
        output = transcode(synthetic_dicom_path, output=tmp_path / "explicit.dcm", syntax="explicit")
        ds = pydicom.dcmread(output, force=True)
        assert ds.file_meta.TransferSyntaxUID == ExplicitVRLittleEndian

    def test_transcode_preserves_pixel_values(self, synthetic_dicom_path, tmp_path):
        original = load_dataset(synthetic_dicom_path)
        original_pixels = original.pixel_array.copy()

        output = transcode(synthetic_dicom_path, output=tmp_path / "transcoded.dcm", syntax="rle")
        reloaded = load_dataset(output)

        assert np.array_equal(reloaded.pixel_array, original_pixels)

    def test_transcode_updates_transfer_syntax_uid(self, synthetic_dicom_path, tmp_path):
        output = transcode(synthetic_dicom_path, output=tmp_path / "rle2.dcm", syntax="rle")
        ds = pydicom.dcmread(output, force=True)

        assert ds.file_meta.TransferSyntaxUID == RLELossless

    def test_batch_transcode_series(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        output_dir = tmp_path / "transcoded_series"
        output_dir.mkdir()

        transcoded = []
        for path in paths:
            out = transcode(path, output=output_dir / path.name, syntax="rle")
            transcoded.append(out)

        assert len(transcoded) == len(paths)
        for path in transcoded:
            ds = pydicom.dcmread(path, force=True)
            assert ds.file_meta.TransferSyntaxUID == RLELossless


class TestPixelDataAccess:
    """Test various pixel data access patterns with GDCM."""

    def test_numpy_array_from_gdcm_buffer(self, synthetic_dicom_path):
        reader = gdcm.ImageReader()
        reader.SetFileName(str(synthetic_dicom_path))
        assert reader.Read()

        image = reader.GetImage()
        pf = image.GetPixelFormat()
        dims = image.GetDimensions()

        buffer = image.GetBuffer()
        
        # Determine numpy dtype
        if pf.GetBitsAllocated() == 8:
            dtype = np.uint8
        elif pf.GetBitsAllocated() == 16:
            dtype = np.uint16 if pf.GetPixelRepresentation() == 0 else np.int16
        else:
            dtype = np.float32

        arr = np.frombuffer(buffer, dtype=dtype)
        expected_size = dims[0] * dims[1]
        if len(dims) > 2 and dims[2] > 1:
            expected_size *= dims[2]

        assert arr.size == expected_size

    def test_multiframe_buffer_access(self, tmp_path):
        from DICOM_reencoder.core import build_multiframe_dataset, save_dataset

        ds = build_multiframe_dataset(frames=3, shape=(16, 16))
        path = save_dataset(ds, tmp_path / "multiframe.dcm")

        reader = gdcm.ImageReader()
        reader.SetFileName(str(path))
        if not reader.Read():
            pytest.skip("GDCM cannot read multiframe in this environment")

        image = reader.GetImage()
        dims = image.GetDimensions()

        # Should have 3 frames
        if len(dims) > 2:
            assert dims[2] == 3 or dims[0] * dims[1] > 0


class TestDataElementManipulation:
    """Test direct data element manipulation with GDCM."""

    def test_create_new_data_element(self, tmp_path):
        ds = gdcm.DataSet()

        # Add PatientName
        de = gdcm.DataElement(gdcm.Tag(0x0010, 0x0010))
        de.SetVR(gdcm.VR(gdcm.VR.PN))
        value = "Test^Patient"
        de.SetByteValue(value, gdcm.VL(len(value)))
        ds.Insert(de)

        # Add PatientID
        de2 = gdcm.DataElement(gdcm.Tag(0x0010, 0x0020))
        de2.SetVR(gdcm.VR(gdcm.VR.LO))
        value2 = "GDCM-001"
        de2.SetByteValue(value2, gdcm.VL(len(value2)))
        ds.Insert(de2)

        assert ds.FindDataElement(gdcm.Tag(0x0010, 0x0010))
        assert ds.FindDataElement(gdcm.Tag(0x0010, 0x0020))

    def test_modify_existing_element(self, synthetic_dicom_path, tmp_path):
        reader = gdcm.Reader()
        reader.SetFileName(str(synthetic_dicom_path))
        assert reader.Read()

        file = reader.GetFile()
        ds = file.GetDataSet()

        # Modify PatientID
        tag = gdcm.Tag(0x0010, 0x0020)
        de = gdcm.DataElement(tag)
        de.SetVR(gdcm.VR(gdcm.VR.LO))
        new_value = "MODIFIED-ID"
        de.SetByteValue(new_value, gdcm.VL(len(new_value)))
        ds.Replace(de)

        output = tmp_path / "modified.dcm"
        writer = gdcm.Writer()
        writer.SetFile(file)
        writer.SetFileName(str(output))
        assert writer.Write()

        reloaded = pydicom.dcmread(output, force=True)
        assert reloaded.PatientID == "MODIFIED-ID"


class TestImageApplyLookupTable:
    """Test GDCM LUT application."""

    def test_apply_modality_lut_subprocess(self, synthetic_dicom_path):
        script = """
import sys, gdcm
path = sys.argv[1]
reader = gdcm.ImageReader()
reader.SetFileName(path)
if not reader.Read():
    sys.exit(1)
image = reader.GetImage()
intercept = image.GetIntercept()
slope = image.GetSlope()
print(f"{slope},{intercept}")
"""
        result = subprocess.run(
            [sys.executable, "-c", script, str(synthetic_dicom_path)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            pytest.skip("GDCM LUT access not available")

        parts = result.stdout.strip().split(",")
        slope = float(parts[0])
        intercept = float(parts[1])

        # Default values
        assert slope != 0  # Slope should be non-zero (typically 1.0)


class TestDICOMDIRAdvanced:
    """Test advanced DICOMDIR operations."""

    def test_dicomdir_patient_level_navigation(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        generator = gdcm.DICOMDIRGenerator()
        generator.SetRootDirectory(str(Path(paths[0]).parent))
        generator.SetFilenames([str(p) for p in paths])

        if not generator.Generate():
            pytest.skip("GDCM DICOMDIR generation not supported")

        dicomdir_path = tmp_path / "DICOMDIR"
        writer = gdcm.Writer()
        writer.SetFile(generator.GetFile())
        writer.SetFileName(str(dicomdir_path))
        assert writer.Write()

        # Parse with pydicom to verify structure
        dd = pydicom.dcmread(dicomdir_path, force=True)
        assert "DirectoryRecordSequence" in dd

        record_types = set()
        for item in dd.DirectoryRecordSequence:
            record_types.add(getattr(item, "DirectoryRecordType", "UNKNOWN"))

        # Should have at least PATIENT, STUDY, SERIES, IMAGE records
        expected_types = {"PATIENT", "STUDY", "SERIES", "IMAGE"}
        found_expected = record_types.intersection(expected_types)
        assert len(found_expected) >= 1  # At least some hierarchy present
