"""Stateful objects used by the interface without tying them to any widget toolkit."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Set, Tuple

from interface.utils.geometry import (
    Matrix,
    apply_scale,
    apply_translation,
    clamp,
    identity_matrix,
)

Point = Tuple[float, float]
ROI = Tuple[Point, Point]


DEFAULT_OVERLAYS: Set[str] = {
    "wl",
    "image_index",
    "location",
    "thickness",
    "timestamp",
    "series",
    "tool",
    "orientation",
}


@dataclass
class ViewerState:
    """Keeps the numeric state for a single viewer mode (2D, MPR, Volume)."""

    name: str
    slice_index: int = 0
    frame_count: int = 1
    zoom: float = 1.0
    pan: Point = (0.0, 0.0)
    window_center: float = 0.0
    window_width: float = 0.0
    transform: Matrix = field(default_factory=identity_matrix)
    series_uid: Optional[str] = None
    orientation: Optional[str] = None
    roi: Optional[ROI] = None
    volume_rendering: bool = False

    def apply_scroll(self, delta: int) -> int:
        if self.frame_count > 1:
            self.slice_index = clamp(self.slice_index + int(delta), 0, max(0, self.frame_count - 1))
        else:
            self.slice_index = max(0, self.slice_index + int(delta))
        return int(self.slice_index)

    def apply_zoom(self, factor: float, origin: Point = (0.0, 0.0)) -> float:
        self.zoom = max(0.05, self.zoom * factor)
        self.transform = apply_scale(self.transform, factor, origin)
        return self.zoom

    def apply_pan(self, dx: float, dy: float) -> Point:
        self.pan = (self.pan[0] + dx, self.pan[1] + dy)
        self.transform = apply_translation(self.transform, dx, dy)
        return self.pan

    def set_window_level(self, center: float, width: float) -> Tuple[float, float]:
        self.window_center = center
        self.window_width = max(width, 1.0)
        return (self.window_center, self.window_width)

    def set_roi(self, start: Point, end: Point) -> ROI:
        self.roi = (start, end)
        return self.roi

    def set_frame_count(self, count: int) -> int:
        self.frame_count = max(1, int(count))
        self.slice_index = clamp(self.slice_index, 0, self.frame_count - 1)
        return self.frame_count


@dataclass
class UIState:
    """Aggregates all viewer states and overlay flags."""

    viewers: Dict[str, ViewerState] = field(default_factory=dict)
    active_viewer: str = "2d"
    active_tool: str = "scroll"
    overlays_enabled: Set[str] = field(default_factory=lambda: set(DEFAULT_OVERLAYS))

    def get_viewer(self, name: Optional[str] = None) -> ViewerState:
        viewer_name = name or self.active_viewer
        if viewer_name not in self.viewers:
            self.viewers[viewer_name] = ViewerState(viewer_name)
        return self.viewers[viewer_name]

    def set_active_viewer(self, name: str) -> ViewerState:
        self.active_viewer = name
        return self.get_viewer(name)

    def toggle_overlay(self, name: str) -> bool:
        if name in self.overlays_enabled:
            self.overlays_enabled.remove(name)
            return False
        self.overlays_enabled.add(name)
        return True

    def set_active_tool(self, name: str) -> str:
        self.active_tool = name
        return self.active_tool

    def snapshot(self) -> Dict[str, Dict[str, object]]:
        """Return a serializable snapshot used by tests/docs."""
        data: Dict[str, Dict[str, object]] = {}
        for name, viewer in self.viewers.items():
            data[name] = {
                "slice_index": viewer.slice_index,
                "frame_count": viewer.frame_count,
                "zoom": viewer.zoom,
                "pan": viewer.pan,
                "window_center": viewer.window_center,
                "window_width": viewer.window_width,
                "transform": viewer.transform,
                "series_uid": viewer.series_uid,
                "orientation": viewer.orientation,
                "roi": viewer.roi,
                "volume_rendering": viewer.volume_rendering,
            }
        return data
