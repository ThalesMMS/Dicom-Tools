from interface.state.ui_state import UIState, ViewerState


def test_scroll_clamped_by_frame_count():
    viewer = ViewerState("2d", frame_count=3)
    viewer.slice_index = 1
    viewer.apply_scroll(5)
    assert viewer.slice_index == 2
    viewer.apply_scroll(-10)
    assert viewer.slice_index == 0


def test_set_frame_count_clamps_slice_index():
    viewer = ViewerState("mpr", slice_index=5, frame_count=10)
    viewer.set_frame_count(3)
    assert viewer.frame_count == 3
    assert viewer.slice_index == 2


def test_ui_state_overlays_and_viewers_persist():
    state = UIState()
    state.toggle_overlay("wl")  # disable
    state.set_active_viewer("mpr")
    mpr_state = state.get_viewer("mpr")
    mpr_state.apply_zoom(1.5)
    assert "wl" not in state.overlays_enabled
    # Switching back preserves overlays and independent viewer zoom
    state.set_active_viewer("2d")
    state.get_viewer("2d").apply_zoom(2.0)
    assert "wl" not in state.overlays_enabled
    assert state.get_viewer("mpr").zoom == 1.5
    assert state.get_viewer("2d").zoom == 2.0


def test_snapshot_contains_viewers():
    state = UIState()
    state.get_viewer("2d").apply_pan(1.0, -1.0)
    state.get_viewer("volume").apply_scroll(2)
    snap = state.snapshot()
    assert set(snap.keys()) == {"2d", "volume"}
    assert snap["2d"]["pan"] == (1.0, -1.0)
    assert snap["volume"]["slice_index"] == 2


def test_frames_multi_frame_handling():
    viewer = UIState().get_viewer("mpr")
    viewer.set_frame_count(5)
    viewer.slice_index = 4
    viewer.apply_scroll(10)
    assert viewer.slice_index == 4
    viewer.apply_scroll(-10)
    assert viewer.slice_index == 0
