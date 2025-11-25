#
# test_cli_and_web.py
# Dicom-Tools-py
#
# Covers CLI entry-points and the Flask web interface.
#

from __future__ import annotations

import io
from argparse import Namespace
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from DICOM_reencoder import cli as cli_mod
from DICOM_reencoder import dicom_echo, dicom_query
from DICOM_reencoder.core import build_synthetic_series, load_dataset
from DICOM_reencoder.web_interface import app as flask_app


def _capture_print(func, capsys, **kwargs: Any) -> str:
    func(Namespace(**kwargs))
    return capsys.readouterr().out


def test_cli_summary_stats_anonymize_validate_png(tmp_path, synthetic_dicom_path, capsys):
    summary_out = _capture_print(cli_mod.cmd_summary, capsys, file=str(synthetic_dicom_path), json=True, verbose=False)
    assert '"id": "TEST-123"' in summary_out

    stats_out = _capture_print(cli_mod.cmd_stats, capsys, file=str(synthetic_dicom_path))
    assert "total_pixels" in stats_out

    png_path = tmp_path / "frame.png"
    _capture_print(
        cli_mod.cmd_png,
        capsys,
        file=str(synthetic_dicom_path),
        frame=0,
        format="png",
        output=str(png_path),
    )
    assert png_path.exists()

    anon_path = tmp_path / "anon.dcm"
    _capture_print(cli_mod.cmd_anonymize, capsys, file=str(synthetic_dicom_path), output=str(anon_path))
    assert anon_path.exists()

    validate_out = _capture_print(cli_mod.cmd_validate, capsys, file=str(synthetic_dicom_path), json=True, include_info=False)
    assert '"ok":' in validate_out


def test_cli_echo_uses_send(monkeypatch, capsys):
    called = {}

    def fake_send(host, port, calling_aet="X", called_aet="Y", timeout=5):
        called["args"] = (host, port, calling_aet, called_aet, timeout)
        return 0x0000

    monkeypatch.setattr(cli_mod, "send_c_echo", fake_send)
    out = _capture_print(cli_mod.cmd_echo, capsys, host="127.0.0.1", port=11112)
    assert "0x0000" in out
    assert called["args"][0] == "127.0.0.1"


def test_cli_volume_builds_files(tmp_path, capsys):
    series_dir = tmp_path / "series"
    paths = build_synthetic_series(series_dir)

    out_npy = tmp_path / "vol.npy"
    out_meta = tmp_path / "vol.json"
    _capture_print(
        cli_mod.cmd_volume,
        capsys,
        directory=str(series_dir),
        output=str(out_npy),
        metadata=str(out_meta),
        preview=False,
    )
    assert out_npy.exists()
    assert out_meta.exists()


def test_cli_nifti_and_transcode_skip_if_missing(tmp_path, synthetic_dicom_path, capsys):
    sitk = pytest.importorskip("SimpleITK")
    out_path = tmp_path / "series.nii.gz"
    meta_path = tmp_path / "series_meta.json"
    series_dir = tmp_path / "series"
    build_synthetic_series(series_dir)
    _capture_print(
        cli_mod.cmd_nifti,
        capsys,
        directory=str(series_dir),
        output=str(out_path),
        series_uid=None,
        no_compress=False,
        metadata=str(meta_path),
    )
    assert out_path.exists()
    assert meta_path.exists()

    gdcm = pytest.importorskip("gdcm")
    out = tmp_path / "transcoded.dcm"
    _capture_print(
        cli_mod.cmd_transcode,
        capsys,
        file=str(synthetic_dicom_path),
        output=str(out),
        syntax="explicit",
    )
    assert out.exists()


def test_dicom_echo_wraps_send(monkeypatch):
    called = {}

    def fake_send(host, port, calling_aet="X", called_aet="Y", timeout=5):
        called["host"] = host
        return 0x0000

    monkeypatch.setattr(dicom_echo, "send_c_echo", fake_send)
    status = dicom_echo.run_echo("localhost", 1234, calling_aet="A", called_aet="B", timeout=1)
    assert status == 0x0000
    assert called["host"] == "localhost"


def test_dicom_query_builders():
    patient = dicom_query.create_patient_query(patient_name="John^Doe", patient_id="123")
    assert patient.QueryRetrieveLevel == "PATIENT"
    assert patient.PatientID == "123"

    study = dicom_query.create_study_query(patient_name="Jane^Doe", modality="CT")
    assert study.QueryRetrieveLevel == "STUDY"
    assert study.ModalitiesInStudy == "CT"

    series = dicom_query.create_series_query("1.2.3", modality="MR")
    assert series.QueryRetrieveLevel == "SERIES"
    assert series.StudyInstanceUID == "1.2.3"
    assert series.Modality == "MR"


@pytest.mark.parametrize("endpoint", ["metadata", "stats", "image", "validate"])
def test_web_interface_upload_and_fetch(endpoint, synthetic_dicom_path):
    client = flask_app.test_client()
    with open(synthetic_dicom_path, "rb") as f:
        upload_resp = client.post("/api/upload", data={"file": (io.BytesIO(f.read()), "sample.dcm")})
    assert upload_resp.status_code == 200
    payload = upload_resp.get_json()
    assert payload["success"] is True
    filename = payload["filename"]

    resp = client.get(f"/api/{endpoint}/{filename}")
    assert resp.status_code == 200
    if endpoint != "image":
        assert resp.is_json


def test_web_interface_anonymize_and_download(synthetic_dicom_path):
    client = flask_app.test_client()
    with open(synthetic_dicom_path, "rb") as f:
        upload_resp = client.post("/api/upload", data={"file": (io.BytesIO(f.read()), "sample.dcm")})
    filename = upload_resp.get_json()["filename"]

    anon_resp = client.post(f"/api/anonymize/{filename}")
    assert anon_resp.status_code == 200
    anon_name = anon_resp.get_json()["filename"]

    download_resp = client.get(f"/api/download/{anon_name}")
    assert download_resp.status_code == 200
    assert download_resp.data
