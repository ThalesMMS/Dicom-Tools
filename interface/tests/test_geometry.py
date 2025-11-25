from interface.utils.geometry import apply_scale, apply_translation, bounding_box, clip_roi, identity_matrix, transform_point


def test_apply_translation_moves_point():
    mat = identity_matrix()
    translated = apply_translation(mat, 2.0, -3.0)
    assert transform_point(translated, (0.0, 0.0)) == (2.0, -3.0)


def test_apply_scale_around_origin():
    mat = identity_matrix()
    scaled = apply_scale(mat, 2.0, origin=(1.0, 1.0))
    assert transform_point(scaled, (1.0, 1.0)) == (1.0, 1.0)
    assert transform_point(scaled, (2.0, 2.0)) == (3.0, 3.0)


def test_bounding_box_and_clip_roi():
    points = [(0, 0), (2, 3), (1, -1)]
    bb = bounding_box(points)
    assert bb == ((0, -1), (2, 3))

    roi = ((-5, -2), (6, 7))
    clipped = clip_roi(roi, width=4, height=4)
    assert clipped == ((0.0, 0.0), (4.0, 4.0))


def test_average_and_clamp_edge_cases():
    from interface.utils.geometry import average, clamp

    assert average([]) == (0.0, 0.0)
    assert average([(1, 2), (3, 4)]) == (2.0, 3.0)
    assert clamp(5, 0, 3) == 3
    assert clamp(-1, 0, 3) == 0
