"""Centralized overlay manager to keep UI layers consistent."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Iterable, List

from interface.overlays.base import Overlay, OverlayContext
from interface.state.ui_state import UIState


class WindowLevelOverlay(Overlay):
    name = "wl"

    def render(self, context: OverlayContext) -> Dict[str, str]:
        wl = context.viewer.window_center
        ww = context.viewer.window_width
        return {"wl": f"WL: {wl:.0f} / WW: {ww:.0f}"}


class ImageIndexOverlay(Overlay):
    name = "image_index"

    def render(self, context: OverlayContext) -> Dict[str, str]:
        current = context.viewer.slice_index + 1
        total = max(1, context.viewer.frame_count)
        return {"image_index": f"Im {current}/{total}"}


class LocationOverlay(Overlay):
    name = "location"

    def render(self, context: OverlayContext) -> Dict[str, str]:
        meta = context.frame_metadata or {}
        loc = meta.get("location_mm", 0.0)
        return {"location": f"Loc: {float(loc):.1f} mm"}


class ThicknessOverlay(Overlay):
    name = "thickness"

    def render(self, context: OverlayContext) -> Dict[str, str]:
        meta = context.frame_metadata or {}
        thick = meta.get("thickness_mm", meta.get("slice_thickness", 0.0))
        return {"thickness": f"Thick: {float(thick):.1f} mm"}


class TimestampOverlay(Overlay):
    name = "timestamp"

    def render(self, context: OverlayContext) -> Dict[str, str]:
        meta = context.frame_metadata or {}
        ts = meta.get("timestamp") or datetime.now(timezone.utc).isoformat(timespec="seconds")
        return {"timestamp": ts}


class SeriesOverlay(Overlay):
    name = "series"

    def render(self, context: OverlayContext) -> Dict[str, str]:
        meta = context.frame_metadata or {}
        series = meta.get("series_name") or context.viewer.series_uid or "Unknown"
        return {"series": str(series)}


class ToolOverlay(Overlay):
    name = "tool"

    def render(self, context: OverlayContext) -> Dict[str, str]:
        return {"tool": f"Tool: {context.active_tool}"}


class OrientationOverlay(Overlay):
    name = "orientation"

    def render(self, context: OverlayContext) -> Dict[str, str]:
        orientation = context.viewer.orientation or "L/R/A/P"
        return {"orientation": orientation}


DEFAULT_OVERLAYS: List[Overlay] = [
    WindowLevelOverlay(),
    ImageIndexOverlay(),
    LocationOverlay(),
    ThicknessOverlay(),
    TimestampOverlay(),
    SeriesOverlay(),
    ToolOverlay(),
    OrientationOverlay(),
]


class OverlayManager:
    def __init__(self, overlays: Iterable[Overlay] | None = None) -> None:
        self._overlays: Dict[str, Overlay] = {overlay.name: overlay for overlay in overlays or DEFAULT_OVERLAYS}

    def render(self, state: UIState, viewer_name: str, frame_metadata: Dict[str, object] | None = None) -> Dict[str, str]:
        enabled = state.overlays_enabled
        viewer = state.get_viewer(viewer_name)
        context = OverlayContext(viewer=viewer, frame_metadata=frame_metadata, active_tool=state.active_tool)
        result: Dict[str, str] = {}
        for name, overlay in self._overlays.items():
            if name not in enabled:
                continue
            result.update(overlay.render(context))
        return result

    def available(self) -> List[str]:
        return list(self._overlays.keys())
