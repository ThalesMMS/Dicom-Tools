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
from pydicom.uid import CTImageStorage, ExplicitVRLittleEndian, generate_uid


def _base_file_meta() -> Dataset:
    # Minimal file meta block that lets GDCM/Pydicom understand the dataset layout
    meta = Dataset()
    meta.MediaStorageSOPClassUID = CTImageStorage
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
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
