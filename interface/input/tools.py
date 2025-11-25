"""Tool routing for UI commands (scroll, zoom, pan, WL, ROI...)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from interface.input.event_bus import Command, Event, EventBus
from interface.state.frames import FrameRequest
from interface.state.ui_state import UIState, ViewerState


def _build_frame_request(viewer: ViewerState, plane: Optional[str] = None, reason: str = "user_input") -> FrameRequest:
    return FrameRequest(
        viewer=viewer.name,
        slice_index=viewer.slice_index,
        zoom=viewer.zoom,
        pan=viewer.pan,
        window_center=viewer.window_center,
        window_width=viewer.window_width,
        frame_count=viewer.frame_count,
        series_uid=viewer.series_uid,
        plane=plane,
        roi=viewer.roi,
        reason=reason,
    )


@dataclass
class Tool:
    name: str
    handles: Iterable[str]

    def apply(self, command: Command, state: UIState) -> List[Event]:
        raise NotImplementedError


class ScrollTool(Tool):
    def __init__(self) -> None:
        super().__init__("scroll", {"onScroll", "onDrag"})

    def apply(self, command: Command, state: UIState) -> List[Event]:
        payload = command.payload or {}
        viewer = state.get_viewer(payload.get("viewer"))
        delta = int(payload.get("delta", 0))
        viewer.apply_scroll(delta)
        request = _build_frame_request(viewer, reason="scroll")
        return [
            Event("state_changed", {"viewer": viewer.name, "tool": self.name}),
            Event("frame_requested", {"request": request}),
        ]


class ZoomTool(Tool):
    def __init__(self) -> None:
        super().__init__("zoom", {"onZoom"})

    def apply(self, command: Command, state: UIState) -> List[Event]:
        payload = command.payload or {}
        viewer = state.get_viewer(payload.get("viewer"))
        factor = float(payload.get("factor", 1.0))
        viewer.apply_zoom(factor)
        request = _build_frame_request(viewer, reason="zoom")
        return [
            Event("state_changed", {"viewer": viewer.name, "tool": self.name}),
            Event("overlay_changed", {"viewer": viewer.name}),
            Event("frame_requested", {"request": request}),
        ]


class PanTool(Tool):
    def __init__(self) -> None:
        super().__init__("pan", {"onPan"})

    def apply(self, command: Command, state: UIState) -> List[Event]:
        payload = command.payload or {}
        viewer = state.get_viewer(payload.get("viewer"))
        dx = float(payload.get("dx", 0))
        dy = float(payload.get("dy", 0))
        viewer.apply_pan(dx, dy)
        request = _build_frame_request(viewer, reason="pan")
        return [
            Event("state_changed", {"viewer": viewer.name, "tool": self.name}),
            Event("frame_requested", {"request": request}),
        ]


class WindowLevelTool(Tool):
    def __init__(self) -> None:
        super().__init__("wl", {"onWindowLevel"})

    def apply(self, command: Command, state: UIState) -> List[Event]:
        payload = command.payload or {}
        viewer = state.get_viewer(payload.get("viewer"))
        center = float(payload.get("center", viewer.window_center))
        width = float(payload.get("width", viewer.window_width or 1.0))
        viewer.set_window_level(center, width)
        request = _build_frame_request(viewer, reason="window_level")
        return [
            Event("overlay_changed", {"viewer": viewer.name}),
            Event("frame_requested", {"request": request}),
        ]


class ROITool(Tool):
    def __init__(self) -> None:
        super().__init__("roi", {"onSelectROI"})

    def apply(self, command: Command, state: UIState) -> List[Event]:
        payload = command.payload or {}
        viewer = state.get_viewer(payload.get("viewer"))
        start = payload.get("start") or (0.0, 0.0)
        end = payload.get("end") or (0.0, 0.0)
        viewer.set_roi(tuple(start), tuple(end))  # type: ignore[arg-type]
        return [
            Event("overlay_changed", {"viewer": viewer.name}),
            Event("frame_requested", {"request": _build_frame_request(viewer, reason="roi")}),
        ]


class OverlayToggleTool(Tool):
    def __init__(self) -> None:
        super().__init__("overlay", {"onToggleOverlay"})

    def apply(self, command: Command, state: UIState) -> List[Event]:
        payload = command.payload or {}
        name = str(payload.get("name"))
        state.toggle_overlay(name)
        viewer_name = payload.get("viewer") or state.active_viewer
        return [Event("overlay_changed", {"viewer": viewer_name})]


class ChangeSeriesTool(Tool):
    def __init__(self) -> None:
        super().__init__("change_series", {"onChangeSeries"})

    def apply(self, command: Command, state: UIState) -> List[Event]:
        payload = command.payload or {}
        viewer = state.get_viewer(payload.get("viewer"))
        series_uid = payload.get("series_uid") or payload.get("series")
        if series_uid:
            viewer.series_uid = str(series_uid)
            viewer.slice_index = 0
        request = _build_frame_request(viewer, reason="change_series")
        return [
            Event("state_changed", {"viewer": viewer.name, "tool": self.name}),
            Event("frame_requested", {"request": request}),
        ]


class RebuildMPRTool(Tool):
    def __init__(self) -> None:
        super().__init__("mpr_rebuild", {"onRebuildMPR"})

    def apply(self, command: Command, state: UIState) -> List[Event]:
        payload = command.payload or {}
        viewer = state.get_viewer(payload.get("viewer"))
        plane = str(payload.get("plane", "axial"))
        request = _build_frame_request(viewer, plane=plane, reason="rebuild_mpr")
        return [Event("frame_requested", {"request": request})]


class ToolManager:
    """Registers command handlers and keeps a reference to UIState."""

    def __init__(self, state: UIState) -> None:
        tools: List[Tool] = [
            ScrollTool(),
            ZoomTool(),
            PanTool(),
            WindowLevelTool(),
            ROITool(),
            OverlayToggleTool(),
            ChangeSeriesTool(),
            RebuildMPRTool(),
        ]
        self.tools: Dict[str, Tool] = {tool.name: tool for tool in tools}
        self.command_index: Dict[str, Tool] = {}
        self.state = state
        for tool in tools:
            for handle in tool.handles:
                self.command_index[handle] = tool

    def bind_to(self, bus: EventBus) -> None:
        for command_name in self.command_index.keys():
            bus.register_command(command_name, self._dispatch)

    def _dispatch(self, command: Command):
        tool = self.command_index.get(command.name)
        if not tool:
            return None
        self.state.set_active_tool(tool.name)
        return tool.apply(command, self.state)

