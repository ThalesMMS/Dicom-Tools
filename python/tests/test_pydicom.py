#
# test_pydicom.py
# Dicom-Tools-py
#
# Ensures pydicom round-trips preserve metadata and pixel data for synthetic files.
#
# Thales Matheus Mendonça Santos - November 2025

import json

import numpy as np
import pydicom
from pydicom.dataelem import RawDataElement
from pydicom.tag import Tag
from pydicom.uid import BasicTextSRStorage, SecondaryCaptureImageStorage

from DICOM_reencoder.core import (
    build_basic_text_sr,
    build_multiframe_dataset,
    build_nested_sequence_dataset,
    build_segmentation,
    build_secondary_capture,
    build_special_vr_dataset,
    calculate_statistics,
    dataset_from_dicom_json,
    dataset_to_dicom_json,
    load_dataset,
    save_dataset,
    summarize_metadata,
)


def test_pydicom_roundtrip(synthetic_dicom_path, tmp_path):
    # Ensure basic edit/save/load cycles preserve both metadata and pixel data
    dataset = load_dataset(synthetic_dicom_path)
    dataset.PatientName = "Unit^Test"

    output = save_dataset(dataset, tmp_path / "roundtrip.dcm")
    reloaded = load_dataset(output)

    assert str(reloaded.PatientName) == "Unit^Test"

    summary = summarize_metadata(reloaded)
    assert summary["patient"]["id"] == "TEST-123"

    stats = calculate_statistics(reloaded.pixel_array)
    assert stats["total_pixels"] == reloaded.Rows * reloaded.Columns
    assert stats["min"] >= 0


def test_sequences_roundtrip_preserves_nested_items(tmp_path):
    ds = build_nested_sequence_dataset()
    path = save_dataset(ds, tmp_path / "sequence.dcm")
    reloaded = load_dataset(path)

    assert "RequestedProcedureCodeSequence" in reloaded
    assert reloaded.RequestedProcedureCodeSequence[0].CodeMeaning == "Synthetic Procedure"
    performed = reloaded.PerformedSeriesSequence[0]
    referenced = performed.ReferencedImageSequence[0]
    assert referenced.ReferencedSOPClassUID == ds.PerformedSeriesSequence[0].ReferencedImageSequence[0].ReferencedSOPClassUID
    assert referenced.ReferencedSOPInstanceUID == ds.PerformedSeriesSequence[0].ReferencedImageSequence[0].ReferencedSOPInstanceUID


def test_structured_report_basic_text_roundtrip(tmp_path):
    sr = build_basic_text_sr()
    path = save_dataset(sr, tmp_path / "sr.dcm")
    reloaded = load_dataset(path)

    assert reloaded.SOPClassUID == BasicTextSRStorage
    assert reloaded.ContentSequence[0].TextValue == sr.ContentSequence[0].TextValue
    assert reloaded.ContentSequence[0].ConceptNameCodeSequence[0].CodeValue == "121071"


def test_character_sets_roundtrip_preserves_utf8(tmp_path):
    ds = build_secondary_capture()
    original_name = "João^山田"
    ds.SpecificCharacterSet = ["ISO_IR 192"]
    ds.PatientName = original_name

    first = save_dataset(ds, tmp_path / "charset.dcm")
    reloaded = load_dataset(first)
    second = save_dataset(reloaded, tmp_path / "charset_copy.dcm")
    reread = load_dataset(second)

    assert str(reread.PatientName) == original_name
    raw = reread.PatientName.original_string
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    assert raw == original_name
    assert any(cs.lower() in {"utf-8", "utf8"} for cs in reread._character_set)


def test_multiframe_dataset_exposes_functional_groups(tmp_path):
    ds = build_multiframe_dataset(frames=3, shape=(4, 4))
    path = save_dataset(ds, tmp_path / "multi.dcm")
    reloaded = load_dataset(path)

    pixels = reloaded.pixel_array
    assert pixels.shape == (3, 4, 4)
    assert len(reloaded.PerFrameFunctionalGroupsSequence) == 3
    assert hasattr(reloaded.SharedFunctionalGroupsSequence[0], "PixelMeasuresSequence")
    assert reloaded.NumberOfFrames == 3


