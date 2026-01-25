import json
from interface.adapters.cpp_cli import CppCliAdapter
from interface.adapters.rust_cli import RustCliAdapter
from interface.adapters import runner


class DummyResult:
    def __init__(self, stdout: str):
        self.ok = True
        self.returncode = 0
        self.stdout = stdout
        self.stderr = ""
        self.output_files = []
        self.metadata = None
        self.backend = None
        self.operation = None


def test_rust_adapter_parses_json_metadata(monkeypatch, tmp_path):
    payload = {"ok": True, "metadata": {"a": 1}}

    def fake_run(cmd, cwd=None, timeout=None):
        return DummyResult(json.dumps(payload))

    monkeypatch.setattr("interface.adapters.rust_cli.run_process", fake_run)
    monkeypatch.setattr("interface.adapters.rust_cli.parse_json_maybe", lambda text: json.loads(text))
    adapter = RustCliAdapter()
    result = adapter.handle({"op": "info", "input": str(tmp_path / "in.dcm")})
    assert result.metadata == payload
    assert result.backend == "rust"
    assert result.operation == "info"


def test_cpp_adapter_parses_json_metadata(monkeypatch, tmp_path):
    payload = {"ok": True, "metadata": {"module": "gdcm"}}

    def fake_run(cmd, cwd=None, timeout=None):
        return DummyResult(json.dumps(payload))

    monkeypatch.setattr("interface.adapters.cpp_cli.run_process", fake_run)
    monkeypatch.setattr("interface.adapters.cpp_cli.parse_json_maybe", lambda text: json.loads(text))
    adapter = CppCliAdapter()
    cmd, outputs = adapter._build_cmd("info", str(tmp_path / "in.dcm"), str(tmp_path / "out"), {})
    result = adapter.handle({"op": "info", "input": str(tmp_path / "in.dcm"), "output": str(tmp_path / "out")})
    assert result.metadata == payload
    assert result.backend == "cpp"
    assert result.operation == "info"
