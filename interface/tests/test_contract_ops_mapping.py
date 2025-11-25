import json
from pathlib import Path

import pytest

from interface.adapters.cpp_cli import CppCliAdapter
from interface.adapters.csharp_cli import CSharpCliAdapter
from interface.adapters.java_cli import JavaCliAdapter
from interface.adapters.js_cli import JsCliAdapter
from interface.adapters.python_cli import PythonCliAdapter
from interface.adapters.rust_cli import RustCliAdapter


@pytest.mark.parametrize(
    "adapter_cls, ops",
    [
        (PythonCliAdapter, ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump", "volume", "nifti", "echo"]),
        (RustCliAdapter, ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump", "histogram", "echo"]),
        (CppCliAdapter, ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump"]),
        (JavaCliAdapter, ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump", "echo", "histogram"]),
        (CSharpCliAdapter, ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump", "echo", "histogram"]),
    ],
)
def test_adapters_map_canonical_ops(adapter_cls, ops, tmp_path):
    adapter = adapter_cls()
    input_path = str(tmp_path / "in.dcm")
    dir_input = str(tmp_path)
    for op in ops:
        out = tmp_path / f"out_{op}"
        if hasattr(adapter, "_build_cmd"):
            if op in {"volume", "nifti"}:
                cmd = adapter._build_cmd(op, dir_input, str(out), {})
            else:
                cmd = adapter._build_cmd(op, input_path, str(out), {})
            assert cmd is not None, f"{adapter_cls.__name__} missing op {op}"


def test_js_adapter_accepts_all_ops(monkeypatch, tmp_path):
    # Monkeypatch subprocess to avoid executing external binary
    def fake_run(args, capture_output=True, text=True):
        class FakeProcess:
            def __init__(self):
                self.returncode = 0
                self.stdout = json.dumps({"ok": True})
                self.stderr = ""

        return FakeProcess()

    monkeypatch.setattr("interface.adapters.js_cli.subprocess.run", fake_run)
    adapter = JsCliAdapter()
    for op in ["info", "anonymize", "to_image", "transcode", "validate", "stats", "dump", "volume", "nifti", "echo"]:
        result = adapter.handle({"op": op, "input": str(tmp_path / "in.dcm")})
        assert result.ok is True
        assert result.operation == op
