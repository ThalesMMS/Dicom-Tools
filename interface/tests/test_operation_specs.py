from interface.operations import DEFAULTS, SUITE_OPS, get_operation_spec


def test_cpp_info_uses_directory_output():
    spec = get_operation_spec("cpp", "info")
    assert spec["output"] == "directory"
    assert spec["has_options"] is False


def test_volume_requires_directory_input():
    spec = get_operation_spec("python", "volume")
    assert spec["input"] == "directory"
    assert spec["output"] == "file"


def test_rust_to_image_exposes_window_level_options():
    spec = get_operation_spec("rust", "to_image")
    for key in ["window_center", "window_width", "normalize"]:
        assert key in spec["option_keys"]


def test_echo_has_no_input_and_display_only_output():
    spec = get_operation_spec("python", "echo")
    assert spec["input"] == "none"
    assert spec["output"] == "display"


def test_default_java_and_csharp_suites_skip_network_echo():
    assert "echo" not in SUITE_OPS["java"]
    assert "echo" not in SUITE_OPS["csharp"]


def test_histogram_inherits_display_output_and_options():
    spec = get_operation_spec("rust", "histogram")
    assert spec["input"] == "file"
    assert spec["output"] == "display"
    assert "bins" in spec["option_keys"]
    assert spec["has_options"] is True


def test_vtk_ops_use_directory_io():
    spec = get_operation_spec("cpp", "vtk_export")
    assert spec["input"] == "directory"
    assert spec["output"] == "directory"


def test_wado_requires_output_but_no_input():
    spec = get_operation_spec("java", "wado")
    assert spec["input"] == "none"
    assert spec["output"] == "file"
    assert spec["output_required"] is True


def test_worklist_and_store_scu_input_requirements():
    worklist = get_operation_spec("java", "worklist")
    assert worklist["input"] == "none"
    assert worklist["has_options"] is True
    store_scu = get_operation_spec("java", "store_scu")
    assert store_scu["input"] == "file"
    assert store_scu["has_options"] is True


def test_csharp_dump_defaults_use_adapter_option_names():
    spec = get_operation_spec("csharp", "dump")
    assert "max_depth" in spec["options"]
    assert "depth" not in spec["options"]


def test_python_batch_ops_use_directory_and_display_specs():
    split_spec = get_operation_spec("python", "split_multiframe")
    assert split_spec["input"] == "file"
    assert split_spec["output"] == "directory"
    assert {"prefix", "frames", "info"} <= set(split_spec["option_keys"])

    list_spec = get_operation_spec("python", "batch_list")
    assert list_spec["input"] == "directory"
    assert list_spec["output"] == "display"
    assert "recursive" in list_spec["option_keys"]

    convert_spec = get_operation_spec("python", "batch_convert")
    assert convert_spec["input"] == "directory"
    assert convert_spec["output"] == "directory"
    assert {"format", "recursive"} <= set(convert_spec["option_keys"])


def test_backend_test_ops_do_not_require_input():
    cpp_spec = get_operation_spec("cpp", "test_gdcm")
    assert cpp_spec["input"] == "none"
    assert cpp_spec["output"] == "display"

    java_spec = get_operation_spec("java", "run_java_tests")
    assert java_spec["input"] == "none"
    assert java_spec["output"] == "display"

    csharp_spec = get_operation_spec("csharp", "run_cs_tests")
    assert csharp_spec["input"] == "none"
    assert csharp_spec["output"] == "display"


def test_backend_test_defaults_match_no_input_display_specs():
    test_ops = {
        "cpp": [
            "test_gdcm",
            "test_dcmtk",
            "test_itk",
            "test_vtk_unit",
            "test_utils",
            "test_integration",
            "test_edge_cases",
            "test_validation",
            "run_cpp_tests",
        ],
        "java": [
            "test_uid",
            "test_datetime",
            "test_charset",
            "test_workflow",
            "test_validation_java",
            "run_java_tests",
        ],
        "csharp": [
            "test_anonymize_cs",
            "test_uid_cs",
            "test_datetime_cs",
            "test_charset_cs",
            "test_dictionary_cs",
            "test_file_operations_cs",
            "test_sequence_cs",
            "test_value_representation_cs",
            "test_option_parser_cs",
            "test_stats_helpers_cs",
            "run_cs_tests",
        ],
    }
    for backend, ops in test_ops.items():
        for op in ops:
            spec = get_operation_spec(backend, op)
            defaults = DEFAULTS[backend][op]
            assert spec["input"] == "none"
            assert defaults["input"] == "none"
            assert spec["output"] == "display"
            assert defaults["output"] == "display"
