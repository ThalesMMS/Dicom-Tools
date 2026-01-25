"""Viewer components that react to frame_ready events and render overlays."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from interface.input.event_bus import Event, EventBus
from interface.overlays.manager import OverlayManager
from interface.state.frames import Frame
from interface.state.ui_state import UIState


@dataclass
class BaseViewer:
    name: str
    state: UIState
    bus: EventBus
    overlays: OverlayManager
    current_frame: Optional[Frame] = None
    current_overlays: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.bus.subscribe("frame_ready", self._on_frame_ready)
        self.bus.subscribe("overlay_changed", self._on_overlay_changed)

    def _on_frame_ready(self, event: Event) -> None:
        payload = event.payload or {}
        frame: Frame = payload.get("frame")
        target_viewer = payload.get("viewer") or (frame.viewer if frame else None)
        if frame is None or target_viewer != self.name:
            return
        self.current_frame = frame
        meta = frame.metadata or {}
        self.current_overlays = self.overlays.render(self.state, self.name, meta)
        self.bus.emit(Event("viewer_updated", {"viewer": self.name, "overlays": self.current_overlays}))

    def _on_overlay_changed(self, event: Event) -> None:
        payload = event.payload or {}
        target_viewer = payload.get("viewer") or self.name
        if target_viewer != self.name:
            return
        meta = self.current_frame.metadata if self.current_frame else {}
        self.current_overlays = self.overlays.render(self.state, self.name, meta or {})
        self.bus.emit(Event("viewer_updated", {"viewer": self.name, "overlays": self.current_overlays}))


class TwoDViewer(BaseViewer):
    def __init__(self, state: UIState, bus: EventBus, overlays: OverlayManager) -> None:
        super().__init__("2d", state, bus, overlays)


class MPRViewer(BaseViewer):
    def __init__(self, state: UIState, bus: EventBus, overlays: OverlayManager) -> None:
        super().__init__("mpr", state, bus, overlays)


class VolumeViewer(BaseViewer):
    def __init__(self, state: UIState, bus: EventBus, overlays: OverlayManager) -> None:
        super().__init__("volume", state, bus, overlays)


class ViewerRegistry:
    """Keeps instances for each viewer so adapters can register easily."""

    def __init__(self, viewers: List[BaseViewer]) -> None:
        self.viewers = {viewer.name: viewer for viewer in viewers}

    def get(self, name: str) -> Optional[BaseViewer]:
        return self.viewers.get(name)

    def names(self) -> List[str]:
        return list(self.viewers.keys())
