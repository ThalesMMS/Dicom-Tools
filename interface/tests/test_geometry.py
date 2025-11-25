from interface.utils.geometry import apply_scale, apply_translation, identity_matrix, transform_point


def test_apply_translation_moves_point():
    mat = identity_matrix()
    translated = apply_translation(mat, 2.0, -3.0)
    assert transform_point(translated, (0.0, 0.0)) == (2.0, -3.0)


def test_apply_scale_around_origin():
    mat = identity_matrix()
    scaled = apply_scale(mat, 2.0, origin=(1.0, 1.0))
    assert transform_point(scaled, (1.0, 1.0)) == (1.0, 1.0)
    assert transform_point(scaled, (2.0, 2.0)) == (3.0, 3.0)
