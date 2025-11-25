from interface.runtime import InterfaceRuntime


def test_switch_active_viewer_preserves_series_and_overlays():
    runtime = InterfaceRuntime.create(type("DummyEngine", (), {"render": lambda self, req: None})())
    state = runtime.state
    viewer_2d = state.get_viewer("2d")
    viewer_2d.series_uid = "SERIES-1"
    state.toggle_overlay("wl")  # disable globally

    state.set_active_viewer("mpr")
    mpr = state.get_viewer("mpr")
    mpr.orientation = "sagittal"
    mpr.series_uid = viewer_2d.series_uid

    state.set_active_viewer("2d")
    assert state.active_viewer == "2d"
    assert "wl" not in state.overlays_enabled
    assert state.get_viewer("mpr").orientation == "sagittal"
    assert state.get_viewer("mpr").series_uid == "SERIES-1"


def test_frame_requests_target_correct_viewer():
    class Engine:
        def __init__(self) -> None:
            self.requests = []

        def render(self, request):
            self.requests.append(request)
            from interface.state.frames import Frame

            return Frame(viewer=request.viewer, slice_index=request.slice_index, width=16, height=16)

    engine = Engine()
    runtime = InterfaceRuntime.create(engine)
    runtime.inputs.scroll("2d", 1)
    runtime.inputs.scroll("mpr", 2)
    viewers = [r.viewer for r in engine.requests]
    assert "2d" in viewers
    assert "mpr" in viewers
