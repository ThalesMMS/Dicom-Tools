from interface.overlays.manager import OverlayManager
from interface.state.ui_state import UIState


def test_overlay_manager_uses_metadata_and_window_level():
    state = UIState()
    viewer = state.get_viewer("2d")
    viewer.set_window_level(40, 400)
    manager = OverlayManager()

    overlays = manager.render(state, "2d", {"location_mm": 12.3, "slice_thickness": 1.5, "series_name": "Demo"})

    assert overlays["wl"] == "WL: 40 / WW: 400"
    assert overlays["location"] == "Loc: 12.3 mm"
    assert overlays["thickness"] == "Thick: 1.5 mm"
    assert overlays["series"] == "Demo"


def test_overlays_respect_enabled_flags():
    state = UIState()
    manager = OverlayManager()

    state.toggle_overlay("thickness")  # disable
    overlays = manager.render(state, "2d", {"slice_thickness": 2.0})
    assert "thickness" not in overlays

    state.toggle_overlay("thickness")  # enable again
    overlays_enabled = manager.render(state, "2d", {"slice_thickness": 2.0})
    assert overlays_enabled["thickness"].startswith("Thick:")


def test_series_overlay_prefers_frame_metadata():
    state = UIState()
    viewer = state.get_viewer("2d")
    viewer.series_uid = "1.2.3"
    manager = OverlayManager()

    fallback = manager.render(state, "2d", {})
    assert fallback["series"] == "1.2.3"

    overridden = manager.render(state, "2d", {"series_name": "MetaSeries"})
    assert overridden["series"] == "MetaSeries"


def test_overlays_change_with_slice_updates():
    state = UIState()
    manager = OverlayManager()
    viewer = state.get_viewer("2d")

    first = manager.render(state, "2d", {"location_mm": 0.0, "slice_thickness": 1.0})
    viewer.slice_index = 5
    second = manager.render(state, "2d", {"location_mm": 5.0, "slice_thickness": 1.0})

    assert first["location"] != second["location"]
    assert first["image_index"] == "Im 1/1"
    assert second["image_index"].startswith("Im 6/")
