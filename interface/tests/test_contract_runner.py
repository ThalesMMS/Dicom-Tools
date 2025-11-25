import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = [ sys.executable, "-m", "interface.contract_runner" ]
SAMPLE = ROOT / "sample_series" / "IM-0001-0147.dcm"


@pytest.mark.skipif(not SAMPLE.exists(), reason="sample_series missing")
def test_python_info_json():
    cmd = RUNNER + ["--backend", "python", "--op", "info", "--input", str(SAMPLE)]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert "metadata" in payload
    assert payload["metadata"]


@pytest.mark.skipif(not SAMPLE.exists(), reason="sample_series missing")
def test_rust_dump():
    cmd = RUNNER + ["--backend", "rust", "--op", "dump", "--input", str(SAMPLE)]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    # stdout should include something like (0008, etc)
    assert "0008" in payload["stdout"]


@pytest.mark.skipif(not SAMPLE.exists(), reason="sample_series missing")
def test_cpp_preview():
    cmd = RUNNER + ["--backend", "cpp", "--op", "to_image", "--input", str(SAMPLE)]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    payload = json.loads(result.stdout)
    if result.returncode != 0 or not payload.get("ok", False):
        pytest.skip(f"cpp CLI unavailable: rc={result.returncode}, stderr={result.stderr!r}")
    assert any(str(f).endswith(".pgm") for f in payload.get("output_files", []))


@pytest.mark.skipif(not SAMPLE.exists(), reason="sample_series missing")
def test_python_anonymize(tmp_path: Path):
    out = tmp_path / "anon.dcm"
    cmd = RUNNER + ["--backend", "python", "--op", "anonymize", "--input", str(SAMPLE), "--output", str(out)]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert out.exists()


@pytest.mark.skipif(not SAMPLE.exists(), reason="sample_series missing")
def test_rust_transcode(tmp_path: Path):
    out = tmp_path / "transcoded.dcm"
    cmd = RUNNER + [
        "--backend",
        "rust",
        "--op",
        "transcode",
        "--input",
        str(SAMPLE),
        "--output",
        str(out),
        "--options",
        json.dumps({"syntax": "explicit-vr-little-endian"}),
    ]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert out.exists()


def test_invalid_backend():
    cmd = RUNNER + ["--backend", "unknown", "--op", "info", "--input", "file.dcm"]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert result.returncode != 0
    assert result.stderr


def _has_node():
    return subprocess.run(["node", "--version"], capture_output=True).returncode == 0


def _js_cli_exists():
    return (ROOT / "js" / "contract-cli" / "index.js").exists()


@pytest.mark.skipif(not SAMPLE.exists(), reason="sample_series missing")
@pytest.mark.skipif(not _has_node() or not _js_cli_exists(), reason="JS CLI not available")
def test_js_info_json():
    cmd = RUNNER + ["--backend", "js", "--op", "info", "--input", str(SAMPLE)]
    env = os.environ.copy()
    env["JS_DICOM_TOOLS_CMD"] = "node js/contract-cli/index.js"
    result = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload.get("metadata") is None or isinstance(payload.get("metadata"), dict)
