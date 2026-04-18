"""Tests for interface/operations/specs.py — requires_input, uses_directory_input,
normalize_output_path, build_spec_hint, and get_operation_spec edge cases."""

import pytest

from interface.operations.specs import (
    build_spec_hint,
    get_operation_spec,
    normalize_output_path,
    requires_input,
    uses_directory_input,
)


# ---------------------------------------------------------------------------
# requires_input
# ---------------------------------------------------------------------------

class TestRequiresInput:
    def test_custom_op_never_requires_input(self):
        spec = {"input": "file"}
        assert requires_input(spec, "custom") is False

    def test_file_input_requires_input(self):
        spec = {"input": "file"}
        assert requires_input(spec, "info") is True

    def test_directory_input_requires_input(self):
        spec = {"input": "directory"}
        assert requires_input(spec, "volume") is True

    def test_none_input_does_not_require_input(self):
        spec = {"input": "none"}
        assert requires_input(spec, "echo") is False

    def test_optional_input_does_not_require_input(self):
        spec = {"input": "optional"}
        assert requires_input(spec, "anything") is False

    def test_missing_input_key_defaults_to_requiring_input(self):
        # An empty spec has no "input" key; spec.get("input") → None,
        # which is not in {"none", "optional"}, so input is required.
        spec = {}
        assert requires_input(spec, "info") is True

    def test_echo_spec_does_not_require_input(self):
        spec = get_operation_spec("python", "echo")
        assert requires_input(spec, "echo") is False

    def test_worklist_spec_does_not_require_input(self):
        spec = get_operation_spec("java", "worklist")
        assert requires_input(spec, "worklist") is False

    def test_info_spec_requires_input(self):
        spec = get_operation_spec("python", "info")
        assert requires_input(spec, "info") is True


# ---------------------------------------------------------------------------
# uses_directory_input
# ---------------------------------------------------------------------------

class TestUsesDirectoryInput:
    def test_directory_spec_returns_true(self):
        assert uses_directory_input({"input": "directory"}) is True

    def test_file_spec_returns_false(self):
        assert uses_directory_input({"input": "file"}) is False

    def test_none_spec_returns_false(self):
        assert uses_directory_input({"input": "none"}) is False

    def test_empty_spec_returns_false(self):
        assert uses_directory_input({}) is False

    def test_volume_spec_uses_directory(self):
        spec = get_operation_spec("python", "volume")
        assert uses_directory_input(spec) is True

    def test_info_spec_does_not_use_directory(self):
        spec = get_operation_spec("python", "info")
        assert uses_directory_input(spec) is False


# ---------------------------------------------------------------------------
# normalize_output_path
# ---------------------------------------------------------------------------