def test_secondary_capture_builds_valid_pixels(tmp_path):
    ds = build_secondary_capture(shape=(10, 10))
    path = save_dataset(ds, tmp_path / "sc.dcm")
    reloaded = load_dataset(path)

    assert reloaded.SOPClassUID == SecondaryCaptureImageStorage
    assert reloaded.pixel_array.shape == (10, 10)
    assert reloaded.PatientID == "SC-001"


def test_segmentation_creation_and_pixels(synthetic_datasets, tmp_path):
    source = synthetic_datasets[0]
    seg = build_segmentation(source)
    path = save_dataset(seg, tmp_path / "seg.dcm")
    loaded = load_dataset(path)

    assert loaded.SOPClassUID.name == "Segmentation Storage"
    assert loaded.SegmentationType == "BINARY"
    assert loaded.SegmentSequence[0].SegmentLabel == "Mask"

    pixels = loaded.pixel_array
    if pixels.ndim == 3:
        assert pixels.shape[1:] == (source.Rows, source.Columns)
    else:
        assert pixels.shape == (source.Rows, source.Columns)
    assert pixels.max() in (0, 1)


def test_special_vrs_and_private_tags_are_preserved(tmp_path):
    ds = build_special_vr_dataset()
    path = save_dataset(ds, tmp_path / "special.dcm")

    reloaded = load_dataset(path)
    private_tag = Tag(0x0099, 0x1001)
    assert private_tag in reloaded
    assert reloaded[private_tag].VR == "UN"
    assert reloaded[private_tag].value == b"\x01\x02\x03\x04"

    at_value = reloaded[Tag(0x0008, 0x2120)].value
    if isinstance(at_value, (list, tuple)):
        assert Tag(0x0008, 0x103E) in at_value
    else:
        assert at_value == Tag(0x0008, 0x103E)
    assert reloaded[Tag(0x0008, 0x0120)].value.startswith("https://dicom.tools/")
    of = np.frombuffer(reloaded[Tag(0x0028, 0x3003)].value, dtype=np.float32)
    od = np.frombuffer(reloaded[Tag(0x0028, 0x3004)].value, dtype=np.float64)
    assert np.allclose(of, [1.25, 2.5])
    assert np.allclose(od, [0.5, 0.75])


def test_deferred_read_lazy_loads_bulk_data(tmp_path):
    ds = build_secondary_capture(shape=(64, 64))
    original_pixels = np.frombuffer(ds.PixelData, dtype=np.uint16).copy()
    path = save_dataset(ds, tmp_path / "lazy.dcm")

    lazy = pydicom.dcmread(path, force=True, defer_size=256)
    raw = lazy.get_item("PixelData", keep_deferred=True)
    assert isinstance(raw, RawDataElement)
    assert raw.value is None and raw.length > 0

    extracted = lazy.pixel_array.reshape(-1)
    assert not isinstance(lazy["PixelData"], RawDataElement)
    assert np.array_equal(extracted, original_pixels)


def test_dicom_json_roundtrip_keeps_pixels_and_sequences(tmp_path):
    ds = build_secondary_capture(shape=(8, 8))
    nested = build_nested_sequence_dataset()
    ds.RequestedProcedureCodeSequence = nested.RequestedProcedureCodeSequence
    ds.PerformedSeriesSequence = nested.PerformedSeriesSequence

    payload = dataset_to_dicom_json(ds, bulk_data_threshold=0)
    parsed = json.loads(payload)
    assert "00080016" in parsed and parsed["00080016"]["vr"] == "UI"
    assert "7FE00010" in parsed  # PixelData

    rebuilt = dataset_from_dicom_json(payload)
    assert rebuilt.PatientID == ds.PatientID
    assert rebuilt.SOPClassUID == ds.SOPClassUID
    assert rebuilt.RequestedProcedureCodeSequence[0].CodeMeaning == "Synthetic Procedure"
    assert rebuilt.PerformedSeriesSequence[0].SeriesDescription == "Performed CT"
    assert rebuilt.PixelData == ds.PixelData
