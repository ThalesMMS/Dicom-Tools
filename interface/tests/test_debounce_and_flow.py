import json
from pathlib import Path

import pytest

from interface.components.render_loop import RenderLoop
from interface.input.event_bus import Event, EventBus
from interface.runtime import InterfaceRuntime
from interface.state.frames import Frame, FrameRequest


class CountingEngine:
    def __init__(self) -> None:
        self.requests: list[FrameRequest] = []

    def render(self, request: FrameRequest) -> Frame:
        self.requests.append(request)
        return Frame(viewer=request.viewer, slice_index=request.slice_index, width=32, height=32, metadata={"series_name": "Demo"})


def test_render_loop_debounce_like_behavior():
    bus = EventBus()
    engine = CountingEngine()
    RenderLoop(bus, engine)

    # Emit multiple frame_requested events in quick succession; loop should process sequentially
    for i in range(3):
        req = FrameRequest(viewer="2d", slice_index=i, zoom=1.0, pan=(0, 0), window_center=0, window_width=0, frame_count=1)
        bus.emit(Event("frame_requested", {"request": req}))

    assert len(engine.requests) == 3
    assert [r.slice_index for r in engine.requests] == [0, 1, 2]


def test_full_flow_with_backend_stub(tmp_path, monkeypatch):
    sample = tmp_path / "sample.dcm"
    sample.write_text("dummy")

    # Stub adapter to avoid real subprocess
    def fake_handle(request):
        return type("Result", (), {"as_dict": lambda self=None: {"ok": True, "metadata": {"series_uid": "S1"}}})()

    monkeypatch.setattr("interface.adapters.get_adapter", lambda backend: type("Stub", (), {"handle": fake_handle})())

    runtime = InterfaceRuntime.create(CountingEngine())
    runtime.inputs.scroll("2d", 1)
    viewer = runtime.viewers.get("2d")
    assert viewer.current_frame is not None
    overlays = viewer.current_overlays
    assert overlays["series"]
    assert "Im" in overlays["image_index"]
