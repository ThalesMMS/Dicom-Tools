"""Composition root for the interface layer."""

from __future__ import annotations

from dataclasses import dataclass

from interface.components import RenderLoop, ViewerRegistry
from interface.components.viewers import MPRViewer, TwoDViewer, VolumeViewer
from interface.input import InputController, MPRInputAdapter, TwoDInputAdapter, VolumeInputAdapter
from interface.input.tools import ToolManager
from interface.input.event_bus import EventBus
from interface.overlays import OverlayManager
from interface.state.ui_state import UIState


@dataclass
class InterfaceRuntime:
    state: UIState
    bus: EventBus
    overlays: OverlayManager
    tools: ToolManager
    inputs: InputController
    viewers: ViewerRegistry
    render_loop: RenderLoop

    @classmethod
    def create(cls, engine) -> "InterfaceRuntime":
        state = UIState()
        bus = EventBus()
        overlays = OverlayManager()
        tools = ToolManager(state)
        tools.bind_to(bus)
        inputs = InputController(bus, [TwoDInputAdapter(), MPRInputAdapter(), VolumeInputAdapter()])
        viewers = ViewerRegistry([TwoDViewer(state, bus, overlays), MPRViewer(state, bus, overlays), VolumeViewer(state, bus, overlays)])
        render_loop = RenderLoop(bus, engine)
        return cls(state, bus, overlays, tools, inputs, viewers, render_loop)

