#
# factories.py
# Dicom-Tools-py
#
# Creates synthetic DICOM datasets and series used in tests and demonstrations.
#
# Thales Matheus Mendonça Santos - November 2025

"""Synthetic dataset creation helpers used in tests and demos."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import numpy as np
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.tag import Tag
from pydicom.uid import (
    BasicTextSRStorage,
    CTImageStorage,
    EnhancedCTImageStorage,
    ExplicitVRLittleEndian,
    SegmentationStorage,
    SecondaryCaptureImageStorage,
    generate_uid,
)


def _base_file_meta(sop_class_uid=CTImageStorage, transfer_syntax=ExplicitVRLittleEndian) -> Dataset:
    # Minimal file meta block that lets GDCM/Pydicom understand the dataset layout
    meta = Dataset()
    meta.MediaStorageSOPClassUID = sop_class_uid
    meta.TransferSyntaxUID = transfer_syntax
    meta.ImplementationClassUID = generate_uid()
    meta.FileMetaInformationVersion = b"\x00\x01"
    meta.MediaStorageSOPInstanceUID = generate_uid()
    return meta


def build_slice(rows: int, cols: int, position: Tuple[float, float, float], *,
                pixel_spacing: Sequence[float], study_uid: str, series_uid: str, instance: int) -> FileDataset:
    """Create a single CT slice dataset with predictable numeric pixels."""
    file_meta = _base_file_meta()
    ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)

    ds.SOPClassUID = CTImageStorage
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = study_uid
    ds.SeriesInstanceUID = series_uid
    ds.Modality = "CT"
    ds.SeriesNumber = 1
    ds.InstanceNumber = instance
    ds.PatientName = "Test^Patient"
    ds.PatientID = "TEST-123"
    ds.PatientBirthDate = "19700101"
    ds.PatientSex = "O"
    now = datetime.now(timezone.utc)
    ds.StudyDate = now.strftime("%Y%m%d")
    ds.StudyTime = now.strftime("%H%M%S")

    ds.Rows = rows
    ds.Columns = cols
    ds.PixelSpacing = list(pixel_spacing)
    ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
    ds.ImagePositionPatient = list(position)
    ds.SliceThickness = 1.0
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelRepresentation = 0
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15

    # Populate the pixel buffer with deterministic values so tests can make strong assertions
    pixel_values = np.arange(rows * cols, dtype=np.uint16).reshape((rows, cols)) + instance
    ds.PixelData = pixel_values.tobytes()
    return ds


def build_synthetic_series(output_dir: Path, *, slices: int = 4, shape: Tuple[int, int] = (32, 32),
                           pixel_spacing: Sequence[float] = (0.7, 0.7)) -> List[Path]:
    """Write a small, consistent DICOM series and return file paths."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    study_uid = generate_uid()
    series_uid = generate_uid()

    paths: List[Path] = []
    for idx in range(slices):
        position = (0.0, 0.0, float(idx))
        ds = build_slice(shape[0], shape[1], position, pixel_spacing=pixel_spacing,
                         study_uid=study_uid, series_uid=series_uid, instance=idx + 1)
        file_path = output_dir / f"slice_{idx+1}.dcm"
        ds.save_as(file_path)
        paths.append(file_path)

    # Return the on-disk paths so callers can feed them directly into readers
    return paths


def build_nested_sequence_dataset() -> FileDataset:
    """Generate a dataset that exercises nested sequences for round-trip tests."""
    file_meta = _base_file_meta()
    ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)
    ds.PatientName = "Seq^Tester"
    ds.PatientID = "SEQ-001"
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.SOPClassUID = CTImageStorage
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID

    procedure = Dataset()
    procedure.CodeValue = "12345"
    procedure.CodingSchemeDesignator = "99TEST"
    procedure.CodeMeaning = "Synthetic Procedure"
    ds.RequestedProcedureCodeSequence = [procedure]

    referenced = Dataset()
    referenced.ReferencedSOPClassUID = CTImageStorage
    referenced.ReferencedSOPInstanceUID = generate_uid()

    performed = Dataset()
    performed.SeriesInstanceUID = ds.SeriesInstanceUID
    performed.ReferencedImageSequence = [referenced]
    performed.SeriesDescription = "Performed CT"
    ds.PerformedSeriesSequence = [performed]
    return ds


