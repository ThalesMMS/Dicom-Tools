#
# test_volume_nifti_transcode.py
# Dicom-Tools-py
#
# Covers volume, NIfTI export, and transfer syntax transcoding against sample data.
#
# Thales Matheus Mendonça Santos - November 2025

from pathlib import Path
import shutil

import pytest
import pydicom
from pydicom.uid import ExplicitVRLittleEndian

from DICOM_reencoder.series_to_nifti import convert_series_to_nifti
from DICOM_reencoder.transcode_dicom import transcode
from DICOM_reencoder.volume_builder import build_volume


@pytest.fixture()
def sample_series_dir(tmp_path):
    source = Path(__file__).resolve().parents[2] / "sample_series"
    target = tmp_path / "sample_series"
    target.mkdir()

    for path in sorted(source.glob("*.dcm"))[:10]:
        shutil.copy2(path, target / path.name)

    return target


def test_build_volume_from_sample_series(sample_series_dir):
    pytest.importorskip("dicom_numpy")

    volume, affine, metadata = build_volume(sample_series_dir)
    slice_count = len(list(sample_series_dir.glob("*.dcm")))

    assert len(volume.shape) == 3
    assert slice_count in volume.shape  # order can vary depending on orientation handling
    assert affine.shape == (4, 4)
    assert metadata["shape"] and slice_count in metadata["shape"]
    assert len(metadata["spacing_mm"]) == 3
    assert metadata["stats"]["max"] >= metadata["stats"]["min"]


def test_convert_series_to_nifti_writes_output(sample_series_dir, tmp_path):
    pytest.importorskip("SimpleITK")

    meta_path = tmp_path / "export_meta.json"
    output_path = tmp_path / "series.nii.gz"
    output, meta = convert_series_to_nifti(
        sample_series_dir,
        output=str(output_path),
        metadata_path=str(meta_path),
    )

    first_uid = pydicom.dcmread(sorted(sample_series_dir.glob("*.dcm"))[0], force=True).SeriesInstanceUID

    assert output == output_path
    assert output_path.exists()
    assert meta_path.exists()
    assert meta["series_uid"] == first_uid
    assert len(meta["size"]) == 3
    assert Path(meta["output"]) == output_path


def test_transcode_produces_explicit_vr_file(sample_series_dir, tmp_path):
    pytest.importorskip("gdcm")

    input_file = sorted(sample_series_dir.glob("*.dcm"))[0]
    destination = tmp_path / "explicit.dcm"

    result = transcode(input_file, output=destination, syntax="explicit")

    assert result == destination
    assert destination.exists()

    output_ds = pydicom.dcmread(destination, force=True)
    assert output_ds.file_meta.TransferSyntaxUID == ExplicitVRLittleEndian