class TestNormalizeOutputPath:
    def test_no_output_returns_none(self):
        spec = {"output": "file"}
        assert normalize_output_path("info", "/input/file.dcm", None, spec) is None

    def test_empty_output_returns_none(self):
        spec = {"output": "file"}
        assert normalize_output_path("info", "/input/file.dcm", "", spec) is None

    def test_display_output_returns_none(self):
        spec = {"output": "display"}
        assert normalize_output_path("info", "/input/file.dcm", "/some/path", spec) is None

    def test_directory_output_returns_string_of_path(self, tmp_path):
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        spec = {"output": "directory"}
        result = normalize_output_path("info", str(tmp_path / "file.dcm"), str(out_dir), spec)
        assert result == str(out_dir)

    def test_file_output_not_dir_returns_string(self, tmp_path):
        out_file = tmp_path / "result.dcm"
        spec = {"output": "file"}
        result = normalize_output_path("anonymize", str(tmp_path / "input.dcm"), str(out_file), spec)
        assert result == str(out_file)

    def test_to_image_when_output_is_dir(self, tmp_path):
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        spec = {"output": "file"}
        result = normalize_output_path("to_image", str(tmp_path / "myscan.dcm"), str(out_dir), spec)
        assert result == str(out_dir / "myscan.png")

    def test_anonymize_when_output_is_dir(self, tmp_path):
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        spec = {"output": "file"}
        result = normalize_output_path("anonymize", str(tmp_path / "myscan.dcm"), str(out_dir), spec)
        assert result == str(out_dir / "myscan_anon.dcm")

    def test_transcode_when_output_is_dir(self, tmp_path):
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        spec = {"output": "file"}
        result = normalize_output_path("transcode", str(tmp_path / "myscan.dcm"), str(out_dir), spec)
        assert result == str(out_dir / "myscan_transcoded.dcm")

    def test_volume_when_output_is_dir(self, tmp_path):
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        spec = {"output": "file"}
        result = normalize_output_path("volume", str(tmp_path / "series"), str(out_dir), spec)
        assert result == str(out_dir / "series_volume.npy")

    def test_nifti_when_output_is_dir(self, tmp_path):
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        spec = {"output": "file"}
        result = normalize_output_path("nifti", str(tmp_path / "series"), str(out_dir), spec)
        assert result == str(out_dir / "series_volume.nii.gz")

    def test_unknown_op_when_output_is_dir_uses_stem(self, tmp_path):
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        spec = {"output": "file"}
        result = normalize_output_path("custom_op", str(tmp_path / "myfile.dcm"), str(out_dir), spec)
        assert result == str(out_dir / "myfile")

    def test_empty_input_stem_falls_back_to_output(self, tmp_path):
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        spec = {"output": "file"}
        # input_path with no stem (like a bare name with no extension and empty string)
        result = normalize_output_path("to_image", "", str(out_dir), spec)
        assert result == str(out_dir / "output.png")


# ---------------------------------------------------------------------------
# build_spec_hint
# ---------------------------------------------------------------------------

class TestBuildSpecHint:
    def test_includes_backend(self):
        spec = {"input": "file", "output": "display", "option_keys": ["json"], "description": ""}
        hint = build_spec_hint(spec, "python", "")
        assert "Backend: python" in hint

    def test_includes_library_when_not_all_or_default(self):
        spec = {"input": "file", "output": "display", "option_keys": [], "description": ""}
        hint = build_spec_hint(spec, "python", "pydicom")
        assert "Lib: pydicom" in hint

    def test_skips_library_when_all(self):
        spec = {"input": "file", "output": "display", "option_keys": [], "description": ""}
        hint = build_spec_hint(spec, "python", "All")
        assert "Lib:" not in hint

    def test_skips_library_when_default(self):
        spec = {"input": "file", "output": "display", "option_keys": [], "description": ""}
        hint = build_spec_hint(spec, "python", "Default")
        assert "Lib:" not in hint

    def test_skips_library_when_empty(self):
        spec = {"input": "file", "output": "display", "option_keys": [], "description": ""}
        hint = build_spec_hint(spec, "python", "")
        assert "Lib:" not in hint

    def test_skips_backend_when_empty(self):
        spec = {"input": "file", "output": "display", "option_keys": [], "description": ""}
        hint = build_spec_hint(spec, "", "")
        assert "Backend:" not in hint

    def test_includes_input_label_for_file(self):
        spec = {"input": "file", "output": "display", "option_keys": [], "description": ""}
        hint = build_spec_hint(spec, "", "")
        assert "Single file" in hint

    def test_includes_input_label_for_directory(self):
        spec = {"input": "directory", "output": "display", "option_keys": [], "description": ""}
        hint = build_spec_hint(spec, "", "")
        assert "Folder/series" in hint

    def test_includes_input_label_for_none(self):
        spec = {"input": "none", "output": "display", "option_keys": [], "description": ""}
        hint = build_spec_hint(spec, "", "")
        assert "No input" in hint

    def test_includes_input_label_for_optional(self):
        spec = {"input": "optional", "output": "display", "option_keys": [], "description": ""}
        hint = build_spec_hint(spec, "", "")
        assert "Optional input" in hint

    def test_includes_output_label_for_display(self):
        spec = {"input": "file", "output": "display", "option_keys": [], "description": ""}
        hint = build_spec_hint(spec, "", "")
        assert "Display only" in hint

    def test_includes_output_label_for_file(self):
        spec = {"input": "file", "output": "file", "option_keys": [], "description": ""}
        hint = build_spec_hint(spec, "", "")
        assert "Output file" in hint

    def test_includes_output_label_for_directory(self):
        spec = {"input": "file", "output": "directory", "option_keys": [], "description": ""}
        hint = build_spec_hint(spec, "", "")
        assert "Output folder" in hint

    def test_includes_option_keys(self):
        spec = {"input": "file", "output": "display", "option_keys": ["json", "verbose"], "description": ""}
        hint = build_spec_hint(spec, "", "")
        assert "json" in hint
        assert "verbose" in hint

    def test_no_options_shows_no_options(self):
        spec = {"input": "file", "output": "display", "option_keys": [], "description": ""}
        hint = build_spec_hint(spec, "", "")
        assert "no options" in hint

    def test_includes_description(self):
        spec = {"input": "file", "output": "display", "option_keys": [], "description": "Does something useful."}
        hint = build_spec_hint(spec, "", "")
        assert "Does something useful." in hint

    def test_unknown_input_falls_back_to_file_folder(self):
        spec = {"input": "blob", "output": "display", "option_keys": [], "description": ""}
        hint = build_spec_hint(spec, "", "")
        assert "File/folder" in hint

    def test_both_backend_and_library_joined_with_dot(self):
        spec = {"input": "file", "output": "display", "option_keys": [], "description": ""}
        hint = build_spec_hint(spec, "java", "dcm4che")
        assert "Backend: java · Lib: dcm4che" in hint


