"""Overlay primitives used by the viewers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from interface.state.ui_state import ViewerState


@dataclass
class OverlayContext:
    viewer: ViewerState
    frame_metadata: Optional[Dict[str, Any]] = None
    active_tool: str = ""


class Overlay:
    name: str

    def render(self, context: OverlayContext) -> Dict[str, str]:
        raise NotImplementedError

