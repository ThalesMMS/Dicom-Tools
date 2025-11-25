"""Unified input controller that normalizes interactions into commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from interface.input.event_bus import Command, EventBus


@dataclass
class InputEvent:
    kind: str
    payload: Dict[str, object]


class InputController:
    """Maps raw UI gestures to Commands using viewer-specific adapters."""

    def __init__(self, bus: EventBus, adapters: List["InputAdapter"] | None = None) -> None:
        self.bus = bus
        self.adapters: Dict[str, "InputAdapter"] = {}
        for adapter in adapters or []:
            self.register_adapter(adapter)

    def register_adapter(self, adapter: "InputAdapter") -> None:
        self.adapters[adapter.name] = adapter

    def emit(self, viewer: str, event: InputEvent) -> None:
        adapter = self.adapters.get(viewer)
        if not adapter:
            return
        for command in adapter.translate(event):
            self.bus.dispatch(command)

    # Convenience helpers used in tests and future UI bindings
    def scroll(self, viewer: str, delta: int) -> None:
        self.emit(viewer, InputEvent("scroll", {"delta": delta}))

    def zoom(self, viewer: str, factor: float) -> None:
        self.emit(viewer, InputEvent("zoom", {"factor": factor}))

    def pan(self, viewer: str, dx: float, dy: float) -> None:
        self.emit(viewer, InputEvent("pan", {"dx": dx, "dy": dy}))

    def window_level(self, viewer: str, center: float, width: float) -> None:
        self.emit(viewer, InputEvent("window_level", {"center": center, "width": width}))

    def toggle_overlay(self, viewer: str, name: str) -> None:
        self.emit(viewer, InputEvent("toggle_overlay", {"name": name}))

    def drag_slice(self, viewer: str, slice_delta: int) -> None:
        self.emit(viewer, InputEvent("drag", {"sliceDelta": slice_delta}))

    def rebuild_mpr(self, viewer: str, plane: str) -> None:
        self.emit(viewer, InputEvent("rebuild_mpr", {"plane": plane}))

