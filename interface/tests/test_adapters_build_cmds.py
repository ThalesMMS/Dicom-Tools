import pytest

from interface.adapters import get_adapter
from interface.adapters.cpp_cli import CppCliAdapter
from interface.adapters.csharp_cli import CSharpCliAdapter
from interface.adapters.java_cli import JavaCliAdapter
from interface.adapters.python_cli import PythonCliAdapter
from interface.adapters.runner import RunResult
from interface.adapters.rust_cli import RustCliAdapter


def test_python_cli_builds_commands(tmp_path):
    adapter = PythonCliAdapter()
    input_path = str(tmp_path / "in.dcm")
    assert adapter._build_cmd("info", input_path, None, {"verbose": True})[-1] == "--verbose"
    cmd = adapter._build_cmd("to_image", input_path, None, {"frame": 1})
    assert any(part == "png" for part in cmd)
    assert "transcode" in " ".join(adapter._build_cmd("transcode", input_path, None, {"syntax": "explicit"}))
    assert any("validate_dicom" in part for part in adapter._build_cmd("validate", input_path, None, {}))
    echo_cmd = adapter._build_cmd("echo", input_path, None, {"host": "h", "port": 1})
    assert "dicom_echo" in " ".join(echo_cmd)
    volume_cmd = adapter._build_cmd("volume", input_path, None, {"preview": True})
    assert "volume" in volume_cmd
    nifti_cmd = adapter._build_cmd("nifti", input_path, None, {"no_compress": True})
    assert "nifti" in nifti_cmd
    assert adapter._build_cmd("stats", input_path, None, {})
    assert adapter._build_cmd("dump", input_path, None, {})


def test_rust_cli_builds_commands(tmp_path):
    adapter = RustCliAdapter()
    input_path = str(tmp_path / "in.dcm")
    assert adapter._build_cmd("info", input_path, None, {"verbose": True})[-1] == "--verbose"
    assert "to-image" in adapter._build_cmd("to_image", input_path, None, {"frame": 2})
    assert "transcode" in adapter._build_cmd("transcode", input_path, None, {"syntax": "ts"})
    assert "validate" in adapter._build_cmd("validate", input_path, None, {})
    assert "histogram" in adapter._build_cmd("histogram", input_path, None, {"bins": 8})
    assert "echo" in adapter._build_cmd("echo", input_path, None, {"host": "1.2.3.4", "port": 11112})
    assert "stats" in adapter._build_cmd("stats", input_path, None, {})


def test_cpp_cli_builds_commands(tmp_path):
    adapter = CppCliAdapter()
    cmd, outputs = adapter._build_cmd("to_image", str(tmp_path / "in.dcm"), None, {})
    assert "preview" in " ".join(cmd)
    assert outputs and outputs[0].endswith("preview.pgm")
    cmd, outputs = adapter._build_cmd("anonymize", str(tmp_path / "in.dcm"), None, {})
    assert "anonymize" in " ".join(cmd)
    cmd, outputs = adapter._build_cmd("transcode", str(tmp_path / "in.dcm"), None, {"syntax": "rle"})
    assert outputs


def test_java_cli_builds_commands(tmp_path):
    adapter = JavaCliAdapter()
    input_path = str(tmp_path / "in.dcm")
    assert "info" in adapter._build_cmd("info", input_path, None, {"json": True})
    assert any(part == "validate" for part in adapter._build_cmd("validate", input_path, None, {}))
    assert any(part == "stats" for part in adapter._build_cmd("histogram", input_path, None, {"bins": 4}))
    assert any(part == "to-image" for part in adapter._build_cmd("to_image", input_path, None, {"frame": 0}))
    assert any(part == "transcode" for part in adapter._build_cmd("transcode", input_path, None, {"syntax": "s"}))
    assert any(part == "echo" for part in adapter._build_cmd("echo", input_path, None, {"host": "h", "port": 1}))
    assert any(part == "store-scu" for part in adapter._build_cmd("store_scu", input_path, None, {"host": "h", "port": 1}))
    assert any(part == "mwl" for part in adapter._build_cmd("worklist", input_path, None, {"host": "h", "port": 1}))
    assert any(part == "qido" for part in adapter._build_cmd("qido", input_path, None, {"url": "http://x"}))
    assert any(part == "stow" for part in adapter._build_cmd("stow", input_path, None, {"url": "http://x"}))
    assert any(part == "wado" for part in adapter._build_cmd("wado", "", str(tmp_path / "out.dcm"), {"url": "http://x"}))
    assert any(part == "sr-summary" for part in adapter._build_cmd("sr_summary", input_path, None, {}))
    assert any(part == "rt-check" for part in adapter._build_cmd("rt_check", input_path, None, {}))


