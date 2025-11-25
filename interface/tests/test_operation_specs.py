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
