#
# test_cli_tools_extra.py
# Dicom-Tools-py
#
# Covers standalone helper scripts: organize_dicom, modify_tags, split_multiframe, batch_process.
#

from __future__ import annotations

from pathlib import Path
import shutil

import pydicom
import pytest

from DICOM_reencoder.core import build_multiframe_dataset, build_synthetic_series, load_dataset, save_dataset
from DICOM_reencoder import organize_dicom
from DICOM_reencoder import modify_tags
from DICOM_reencoder import split_multiframe
from DICOM_reencoder import batch_process


def test_organize_by_series_copies_files(tmp_path):
    source_dir = tmp_path / "src"
    paths = build_synthetic_series(source_dir)
    dest_dir = tmp_path / "dest"

    organize_dicom.organize_by_series(str(source_dir), str(dest_dir), copy_mode=True, recursive=False)

    # Files should be organized under patient/study/series hierarchy
    organized_files = list(dest_dir.rglob("*.dcm"))
    assert len(organized_files) == len(paths)
    # Original files remain because copy_mode=True
    assert all(Path(p).exists() for p in paths)


def test_modify_tags_batch_overwrites_attributes(tmp_path):
    ds = build_multiframe_dataset(frames=2, shape=(4, 4))
    src_path = save_dataset(ds, tmp_path / "multi.dcm")
    output_path = tmp_path / "modified.dcm"

    modify_tags.modify_tags_batch(
        str(src_path),
        {"PatientName": "Edited^Name", "SeriesDescription": "Edited Series"},
        output_file=str(output_path),
    )

    reloaded = load_dataset(output_path)
    assert str(reloaded.PatientName) == "Edited^Name"
    assert reloaded.SeriesDescription == "Edited Series"


def test_split_multiframe_outputs_unique_frames(tmp_path):
    ds = build_multiframe_dataset(frames=3, shape=(5, 5))
    src_path = save_dataset(ds, tmp_path / "multi.dcm")
    out_dir = tmp_path / "split"

    frames = split_multiframe.split_multiframe(str(src_path), output_dir=str(out_dir), prefix="slice")
    assert frames == 3
    outputs = sorted(out_dir.glob("slice_frame_*.dcm"))
    assert len(outputs) == 3

    sop_uids = []
    for path in outputs:
        frame_ds = pydicom.dcmread(path, force=True)
        sop_uids.append(frame_ds.SOPInstanceUID)
        assert frame_ds.NumberOfFrames == 1
        assert frame_ds.InstanceNumber >= 1
    assert len(set(sop_uids)) == 3


def test_batch_process_pipeline(tmp_path, capsys):
    series_dir = tmp_path / "series"
    paths = build_synthetic_series(series_dir)

    files = batch_process.find_dicom_files(str(series_dir))
    assert len(files) == len(paths)

    # List files (output only; ensure no crash)
    batch_process.list_files(files)
    capsys.readouterr()

    # Anonymize and convert a single file
    out_dir = tmp_path / "out"
    batch_process.anonymize_batch(files[:1], output_dir=str(out_dir))
    batch_process.convert_batch(files[:1], output_dir=str(out_dir), output_format="png")

    anon_files = list(out_dir.glob("*_anonymized.dcm"))
    png_files = list(out_dir.glob("*.png"))
    assert anon_files and png_files

    # Validate batch runs without errors
    batch_process.validate_batch(files[:1])
    capsys.readouterr()
