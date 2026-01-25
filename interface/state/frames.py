"""Lightweight frame/request models used by the render loop."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from interface.state.ui_state import ROI

Point = Tuple[float, float]


@dataclass
class FrameRequest:
    viewer: str
    slice_index: int
    zoom: float
    pan: Point
    window_center: float
    window_width: float
    frame_count: int
    series_uid: Optional[str] = None
    plane: Optional[str] = None
    roi: Optional[ROI] = None
    reason: str = "user_input"


@dataclass
class Frame:
    viewer: str
    slice_index: int
    width: int
    height: int
    buffer: Optional[bytes] = None
    metadata: Optional[Dict[str, Any]] = None
    histogram: Optional[list[int]] = None

