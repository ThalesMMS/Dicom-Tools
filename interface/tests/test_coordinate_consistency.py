from interface.utils.geometry import transform_point
from interface.state.ui_state import UIState


def test_viewers_share_coordinate_transforms():
    state = UIState()
    two_d = state.get_viewer("2d")
    mpr = state.get_viewer("mpr")

    two_d.apply_pan(10, -5)
    two_d.apply_zoom(2.0, origin=(0, 0))

    # Apply same operations to MPR and ensure transforms behave the same for a sample point
    mpr.apply_pan(10, -5)
    mpr.apply_zoom(2.0, origin=(0, 0))

    point = (1.0, 1.0)
    assert transform_point(two_d.transform, point) == transform_point(mpr.transform, point)
