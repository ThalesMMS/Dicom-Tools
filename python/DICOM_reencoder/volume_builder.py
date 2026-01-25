#!/usr/bin/env python3
#
# volume_builder.py
# Dicom-Tools-py
#
# Builds 3D numpy volumes and affine matrices from DICOM slices via dicom-numpy.
#
# Thales Matheus Mendonça Santos - November 2025

"""
Construct a 3D volume from a directory of DICOM slices using dicom-numpy.

Outputs a .npy volume (z, y, x) along with an optional JSON sidecar that
captures the affine transform, spacing, and basic statistics. This is useful
for quickly feeding DICOM datasets into research pipelines or sanity-checking
slice ordering.
"""

import argparse
import json
from pathlib import Path
from typing import Iterable, List, Tuple

import numpy as np
import pydicom


def _require_dicom_numpy():
    try:
        import dicom_numpy
    except ImportError as exc:  # noqa: BLE001
        raise SystemExit("dicom-numpy is required for dicom-volume. Install with: pip install dicom-numpy") from exc
    return dicom_numpy


def _load_sorted_datasets(dicom_dir: Path) -> List[pydicom.dataset.Dataset]:
    """Load datasets sorted by InstanceNumber (fallback to filename)."""
    files = sorted(
        [p for p in dicom_dir.rglob("*") if p.is_file() and p.suffix.lower() in {".dcm", ""}],
        key=lambda p: p.name,
    )
    if not files:
        raise RuntimeError(f"No DICOM files found in {dicom_dir}")

    datasets = []
    for path in files:
        try:
            ds = pydicom.dcmread(path, force=True)
            datasets.append(ds)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Failed to read {path}: {exc}") from exc

    # Sort slices using InstanceNumber to preserve correct anatomical order
    datasets.sort(key=lambda ds: getattr(ds, "InstanceNumber", 0))
    return datasets


def build_volume(dicom_dir: Path) -> Tuple[np.ndarray, np.ndarray, dict]:
    """
    Build a 3D numpy volume and affine matrix from a directory of DICOM slices.

    Returns:
        volume: 3D numpy array shaped (z, y, x).
        affine: 4x4 affine matrix describing voxel orientation and spacing.
        metadata: Dict with spacing, orientation, and summary statistics.
    """
    dicom_numpy = _require_dicom_numpy()
    datasets = _load_sorted_datasets(dicom_dir)

    try:
        volume, affine = dicom_numpy.combine_slices(datasets)
    except dicom_numpy.DicomImportException as exc:
        raise RuntimeError(f"Failed to combine slices: {exc}") from exc

    first = datasets[0]
    # Combine in-plane spacing with slice thickness to fully describe voxel size
    spacing = list(getattr(first, "PixelSpacing", [1.0, 1.0]))
    spacing.append(float(getattr(first, "SliceThickness", 1.0)))

    stats = {
        "min": float(volume.min()),
        "max": float(volume.max()),
        "mean": float(volume.mean()),
        "std": float(volume.std()),
    }

    metadata = {
        "shape": list(volume.shape),
        "dtype": str(volume.dtype),
        "affine": affine.tolist(),
        "spacing_mm": spacing,
        "series_uid": getattr(first, "SeriesInstanceUID", "N/A"),
        "study_uid": getattr(first, "StudyInstanceUID", "N/A"),
        "stats": stats,
    }

    return volume, affine, metadata


def _default_output_paths(dicom_dir: Path, output: str | None) -> Tuple[Path, Path]:
    base_name = dicom_dir.name or "volume"
    npy_path = Path(output) if output else Path("output") / f"{base_name}_volume.npy"
    meta_path = npy_path.with_suffix(".json")
    npy_path.parent.mkdir(parents=True, exist_ok=True)
    return npy_path, meta_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a 3D volume from a DICOM folder using dicom-numpy")
    parser.add_argument("directory", help="Path to directory containing DICOM slices")
    parser.add_argument("-o", "--output", help="Output .npy path (default: output/<dir>_volume.npy)")
    parser.add_argument("--metadata", help="Optional path to write JSON metadata (default: alongside .npy)")
    parser.add_argument("--preview", action="store_true", help="Print metadata without writing files")
    args = parser.parse_args()

    volume, affine, metadata = build_volume(Path(args.directory))

    if args.preview:
        print(json.dumps(metadata, indent=2))
        return

    npy_path, default_meta = _default_output_paths(Path(args.directory), args.output)
    meta_path = Path(args.metadata) if args.metadata else default_meta

    np.save(npy_path, volume)
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Volume saved to {npy_path} with shape {metadata['shape']} and dtype {metadata['dtype']}")
    print(f"Metadata written to {meta_path}")


if __name__ == "__main__":
    main()
