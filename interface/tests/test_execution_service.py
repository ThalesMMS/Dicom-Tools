"""Tests for interface/services/execution.py — validate_request, prepare_request,
execute_operation, and execute_suite."""

import pytest

from interface.adapters.runner import RunResult
from interface.operations.specs import get_operation_spec
from interface.services.execution import (
    execute_operation,
    execute_suite,
    prepare_request,
    validate_request,
)


# ---------------------------------------------------------------------------
# Helpers / stubs
# ---------------------------------------------------------------------------

def _make_file_spec(**overrides):
    spec = {"input": "file", "output": "file", "output_required": False}
    spec.update(overrides)
    return spec


def _make_display_spec(**overrides):
    spec = {"input": "file", "output": "display", "output_required": False}
    spec.update(overrides)
    return spec


def _make_none_input_spec(**overrides):
    spec = {"input": "none", "output": "display", "output_required": False}
    spec.update(overrides)
    return spec


class _FakeAdapter:
    """A simple stub that always returns success."""

    def __init__(self, ok=True, returncode=0, stdout="", stderr=""):
        self._result = RunResult(ok=ok, returncode=returncode, stdout=stdout, stderr=stderr, output_files=[])

    def handle(self, request):
        self._last_request = request
        return self._result


class _RaisingAdapter:
    def handle(self, request):
        raise RuntimeError("boom")


# ---------------------------------------------------------------------------
# validate_request
# ---------------------------------------------------------------------------

class TestValidateRequest:
    def test_returns_none_on_valid_file_input(self, tmp_path):
        f = tmp_path / "in.dcm"
        f.touch()
        spec = _make_file_spec()
        assert validate_request("info", str(f), None, spec) is None

    def test_missing_output_required(self, tmp_path):
        f = tmp_path / "in.dcm"
        f.touch()
        spec = _make_none_input_spec(output_required=True)
        error = validate_request("wado", str(f), None, spec)
        assert error is not None
        assert "output" in error.lower()

    def test_missing_input_when_required(self):
        spec = _make_file_spec()
        error = validate_request("info", "", None, spec)
        assert error is not None
        assert "input" in error.lower()

    def test_nonexistent_input_path(self, tmp_path):
        spec = _make_file_spec()
        error = validate_request("info", str(tmp_path / "no_such.dcm"), None, spec)
        assert error is not None
        assert "does not exist" in error.lower()

    def test_file_op_given_directory(self, tmp_path):
        d = tmp_path / "series"
        d.mkdir()
        spec = _make_file_spec()
        error = validate_request("info", str(d), None, spec)
        assert error is not None
        assert "single file" in error.lower()

    def test_directory_op_given_file(self, tmp_path):
        f = tmp_path / "in.dcm"
        f.touch()
        spec = {"input": "directory", "output": "file", "output_required": False}
        error = validate_request("volume", str(f), None, spec)
        assert error is not None
        assert "folder" in error.lower()

    def test_directory_output_given_a_file_path(self, tmp_path):
        f_input = tmp_path / "in.dcm"
        f_input.touch()
        f_output = tmp_path / "existing_file.txt"
        f_output.touch()
        spec = {"input": "file", "output": "directory", "output_required": False}
        error = validate_request("dump", str(f_input), str(f_output), spec)
        assert error is not None
        assert "folder" in error.lower()

    def test_directory_output_given_a_dir_is_ok(self, tmp_path):
        f_input = tmp_path / "in.dcm"
        f_input.touch()
        d_output = tmp_path / "out"
        d_output.mkdir()
        spec = {"input": "file", "output": "directory", "output_required": False}
        error = validate_request("dump", str(f_input), str(d_output), spec)
        assert error is None

    def test_none_input_op_with_empty_path_is_valid(self):
        spec = _make_none_input_spec()
        error = validate_request("echo", "", None, spec)
        assert error is None

    def test_custom_op_does_not_require_input(self, tmp_path):
        spec = {"input": "optional", "output": "file", "output_required": False}
        error = validate_request("custom", "", None, spec)
        assert error is None

    def test_output_required_with_output_provided_passes(self, tmp_path):
        spec = _make_none_input_spec(output_required=True)
        error = validate_request("wado", "", str(tmp_path / "out.dcm"), spec)
        assert error is None


# ---------------------------------------------------------------------------
# prepare_request
# ---------------------------------------------------------------------------

