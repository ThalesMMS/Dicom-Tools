import json
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
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert any(str(f).endswith(".pgm") for f in payload.get("output_files", []))
