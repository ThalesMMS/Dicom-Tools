import pytest

from interface.runtime import InterfaceRuntime
from interface.state.frames import Frame
from interface.utils.geometry import identity_matrix


class DummyEngine:
    def __init__(self) -> None:
        self.requests = []

    def render(self, request):
        self.requests.append(request)
        # Return a synthetic frame; metadata mirrors request to keep assertions simple
        meta = {
            "location_mm": float(request.slice_index),
            "slice_thickness": 2.0,
            "series_name": request.series_uid or "Series",
        }
        return Frame(viewer=request.viewer, slice_index=request.slice_index, width=256, height=256, metadata=meta)


def make_runtime():
    engine = DummyEngine()
    runtime = InterfaceRuntime.create(engine)
    return runtime, engine


def test_scroll_updates_slice_and_requests_frame():
    runtime, engine = make_runtime()
    runtime.inputs.scroll("2d", 1)
    viewer_state = runtime.state.get_viewer("2d")
    assert viewer_state.slice_index == 1
    assert engine.requests[-1].slice_index == 1
    viewer = runtime.viewers.get("2d")
    assert viewer is not None
    assert viewer.current_frame is not None
    assert viewer.current_frame.slice_index == 1


def test_zoom_and_pan_update_transform():
    runtime, _ = make_runtime()
    viewer_state = runtime.state.get_viewer("2d")
    assert viewer_state.transform == identity_matrix()
    runtime.inputs.zoom("2d", 2.0)
    runtime.inputs.pan("2d", 3.0, -2.0)
    assert pytest.approx(viewer_state.zoom) == 2.0
    assert viewer_state.pan == (3.0, -2.0)
    # Translation stored in the last column of the matrix
    assert pytest.approx(viewer_state.transform[0][2]) == 3.0
    assert pytest.approx(viewer_state.transform[1][2]) == -2.0


def test_window_level_overlay_updates():
    runtime, _ = make_runtime()
    runtime.inputs.window_level("2d", center=40, width=400)
    viewer = runtime.viewers.get("2d")
    assert viewer is not None
    overlays = viewer.current_overlays
    assert overlays["wl"] == "WL: 40 / WW: 400"


def test_switch_viewers_preserves_state():
    runtime, _ = make_runtime()
    runtime.inputs.zoom("2d", 1.5)
    runtime.inputs.zoom("mpr", 2.2)
    assert pytest.approx(runtime.state.get_viewer("2d").zoom) == 1.5
    assert pytest.approx(runtime.state.get_viewer("mpr").zoom) == 2.2
    # Changing MPR slice should not affect 2D
    runtime.inputs.scroll("mpr", 3)
    assert runtime.state.get_viewer("2d").slice_index == 0
    assert runtime.state.get_viewer("mpr").slice_index == 3


def test_overlay_toggle_disables_layer():
    runtime, _ = make_runtime()
    runtime.inputs.scroll("2d", 1)  # ensure a frame exists
    runtime.inputs.toggle_overlay("2d", "wl")
    assert "wl" not in runtime.state.overlays_enabled
    viewer = runtime.viewers.get("2d")
    assert viewer is not None
    assert "wl" not in viewer.current_overlays


def test_rebuild_mpr_triggers_plane_request():
    runtime, engine = make_runtime()
    runtime.inputs.rebuild_mpr("mpr", "sagittal")
    assert engine.requests[-1].plane == "sagittal"
    viewer = runtime.viewers.get("mpr")
    assert viewer is not None
    assert viewer.current_frame is not None
    assert viewer.current_frame.viewer == "mpr"