# ---------------------------------------------------------------------------
# get_operation_spec — edge cases
# ---------------------------------------------------------------------------

class TestGetOperationSpec:
    def test_unknown_op_gets_defaults(self):
        spec = get_operation_spec("python", "totally_unknown_op")
        assert spec["input"] == "file"
        assert spec["output"] == "file"
        assert spec["output_required"] is False

    def test_backend_case_insensitive(self):
        spec_lower = get_operation_spec("python", "info")
        spec_upper = get_operation_spec("PYTHON", "info")
        assert spec_lower == spec_upper

    def test_override_replaces_base_fields(self):
        # cpp info overrides output from "display" to "directory"
        spec = get_operation_spec("cpp", "info")
        assert spec["output"] == "directory"
        assert spec["has_options"] is False

    def test_spec_defaults_output_required_false(self):
        spec = get_operation_spec("python", "info")
        assert spec["output_required"] is False

    def test_wado_has_output_required_true(self):
        spec = get_operation_spec("java", "wado")
        assert spec["output_required"] is True

    def test_option_keys_populated_from_defaults_when_missing(self):
        # Java info has no option_keys in canonical spec fallback but does in override
        spec = get_operation_spec("java", "info")
        assert "json" in spec["option_keys"]

    def test_has_options_false_when_no_keys(self):
        spec = get_operation_spec("cpp", "test_gdcm")
        assert spec["has_options"] is False
        assert spec["option_keys"] == []

    def test_has_options_true_when_keys_present(self):
        spec = get_operation_spec("python", "to_image")
        assert spec["has_options"] is True

    def test_vtk_op_directory_io(self):
        for vtk_op in ["vtk_export", "vtk_nifti", "vtk_isosurface", "vtk_mip"]:
            spec = get_operation_spec("cpp", vtk_op)
            assert spec["input"] == "directory", vtk_op
            assert spec["output"] == "directory", vtk_op

    def test_csharp_worklist_input_is_none(self):
        spec = get_operation_spec("csharp", "worklist")
        assert spec["input"] == "none"

    def test_rust_stats_has_no_options(self):
        spec = get_operation_spec("rust", "stats")
        assert spec["has_options"] is False
        assert spec["option_keys"] == []

    def test_custom_op_has_optional_input(self):
        spec = get_operation_spec("python", "custom")
        assert spec["input"] == "optional"