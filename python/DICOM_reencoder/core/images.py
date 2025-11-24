#
# images.py
# Dicom-Tools-py
#
# Processes DICOM pixel arrays for windowing, statistics, and PNG generation.
#
# Thales Matheus Mendonça Santos - November 2025

"""Pixel-data helpers shared by the CLI, web API, and tests."""

from io import BytesIO
from typing import Optional

import numpy as np
from PIL import Image
import pydicom
from pydicom.dataset import Dataset


def get_frame(dataset: Dataset, frame_index: int = 0) -> np.ndarray:
    """Return a single frame from a dataset, handling multi-frame safely."""
    pixels = dataset.pixel_array
    if pixels.ndim > 2:
        if frame_index >= pixels.shape[0]:
            raise IndexError(f"Frame {frame_index} out of range for {pixels.shape[0]} frames")
        # Multi-frame datasets store frames along the first axis; slice out the requested one
        return np.asarray(pixels[frame_index])
    return np.asarray(pixels)


def calculate_statistics(pixel_array: np.ndarray) -> dict:
    """Compute descriptive statistics for a pixel array."""
    flat_pixels = np.asarray(pixel_array).flatten()

    stats = {
        "min": int(np.min(flat_pixels)),
        "max": int(np.max(flat_pixels)),
        "mean": float(np.mean(flat_pixels)),
        "median": float(np.median(flat_pixels)),
        "std": float(np.std(flat_pixels)),
        "variance": float(np.var(flat_pixels)),
        "p1": float(np.percentile(flat_pixels, 1)),
        "p5": float(np.percentile(flat_pixels, 5)),
        "p25": float(np.percentile(flat_pixels, 25)),
        "p75": float(np.percentile(flat_pixels, 75)),
        "p95": float(np.percentile(flat_pixels, 95)),
        "p99": float(np.percentile(flat_pixels, 99)),
        "total_pixels": int(len(flat_pixels)),
        "unique_values": int(len(np.unique(flat_pixels))),
        "zero_pixels": int(np.sum(flat_pixels == 0)),
    }

    stats["range"] = stats["max"] - stats["min"]
    stats["iqr"] = stats["p75"] - stats["p25"]
    # Guard against divide-by-zero when all pixels are zero
    stats["zero_percent"] = (stats["zero_pixels"] / max(stats["total_pixels"], 1)) * 100
    return stats


def _derive_window(dataset: Dataset, frame: np.ndarray) -> tuple[int, int]:
    """Determine window center/width using DICOM tags or histogram heuristics."""
    wc = dataset.get("WindowCenter")
    ww = dataset.get("WindowWidth")

    if wc is not None and ww is not None:
        if isinstance(wc, pydicom.multival.MultiValue):
            wc = float(wc[0])
        if isinstance(ww, pydicom.multival.MultiValue):
            ww = float(ww[0])
        return int(wc), int(max(1, ww))

    # Fallback: use robust percentiles
    center = float(np.median(frame))
    width = float(np.percentile(frame, 95) - np.percentile(frame, 5))
    width = width if width > 0 else float(np.max(frame) - np.min(frame) or 1)
    return int(center), int(width)


def window_frame(dataset: Dataset, frame_index: int = 0, *, window_center: Optional[int] = None,
                 window_width: Optional[int] = None) -> np.ndarray:
    """Apply windowing and return an 8-bit image suitable for PNG export."""
    frame = get_frame(dataset, frame_index)
    center, width = window_center, window_width
    if center is None or width is None:
        # If no manual window is supplied, derive one from tags or pixel statistics
        center, width = _derive_window(dataset, frame)

    img_min = center - width // 2
    img_max = center + width // 2
    windowed = np.clip(frame, img_min, img_max)
    scaled = ((windowed - img_min) / max(img_max - img_min, 1) * 255.0).astype(np.uint8)

    if dataset.get("PhotometricInterpretation") == "MONOCHROME1":
        # MONOCHROME1 stores darker pixels as higher values, so invert for display
        scaled = 255 - scaled

    return scaled


def frame_to_png_bytes(dataset: Dataset, frame_index: int = 0, *, window_center: Optional[int] = None,
                       window_width: Optional[int] = None) -> BytesIO:
    """Convert a DICOM frame into PNG bytes."""
    image = Image.fromarray(window_frame(dataset, frame_index, window_center=window_center, window_width=window_width))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