class TestPrepareRequest:
    def test_returns_dict_with_expected_keys(self, tmp_path):
        f = tmp_path / "in.dcm"
        f.touch()
        spec = _make_display_spec()
        req = prepare_request("python", "info", str(f), None, {}, spec)
        assert req["backend"] == "python"
        assert req["op"] == "info"
        assert req["input"] == str(f)
        assert req["output"] is None  # display → None
        assert req["options"] == {}

    def test_none_input_spec_with_empty_input_normalizes_to_empty_string(self, tmp_path):
        spec = _make_none_input_spec()
        req = prepare_request("python", "echo", "", None, {}, spec)
        assert req["input"] == ""

    def test_creates_parent_dir_for_file_output(self, tmp_path):
        f = tmp_path / "in.dcm"
        f.touch()
        out_file = tmp_path / "sub" / "result.dcm"
        spec = _make_file_spec()
        req = prepare_request("python", "anonymize", str(f), str(out_file), {}, spec)
        assert out_file.parent.exists()
        assert req["output"] == str(out_file)

    def test_creates_directory_output_dir(self, tmp_path):
        f = tmp_path / "in.dcm"
        f.touch()
        out_dir = tmp_path / "out_dir"
        spec = {"input": "file", "output": "directory", "output_required": False}
        req = prepare_request("cpp", "info", str(f), str(out_dir), {}, spec)
        assert out_dir.exists()
        assert out_dir.is_dir()
        assert req["output"] == str(out_dir)

    def test_display_output_sets_output_none(self, tmp_path):
        f = tmp_path / "in.dcm"
        f.touch()
        spec = _make_display_spec()
        req = prepare_request("python", "validate", str(f), "/some/path", {}, spec)
        assert req["output"] is None

    def test_options_passed_through(self, tmp_path):
        f = tmp_path / "in.dcm"
        f.touch()
        spec = _make_display_spec()
        opts = {"json": True, "bins": 16}
        req = prepare_request("python", "stats", str(f), None, opts, spec)
        assert req["options"] == opts

    def test_to_image_output_inferred_when_output_dir(self, tmp_path):
        f = tmp_path / "myscan.dcm"
        f.touch()
        out_dir = tmp_path / "imgs"
        out_dir.mkdir()
        spec = _make_file_spec()
        req = prepare_request("python", "to_image", str(f), str(out_dir), {}, spec)
        assert req["output"] == str(out_dir / "myscan.png")


# ---------------------------------------------------------------------------
# execute_operation
# ---------------------------------------------------------------------------

class TestExecuteOperation:
    def test_delegates_to_adapter_handle(self):
        adapter = _FakeAdapter(ok=True, stdout="output")
        request = {"backend": "python", "op": "info", "input": "/x.dcm", "output": None, "options": {}}
        result = execute_operation(adapter, request)
        assert result.ok is True
        assert result.stdout == "output"
        assert adapter._last_request is request

    def test_returns_adapter_result_directly(self):
        adapter = _FakeAdapter(ok=False, returncode=1, stderr="error")
        result = execute_operation(adapter, {})
        assert result.ok is False
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# execute_suite
# ---------------------------------------------------------------------------

class TestExecuteSuite:
    def test_empty_ops_returns_empty_list(self):
        adapter = _FakeAdapter()
        results = execute_suite("python", [], lambda op: {}, adapter=adapter)
        assert results == []

    def test_successful_op_appears_in_results(self, tmp_path):
        f = tmp_path / "in.dcm"
        f.touch()

        adapter = _FakeAdapter(ok=True)

        def get_defaults(op):
            return {"input": str(f)}

        results = execute_suite("python", ["info"], get_defaults, adapter=adapter)
        assert len(results) == 1
        assert results[0]["op"] == "info"
        assert results[0]["ok"] is True

    def test_adapter_exception_captured_per_op(self, tmp_path):
        f = tmp_path / "in.dcm"
        f.touch()

        def get_defaults(op):
            return {"input": str(f)}

        results = execute_suite("python", ["info"], get_defaults, adapter=_RaisingAdapter())
        assert len(results) == 1
        assert results[0]["ok"] is False
        assert "boom" in results[0]["error"]

    def test_missing_input_for_required_op_captured_as_error(self):
        def get_defaults(op):
            return {}  # no input provided

        results = execute_suite("python", ["info"], get_defaults, adapter=_FakeAdapter())
        assert len(results) == 1
        assert results[0]["ok"] is False

    def test_multiple_ops_all_processed(self, tmp_path):
        f = tmp_path / "in.dcm"
        f.touch()
        adapter = _FakeAdapter(ok=True)

        def get_defaults(op):
            return {"input": str(f)}

        ops = ["info", "validate"]
        results = execute_suite("python", ops, get_defaults, adapter=adapter)
        assert len(results) == 2
        op_names = [r["op"] for r in results]
        assert "info" in op_names
        assert "validate" in op_names

    def test_backend_key_normalized_to_lowercase(self, tmp_path):
        f = tmp_path / "in.dcm"
        f.touch()
        adapter = _FakeAdapter(ok=True)

        def get_defaults(op):
            return {"input": str(f)}

        results = execute_suite("PYTHON", ["info"], get_defaults, adapter=adapter)
        assert len(results) == 1
        assert results[0]["ok"] is True

    def test_no_input_ops_run_without_defaults(self):
        """Test ops with input=none (e.g. echo) run even with empty defaults."""
        adapter = _FakeAdapter(ok=True)

        def get_defaults(op):
            return {}  # no input — echo doesn't need one

        results = execute_suite("python", ["echo"], get_defaults, adapter=adapter)
        assert len(results) == 1
        assert results[0]["ok"] is True

    def test_result_payload_merged_from_as_dict(self, tmp_path):
        f = tmp_path / "in.dcm"
        f.touch()
        adapter = _FakeAdapter(ok=True, stdout="hello")

        def get_defaults(op):
            return {"input": str(f)}

        results = execute_suite("python", ["validate"], get_defaults, adapter=adapter)
        assert "stdout" in results[0]

    def test_none_defaults_fall_back_to_empty_dict(self):
        """get_defaults_fn returning None should not crash."""
        adapter = _FakeAdapter(ok=True)

        def get_defaults(op):
            return None

        # echo has input=none, so empty defaults are fine
        results = execute_suite("python", ["echo"], get_defaults, adapter=adapter)
        assert len(results) == 1