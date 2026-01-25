import pytest

from interface.runtime import InterfaceRuntime
from interface.utils.geometry import transform_point


def test_zoom_respects_origin_center():
    runtime = InterfaceRuntime.create(type("DummyEngine", (), {"render": lambda self, req: None})())
    viewer = runtime.state.get_viewer("2d")
    origin = (5.0, 5.0)
    runtime.inputs.zoom("2d", 2.0, origin=origin)

    # Point at origin should remain the same after scaling around origin
    assert transform_point(viewer.transform, origin) == origin


def test_scroll_updates_location_overlay():
    class Engine:
        def __init__(self) -> None:
            self.calls = 0

        def render(self, request):
            self.calls += 1
            meta = {"location_mm": float(request.slice_index), "slice_thickness": 1.5, "series_name": "Demo"}
            from interface.state.frames import Frame

            return Frame(viewer=request.viewer, slice_index=request.slice_index, width=64, height=64, metadata=meta)

    runtime = InterfaceRuntime.create(Engine())
    runtime.inputs.scroll("2d", 1)
    runtime.inputs.scroll("2d", 1)
    viewer = runtime.viewers.get("2d")
    overlays = viewer.current_overlays
    assert overlays["location"] == "Loc: 2.0 mm"
    assert overlays["thickness"].startswith("Thick: 1.5")
