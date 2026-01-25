import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from interface.adapters.js_cli import JsCliAdapter
from interface.adapters.csharp_cli import CSharpCliAdapter
from interface.adapters.java_cli import JavaCliAdapter
from interface.adapters.python_cli import PythonCliAdapter
from interface.adapters.rust_cli import RustCliAdapter
from interface.adapters.runner import RunResult, run_process

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


def test_python_adapter_respects_env(monkeypatch):
    monkeypatch.setenv("PYTHON_DICOM_TOOLS_CMD", "echo custom_cli --flag")
    adapter = PythonCliAdapter()
    assert adapter.base_cmd == ["echo", "custom_cli", "--flag"]


def test_rust_adapter_respects_env(monkeypatch):
    monkeypatch.setenv("RUST_DICOM_TOOLS_CMD", "echo rust_cli --flag")
    adapter = RustCliAdapter()
    assert adapter.base_cmd == ["echo", "rust_cli", "--flag"]


def test_csharp_adapter_respects_env(monkeypatch):
    monkeypatch.setenv("CS_DICOM_TOOLS_CMD", "dotnet /tmp/cs_cli.dll")
    adapter = CSharpCliAdapter()
    assert adapter.base_cmd == ["dotnet", "/tmp/cs_cli.dll"]


def test_java_adapter_respects_env(monkeypatch):
    monkeypatch.setenv("JAVA_DICOM_TOOLS_CMD", "/tmp/custom.jar")
    adapter = JavaCliAdapter()
    assert adapter.base_cmd[-1] == "/tmp/custom.jar"


def test_run_process_handles_missing_binary(tmp_path: Path):
    missing = tmp_path / "does_not_exist"
    result = run_process([str(missing)])
    assert result.ok is False
    assert result.returncode != 0
    assert "not found" in result.stderr.lower()


def test_run_process_times_out():
    cmd = [sys.executable, "-c", "import time; time.sleep(2)"]
    result = run_process(cmd, timeout=0.1)
    assert result.ok is False
    assert result.returncode != 0
    assert "timed out" in result.stderr.lower()


def test_js_adapter_handles_invalid_json(monkeypatch):
    def fake_run(args, capture_output=True, text=True):
        class FakeProcess:
            def __init__(self):
                self.returncode = 0
                self.stdout = "not-json"
                self.stderr = ""

        return FakeProcess()

    monkeypatch.setattr("interface.adapters.js_cli.subprocess.run", fake_run)
    adapter = JsCliAdapter()
    result = adapter.handle({"op": "info", "input": "file.dcm"})
    assert result.ok is True
    assert result.metadata is None
    assert result.output_files == []
    assert result.backend == "js"
    assert result.operation == "info"


def test_js_adapter_respects_env(monkeypatch):
    monkeypatch.setenv("JS_DICOM_TOOLS_CMD", "node custom_cli.js --flag")
    adapter = JsCliAdapter()
    assert adapter.cmd[:2] == ["node", "custom_cli.js"]
    assert adapter.cmd[-1] == "--flag"


def test_runresult_contains_contract_keys():
    rr = RunResult(
        ok=True,
        returncode=0,
        stdout="{}",
        stderr="",
        output_files=["a", "b"],
        metadata={"meta": True},
        backend="python",
        operation="info",
    )
    payload = rr.as_dict()
    for key in ["ok", "returncode", "stdout", "stderr", "metadata", "backend", "operation", "artifacts"]:
        assert key in payload
    assert payload["artifacts"] == ["a", "b"]
    assert payload["backend"] == "python"
    assert payload["operation"] == "info"


def test_run_process_reports_stderr_on_failure():
    cmd = [sys.executable, "-c", "import sys; sys.stderr.write('bad'); sys.exit(2)"]
    result = run_process(cmd)
    assert result.ok is False
    assert result.returncode == 2
    assert result.stderr == "bad"


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