def build_basic_text_sr() -> FileDataset:
    """Create a minimal Basic Text SR document for structural round-trip checks."""
    file_meta = _base_file_meta(sop_class_uid=BasicTextSRStorage)
    ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)
    now = datetime.now(timezone.utc)

    ds.SOPClassUID = BasicTextSRStorage
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.Modality = "SR"
    ds.PatientName = "Report^Patient"
    ds.PatientID = "SR-001"
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.SeriesNumber = 7
    ds.InstanceNumber = 1
    ds.ContentDate = now.strftime("%Y%m%d")
    ds.ContentTime = now.strftime("%H%M%S")
    ds.CompletionFlag = "COMPLETE"
    ds.VerificationFlag = "UNVERIFIED"
    ds.SpecificCharacterSet = ["ISO_IR 192"]

    code = Dataset()
    code.CodeValue = "121071"
    code.CodingSchemeDesignator = "DCM"
    code.CodeMeaning = "Findings"

    text_item = Dataset()
    text_item.RelationshipType = "CONTAINS"
    text_item.ValueType = "TEXT"
    text_item.ConceptNameCodeSequence = [code]
    text_item.TextValue = "Synthetic SR content for verification."

    ds.ContentSequence = [text_item]
    return ds


def build_multiframe_dataset(frames: int = 3, shape: Tuple[int, int] = (8, 8)) -> FileDataset:
    """Produce a small enhanced-style multi-frame dataset with functional groups."""
    rows, cols = shape
    file_meta = _base_file_meta(sop_class_uid=EnhancedCTImageStorage)
    ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)

    ds.SOPClassUID = EnhancedCTImageStorage
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.Modality = "CT"
    ds.SeriesNumber = 2
    ds.InstanceNumber = 1

    ds.Rows = rows
    ds.Columns = cols
    ds.NumberOfFrames = frames
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.SamplesPerPixel = 1
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0

    ds.PerFrameFunctionalGroupsSequence = []
    for idx in range(frames):
        fg = Dataset()
        frame_content = Dataset()
        frame_content.DimensionIndexValues = [idx + 1]
        frame_content.FrameAcquisitionNumber = idx + 1
        fg.FrameContentSequence = [frame_content]

        plane_position = Dataset()
        plane_position.ImagePositionPatient = [0.0, 0.0, float(idx)]
        fg.PlanePositionSequence = [plane_position]
        ds.PerFrameFunctionalGroupsSequence.append(fg)

    pixel_measures = Dataset()
    pixel_measures.PixelSpacing = [0.5, 0.5]
    pixel_measures.SliceThickness = 1.0
    shared = Dataset()
    shared.PixelMeasuresSequence = [pixel_measures]
    ds.SharedFunctionalGroupsSequence = [shared]

    data = np.arange(frames * rows * cols, dtype=np.uint16).reshape((frames, rows, cols))
    ds.PixelData = data.tobytes()
    return ds


def build_secondary_capture(shape: Tuple[int, int] = (16, 16)) -> FileDataset:
    """Construct a simple Secondary Capture dataset from scratch."""
    rows, cols = shape
    file_meta = _base_file_meta(sop_class_uid=SecondaryCaptureImageStorage)
    ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)

    ds.SOPClassUID = SecondaryCaptureImageStorage
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.Modality = "SC"
    ds.PatientName = "Capture^Patient"
    ds.PatientID = "SC-001"
    ds.SeriesNumber = 3
    ds.InstanceNumber = 1

    ds.Rows = rows
    ds.Columns = cols
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.SamplesPerPixel = 1
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0

    pixels = np.arange(rows * cols, dtype=np.uint16).reshape((rows, cols))
    ds.PixelData = pixels.tobytes()
    return ds


