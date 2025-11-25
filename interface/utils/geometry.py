"""Small geometry helpers to keep viewer math testable and UI-agnostic."""

from __future__ import annotations

from typing import Iterable, Tuple

Matrix = Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]]
Point = Tuple[float, float]


def identity_matrix() -> Matrix:
    """Return a 3x3 identity matrix suitable for 2D transforms."""
    return ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def apply_translation(matrix: Matrix, dx: float, dy: float) -> Matrix:
    """Translate a matrix by (dx, dy)."""
    return (
        (matrix[0][0], matrix[0][1], matrix[0][2] + dx),
        (matrix[1][0], matrix[1][1], matrix[1][2] + dy),
        matrix[2],
    )


def apply_scale(matrix: Matrix, factor: float, origin: Point = (0.0, 0.0)) -> Matrix:
    """Scale a matrix around an origin."""
    ox, oy = origin
    # Translate to origin, scale, translate back
    translated = apply_translation(matrix, -ox, -oy)
    scaled = (
        (translated[0][0] * factor, translated[0][1] * factor, translated[0][2] * factor),
        (translated[1][0] * factor, translated[1][1] * factor, translated[1][2] * factor),
        translated[2],
    )
    return apply_translation(scaled, ox, oy)


def transform_point(matrix: Matrix, point: Point) -> Point:
    """Apply a 3x3 transform to a 2D point."""
    x, y = point
    nx = matrix[0][0] * x + matrix[0][1] * y + matrix[0][2]
    ny = matrix[1][0] * x + matrix[1][1] * y + matrix[1][2]
    return (nx, ny)


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def average(points: Iterable[Point]) -> Point:
    pts = list(points)
    if not pts:
        return (0.0, 0.0)
    sx = sum(p[0] for p in pts)
    sy = sum(p[1] for p in pts)
    return (sx / len(pts), sy / len(pts))

