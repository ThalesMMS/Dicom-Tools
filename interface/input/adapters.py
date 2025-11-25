"""Input adapters that normalize mouse/keyboard gestures into commands."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Set

from interface.input.event_bus import Command
from interface.input.controller import InputEvent


CANONICAL_COMMANDS: Dict[str, str] = {
    "scroll": "onScroll",
    "zoom": "onZoom",
    "pan": "onPan",
    "window_level": "onWindowLevel",
    "change_series": "onChangeSeries",
    "toggle_overlay": "onToggleOverlay",
    "select_roi": "onSelectROI",
    "drag": "onDrag",
    "rebuild_mpr": "onRebuildMPR",
}


@dataclass
class InputAdapter:
    name: str
    capabilities: Set[str] = field(default_factory=set)
    command_map: Dict[str, str] = field(default_factory=lambda: dict(CANONICAL_COMMANDS))

    def supports(self, kind: str) -> bool:
        return not self.capabilities or kind in self.capabilities

    def translate(self, event: InputEvent) -> List[Command]:
        """Translate a normalized InputEvent into one or more Commands."""
        if not self.supports(event.kind):
            return []
        command_name = self.command_map.get(event.kind)
        if not command_name:
            return []

        payload = dict(event.payload)
        payload["viewer"] = self.name

        # Dragging the mouse for slice navigation is treated as scroll
        if event.kind == "drag" and "sliceDelta" in payload and "delta" not in payload:
            payload["delta"] = payload.pop("sliceDelta")

        return [Command(command_name, payload)]


class TwoDInputAdapter(InputAdapter):
    def __init__(self, name: str = "2d") -> None:
        super().__init__(name=name, capabilities=set(CANONICAL_COMMANDS))


class MPRInputAdapter(InputAdapter):
    def __init__(self, name: str = "mpr") -> None:
        super().__init__(name=name, capabilities=set(CANONICAL_COMMANDS))


class VolumeInputAdapter(InputAdapter):
    def __init__(self, name: str = "volume") -> None:
        # Volume does not rebuild MPR planes but keeps all other interactions
        caps = set(CANONICAL_COMMANDS)
        caps.discard("rebuild_mpr")
        super().__init__(name=name, capabilities=caps)