def build_segmentation(source: FileDataset, mask: np.ndarray | None = None) -> FileDataset:
    """Create a minimal binary segmentation object derived from a source image."""
    rows, cols = int(source.Rows), int(source.Columns)
    seg_mask = mask if mask is not None else np.ones((rows, cols), dtype=np.uint8)

    file_meta = _base_file_meta(sop_class_uid=SegmentationStorage)
    ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)

    ds.SOPClassUID = SegmentationStorage
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = source.StudyInstanceUID
    ds.SeriesInstanceUID = generate_uid()
    ds.SeriesNumber = 9
    ds.InstanceNumber = 1
    ds.Modality = "SEG"
    ds.ContentLabel = "TEST"
    ds.ContentDescription = "Synthetic segmentation"
    ds.SegmentationType = "BINARY"
    ds.Manufacturer = "DicomTools"
    ds.Rows = rows
    ds.Columns = cols
    ds.NumberOfFrames = 1
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 1
    ds.BitsStored = 1
    ds.HighBit = 0
    ds.PixelRepresentation = 0
    ds.LossyImageCompression = "00"

    # Shared functional groups
    pixel_measures = Dataset()
    pixel_measures.PixelSpacing = source.get("PixelSpacing", [1.0, 1.0])
    pixel_measures.SliceThickness = source.get("SliceThickness", 1.0)
    shared = Dataset()
    shared.PixelMeasuresSequence = [pixel_measures]
    if source.get("ImageOrientationPatient"):
        orientation = Dataset()
        orientation.ImageOrientationPatient = source.ImageOrientationPatient
        shared.PlaneOrientationSequence = [orientation]
    ds.SharedFunctionalGroupsSequence = [shared]

    # Per-frame functional groups
    frame = Dataset()
    frame_content = Dataset()
    frame_content.DimensionIndexValues = [1]
    frame.FrameContentSequence = [frame_content]
    if source.get("ImagePositionPatient"):
        position = Dataset()
        position.ImagePositionPatient = source.ImagePositionPatient
        frame.PlanePositionSequence = [position]
    ds.PerFrameFunctionalGroupsSequence = [frame]

    # Define a single segment
    category = Dataset()
    category.CodeValue = "T-D0050"
    category.CodingSchemeDesignator = "SRT"
    category.CodeMeaning = "Tissue"

    seg_type = Dataset()
    seg_type.CodeValue = "T-04000"
    seg_type.CodingSchemeDesignator = "SRT"
    seg_type.CodeMeaning = "Organ"

    segment = Dataset()
    segment.SegmentNumber = 1
    segment.SegmentLabel = "Mask"
    segment.SegmentedPropertyCategoryCodeSequence = [category]
    segment.SegmentedPropertyTypeCodeSequence = [seg_type]
    ds.SegmentSequence = [segment]

    # Reference the source image
    ref_image = Dataset()
    ref_image.ReferencedSOPClassUID = source.SOPClassUID
    ref_image.ReferencedSOPInstanceUID = source.SOPInstanceUID
    derivation = Dataset()
    derivation.SourceImageSequence = [ref_image]
    ds.DerivationImageSequence = [derivation]

    # Pack the binary mask; pydicom/gdcm expect bit-packed segmentation frames
    if seg_mask.dtype != np.uint8:
        seg_mask = seg_mask.astype(np.uint8)
    packed = np.packbits(seg_mask.reshape(-1), bitorder="little").tobytes()
    ds.PixelData = packed
    return ds


def build_special_vr_dataset() -> FileDataset:
    """Create a dataset that exercises uncommon VRs and private tags."""
    file_meta = _base_file_meta()
    ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)

    ds.PatientName = "VR^Tester"
    ds.PatientID = "VR-001"
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.SOPClassUID = CTImageStorage
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID

    # Private tag block with raw bytes stored as UN to ensure preservation
    ds.add_new(Tag(0x0099, 0x0010), "LO", "DICOMTOOLS")
    raw_private = b"\x01\x02\x03\x04"
    ds.add_new(Tag(0x0099, 0x1001), "UN", raw_private)

    # AT: attribute tag reference
    ds.add_new(Tag(0x0008, 0x2120), "AT", [Tag(0x0008, 0x103e)])

    # UR: URI VR
    ds.add_new(Tag(0x0008, 0x0120), "UR", "https://dicom.tools/resource")

    # Other float VRs to ensure encoding is round-tripped
    ds.add_new(Tag(0x0028, 0x3003), "OF", np.array([1.25, 2.5], dtype=np.float32).tobytes())
    ds.add_new(Tag(0x0028, 0x3004), "OD", np.array([0.5, 0.75], dtype=np.float64).tobytes())

    return ds
