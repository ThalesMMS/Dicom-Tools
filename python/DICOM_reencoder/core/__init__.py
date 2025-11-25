#
# __init__.py
# Dicom-Tools-py
#
# Centralizes imports for reusable core helpers shared across the toolkit.
#
# Thales Matheus Mendonça Santos - November 2025

"""Shared utilities for DICOM Tools.

This module centralizes reusable helpers so both the CLI and web layers
can rely on the same implementations.
"""

from .datasets import ensure_pixel_data, load_dataset, save_dataset
from .factories import (
    build_basic_text_sr,
    build_multiframe_dataset,
    build_nested_sequence_dataset,
    build_segmentation,
    build_secondary_capture,
    build_synthetic_series,
)
from .images import calculate_statistics, frame_to_png_bytes, get_frame, window_frame
from .metadata import summarize_metadata
from .network import VerificationServer, send_c_echo

# Re-export common helpers so callers can import from a single namespace
__all__ = [
    "ensure_pixel_data",
    "load_dataset",
    "save_dataset",
    "build_synthetic_series",
    "build_multiframe_dataset",
    "build_nested_sequence_dataset",
    "build_secondary_capture",
    "build_basic_text_sr",
    "calculate_statistics",
    "frame_to_png_bytes",
    "get_frame",
    "window_frame",
    "summarize_metadata",
    "VerificationServer",
    "send_c_echo",
]
