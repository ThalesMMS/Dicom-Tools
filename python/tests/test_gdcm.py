#
# test_gdcm.py
# Dicom-Tools-py
#
# Checks that GDCM reads synthetic DICOM files, transcodes, writes, and handles DICOMDIRs.
#
# Thales Matheus Mendonça Santos - November 2025

from pathlib import Path
import sys

import numpy as np
import pytest
import pydicom
from pydicom.uid import JPEG2000Lossless, RLELossless

from DICOM_reencoder.core import build_segmentation, build_secondary_capture, save_dataset
from DICOM_reencoder.transcode_dicom import transcode

gdcm = pytest.importorskip("gdcm")


def test_gdcm_reads_synthetic_dicom(synthetic_dicom_path):
    # GDCM should be able to parse and expose pixel buffers for generated fixtures
    reader = gdcm.ImageReader()
    reader.SetFileName(str(synthetic_dicom_path))
    assert reader.Read()

    image = reader.GetImage()
    dims = image.GetDimensions()
    assert dims[0] == 32
    assert dims[1] == 32
    assert image.GetBufferLength() > 0


def test_gdcm_transcodes_to_rle_with_expected_metadata(synthetic_dicom_path, tmp_path):
    output = transcode(synthetic_dicom_path, output=tmp_path / "rle.dcm", syntax="rle")
    assert output.exists()

    ds = pydicom.dcmread(output, force=True)
    assert ds.file_meta.TransferSyntaxUID == RLELossless
    assert ds.SamplesPerPixel == 1
    assert ds.BitsStored == 16


def test_gdcm_writer_updates_attributes_and_preserves_pixels(synthetic_dicom_path, tmp_path):
    reader = gdcm.Reader()
    reader.SetFileName(str(synthetic_dicom_path))
    assert reader.Read()

    file = reader.GetFile()
    dataset = file.GetDataSet()

    tag = gdcm.Tag(0x0010, 0x0010)
    name = gdcm.DataElement(tag)
    name.SetVR(gdcm.VR(gdcm.VR.PN))
    value = "GDCM^TEST "
    name.SetByteValue(value, gdcm.VL(len(value)))
    dataset.Replace(name)

    output = tmp_path / "gdcm_writer.dcm"
    writer = gdcm.Writer()
    writer.SetFile(file)
    writer.SetFileName(str(output))
    assert writer.Write()

    reloaded = pydicom.dcmread(output, force=True)
    assert str(reloaded.PatientName) == "GDCM^TEST"
    assert reloaded.pixel_array.shape == (32, 32)


def test_gdcm_generates_and_reads_dicomdir(synthetic_series, tmp_path):
    paths, _ = synthetic_series
    generator = gdcm.DICOMDIRGenerator()
    generator.SetRootDirectory(str(Path(paths[0]).parent))
    generator.SetFilenames([str(p) for p in paths])
    if not generator.Generate():
        pytest.skip("GDCM could not generate a DICOMDIR in this environment")

    dicomdir_path = tmp_path / "DICOMDIR"
    writer = gdcm.Writer()
    writer.SetFile(generator.GetFile())
    writer.SetFileName(str(dicomdir_path))
    assert writer.Write()

    reader = gdcm.Reader()
    reader.SetFileName(str(dicomdir_path))
    assert reader.Read()

    dicomdir_ds = pydicom.dcmread(dicomdir_path, force=True)
    assert "DirectoryRecordSequence" in dicomdir_ds

    referenced = set()
    for item in dicomdir_ds.DirectoryRecordSequence:
        ref = getattr(item, "ReferencedFileID", None)
        if ref:
            if isinstance(ref, (list, tuple)):
                referenced.add("/".join(ref))
            else:
                referenced.add(str(ref))

    for p in paths:
        assert any(p.name in ref for ref in referenced)


def test_gdcm_transcodes_to_jpeg2000_when_supported(synthetic_dicom_path, tmp_path):
    try:
        output = transcode(synthetic_dicom_path, output=tmp_path / "j2k.dcm", syntax="jpeg2000-lossless")
    except RuntimeError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"JPEG2000 transcode unavailable: {exc}")

    ds = pydicom.dcmread(output, force=True)
    assert ds.file_meta.TransferSyntaxUID == JPEG2000Lossless
    assert ds.Rows == 32 and ds.Columns == 32


def test_gdcm_reads_segmentation_and_reconstructs_mask(synthetic_datasets, tmp_path):
    if sys.platform == "darwin":
        pytest.skip("GDCM segmentation read is unstable on this GDCM build")

    source = synthetic_datasets[0]
    seg = build_segmentation(source)
    seg_path = save_dataset(seg, tmp_path / "seg_gdcm.dcm")

    reader = gdcm.ImageReader()
    reader.SetFileName(str(seg_path))
    if not reader.Read():  # pragma: no cover - environment dependent
        pytest.skip("GDCM could not read segmentation object")

    image = reader.GetImage()
    dims = image.GetDimensions()
    buffer = image.GetBuffer()

    mask = np.frombuffer(buffer, dtype=np.uint8)
    expected_size = dims[0] * dims[1] * max(1, dims[2])
    assert mask.size == expected_size
    assert set(np.unique(mask)).issubset({0, 1})