def test_csharp_cli_builds_commands(tmp_path):
    adapter = CSharpCliAdapter()
    input_path = str(tmp_path / "in.dcm")
    assert "info" in adapter._build_cmd("info", input_path, None, {})[1]
    assert "validate" in adapter._build_cmd("validate", input_path, None, {})[1]
    assert "histogram" in adapter._build_cmd("histogram", input_path, None, {"bins": 5})[1]
    assert any(part == "to-image" for part in adapter._build_cmd("to_image", input_path, None, {"frame": 0}))
    assert any(part == "transcode" for part in adapter._build_cmd("transcode", input_path, None, {"syntax": "s"}))
    assert any(part == "echo" for part in adapter._build_cmd("echo", input_path, None, {"host": "h", "port": 1}))
    assert any(part == "store-scu" for part in adapter._build_cmd("store_scu", input_path, None, {"host": "h", "port": 1})[1:])
    assert any(part == "worklist" for part in adapter._build_cmd("worklist", input_path, None, {"host": "h", "port": 1})[1:])
    assert any(part == "qido" for part in adapter._build_cmd("qido", input_path, None, {"url": "http://x"})[1:])
    assert any(part == "stow" for part in adapter._build_cmd("stow", input_path, None, {"url": "http://x"})[1:])
    assert any(part == "wado" for part in adapter._build_cmd("wado", input_path, str(tmp_path / "out.dcm"), {"url": "http://x"})[1:])
    assert any(part == "sr-summary" for part in adapter._build_cmd("sr_summary", input_path, None, {})[1:])
    assert any(part == "rt-check" for part in adapter._build_cmd("rt_check", input_path, None, {})[1:])


def test_get_adapter_invalid():
    assert get_adapter("python")
    assert get_adapter("rust")
    assert get_adapter("cpp")
    assert get_adapter("java")
    assert get_adapter("csharp")
    assert get_adapter("js")
    try:
        get_adapter("nope")
    except ValueError:
        pass
    else:  # pragma: no cover
        assert False, "Expected ValueError"


def test_cpp_test_runner_does_not_require_input(monkeypatch):
    monkeypatch.setattr(
        "interface.adapters.cpp_cli.run_process",
        lambda cmd, cwd=None: RunResult(ok=True, returncode=0, stdout="", stderr="", output_files=[]),
    )
    adapter = CppCliAdapter()
    result = adapter.handle({"op": "run_cpp_tests", "options": {}})
    assert result.ok is True


def test_java_test_runner_does_not_require_input(monkeypatch):
    monkeypatch.setattr(
        "interface.adapters.java_cli.run_process",
        lambda cmd, cwd=None: RunResult(ok=True, returncode=0, stdout="", stderr="", output_files=[]),
    )
    adapter = JavaCliAdapter()
    result = adapter.handle({"op": "run_java_tests", "options": {}})
    assert result.ok is True


# --- Additional edge cases for cpp no_input_ops (all members of the set) ---

@pytest.mark.parametrize("op", [
    "test_gdcm",
    "test_dcmtk",
    "test_itk",
    "test_vtk_unit",
    "test_utils",
    "test_integration",
    "test_edge_cases",
    "test_validation",
    "run_cpp_tests",
])
def test_cpp_all_no_input_ops_accept_empty_input(monkeypatch, op):
    monkeypatch.setattr(
        "interface.adapters.cpp_cli.run_process",
        lambda cmd, cwd=None: RunResult(ok=True, returncode=0, stdout="", stderr="", output_files=[]),
    )
    adapter = CppCliAdapter()
    result = adapter.handle({"op": op, "options": {}})
    assert result.ok is True, f"{op} should succeed without input"


def test_cpp_handle_missing_op_returns_error():
    adapter = CppCliAdapter()
    result = adapter.handle({"op": "", "input": "/some/file.dcm", "options": {}})
    assert result.ok is False
    assert result.returncode == 1
    assert result.stderr == "op is required"


def test_cpp_regular_op_without_input_returns_error():
    adapter = CppCliAdapter()
    result = adapter.handle({"op": "info", "input": "", "options": {}})
    assert result.ok is False
    assert result.returncode == 1
    assert result.stderr == "input is required"


def test_java_handle_missing_op_returns_error():
    adapter = JavaCliAdapter()
    result = adapter.handle({"op": "", "input": "/some/file.dcm", "options": {}})
    assert result.ok is False
    assert result.returncode == 1
    assert result.stderr == "op is required"


def test_java_handle_missing_input_for_info_returns_error():
    adapter = JavaCliAdapter()
    result = adapter.handle({"op": "info", "input": "", "options": {}})
    assert result.ok is False
    assert result.returncode == 1


@pytest.mark.parametrize("op", [
    "test_uid",
    "test_datetime",
    "test_charset",
    "test_workflow",
    "test_validation_java",
    "run_java_tests",
])
def test_java_test_ops_do_not_require_input(monkeypatch, op):
    monkeypatch.setattr(
        "interface.adapters.java_cli.run_process",
        lambda cmd, cwd=None: RunResult(ok=True, returncode=0, stdout="", stderr="", output_files=[]),
    )
    adapter = JavaCliAdapter()
    result = adapter.handle({"op": op, "options": {}})
    assert result.ok is True, f"{op} should succeed without input"
