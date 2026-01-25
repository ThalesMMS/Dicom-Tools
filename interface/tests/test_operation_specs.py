from interface.app import get_operation_spec


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
