import pytest

from interface.runtime import InterfaceRuntime


def test_tool_switch_changes_behavior():
    runtime = InterfaceRuntime.create(type("DummyEngine", (), {"render": lambda self, req: None})())
    viewer = runtime.state.get_viewer("2d")

    runtime.inputs.zoom("2d", 2.0)
    assert pytest.approx(viewer.zoom) == 2.0
    runtime.inputs.pan("2d", 5.0, 0.0)
    assert viewer.pan == (5.0, 0.0)

    # Drag (scroll) should change slice, not pan/zoom
    runtime.inputs.drag_slice("2d", 3)
    assert viewer.slice_index == 3
    assert viewer.pan == (5.0, 0.0)
    assert pytest.approx(viewer.zoom) == 2.0
