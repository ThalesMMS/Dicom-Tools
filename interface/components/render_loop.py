"""Reactive render loop: commands → core → frame_ready → viewers."""

from __future__ import annotations

from typing import Protocol

from interface.input.event_bus import Event, EventBus
from interface.state.frames import Frame, FrameRequest


class FrameEngine(Protocol):
    def render(self, request: FrameRequest) -> Frame:
        """Produce a frame for a request. Implemented by real engines or mocks."""


class RenderLoop:
    def __init__(self, bus: EventBus, engine: FrameEngine) -> None:
        self.bus = bus
        self.engine = engine
        self._rendering = False
        self.bus.subscribe("frame_requested", self._on_frame_requested)

    def _on_frame_requested(self, event: Event) -> None:
        payload = event.payload or {}
        request: FrameRequest = payload.get("request")
        if request is None:
            return
        if self._rendering:
            # Drop recursive frame requests to avoid infinite loops
            return
        self._rendering = True
        try:
            frame = self.engine.render(request)
            self.bus.emit(Event("frame_ready", {"frame": frame, "viewer": request.viewer, "frame_request": request}))
        finally:
            self._rendering = False
