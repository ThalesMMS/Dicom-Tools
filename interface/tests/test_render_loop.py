from interface.components.render_loop import RenderLoop
from interface.input.event_bus import Event, EventBus
from interface.state.frames import Frame, FrameRequest


class FakeEngine:
    def __init__(self) -> None:
        self.requests = []

    def render(self, request: FrameRequest) -> Frame:
        self.requests.append(request)
        return Frame(viewer=request.viewer, slice_index=request.slice_index, width=64, height=64, metadata={"location_mm": 1.0})


def test_render_loop_emits_frame_ready_once():
    bus = EventBus()
    engine = FakeEngine()
    ready_events: list[Event] = []
    bus.subscribe("frame_ready", ready_events.append)

    RenderLoop(bus, engine)

    request = FrameRequest(viewer="2d", slice_index=0, zoom=1.0, pan=(0.0, 0.0), window_center=0, window_width=0, frame_count=1)
    bus.emit(Event("frame_requested", {"request": request}))

    assert len(engine.requests) == 1
    assert len(ready_events) == 1
    assert ready_events[0].payload["frame"].viewer == "2d"
