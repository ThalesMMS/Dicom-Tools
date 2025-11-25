import pytest

from interface.input import Command, Event, EventBus
from interface.runtime import InterfaceRuntime
from interface.state.frames import Frame


class DummyEngine:
    def __init__(self) -> None:
        self.requests = []

    def render(self, request):
        self.requests.append(request)
        meta = {"location_mm": float(request.slice_index), "slice_thickness": 1.0}
        return Frame(viewer=request.viewer, slice_index=request.slice_index, width=128, height=128, metadata=meta)


def test_event_bus_subscribe_and_unsubscribe():
    bus = EventBus()
    calls: list[int] = []

    def handler(event: Event):
        calls.append(event.payload["value"])

    bus.subscribe("ping", handler)
    bus.emit(Event("ping", {"value": 1}))
    bus.unsubscribe("ping", handler)
    bus.emit(Event("ping", {"value": 2}))

    assert calls == [1]


def test_event_bus_dispatch_preserves_order():
    bus = EventBus()
    sequence: list[str] = []

    def handler(command: Command):
        sequence.append(f"cmd:{command.payload['value']}")
        return Event("pong", {"value": command.payload["value"]})

    bus.register_command("ping", handler)
    bus.subscribe("pong", lambda event: sequence.append(f"evt:{event.payload['value']}"))

    bus.dispatch(Command("ping", {"value": 7}))

    assert sequence == ["cmd:7", "evt:7"]


def test_input_controller_updates_active_tool_and_state():
    runtime = InterfaceRuntime.create(DummyEngine())

    runtime.inputs.scroll("2d", 2)
    assert runtime.state.active_tool == "scroll"
    assert runtime.state.get_viewer("2d").slice_index == 2

    runtime.inputs.zoom("2d", 1.5)
    assert runtime.state.active_tool == "zoom"
    assert pytest.approx(runtime.state.get_viewer("2d").zoom) == 1.5

    before = runtime.state.get_viewer("2d").slice_index
    runtime.inputs.drag_slice("2d", 3)
    assert runtime.state.active_tool == "scroll"  # drag maps to scroll
    assert runtime.state.get_viewer("2d").slice_index == before + 3


def test_tools_apply_per_viewer_state_isolated():
    runtime = InterfaceRuntime.create(DummyEngine())

    runtime.inputs.zoom("2d", 1.2)
    runtime.inputs.zoom("mpr", 1.8)
    runtime.inputs.pan("mpr", 2.0, -1.0)

    assert pytest.approx(runtime.state.get_viewer("2d").zoom) == 1.2
    mpr_state = runtime.state.get_viewer("mpr")
    assert pytest.approx(mpr_state.zoom) == 1.8
    assert mpr_state.pan == (2.0, -1.0)
