#!/usr/bin/env python3
#
# series_to_nifti.py
# Dicom-Tools-py
#
# Converts a DICOM series directory into a NIfTI volume using SimpleITK.
#
# Thales Matheus Mendonça Santos - November 2025

"""
Convert a DICOM series into a NIfTI volume using SimpleITK.

This leverages SimpleITK's series reader to honor spacing, orientation, and
instance sorting. It is intentionally minimal so it can run as a quick bridge
between DICOM folders and research tooling that expects NIfTI.
"""

import argparse
import json
from pathlib import Path
from typing import Iterable, Tuple


def _require_simpleitk():
    try:
        import SimpleITK as sitk
    except ImportError as exc:  # noqa: BLE001
        raise SystemExit("SimpleITK is required for dicom-to-nifti. Install with: pip install SimpleITK") from exc
    return sitk


def _normalize_output_path(base_dir: Path, output: str | None, series_uid: str) -> Path:
    """Choose a sensible .nii.gz output path."""
    if output:
        out_path = Path(output)
    else:
        out_path = base_dir / f"{series_uid}.nii.gz"

    suffixes = "".join(out_path.suffixes)
    if suffixes not in {".nii", ".nii.gz"}:
        out_path = out_path.with_suffix(".nii.gz")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    return out_path


def convert_series_to_nifti(series_dir: Path, *, series_uid: str | None = None, output: str | None = None,
                            compress: bool = True, metadata_path: str | None = None) -> Tuple[Path, dict]:
    """
    Convert a directory containing a DICOM series into a NIfTI file.

    Args:
        series_dir: Directory containing a single or multiple DICOM series.
        series_uid: Optional SeriesInstanceUID to select when multiple exist.
        output: Output file path (.nii or .nii.gz). Defaults to <SeriesUID>.nii.gz.
        compress: Whether to write compressed NIfTI (.nii.gz).
        metadata_path: Optional path to write a JSON sidecar with spacing/origin/direction.
    """
    sitk = _require_simpleitk()
    series_dir = Path(series_dir)

    reader = sitk.ImageSeriesReader()
    series_ids: Iterable[str] = reader.GetGDCMSeriesIDs(str(series_dir)) or []
    series_ids = list(series_ids)
    if not series_ids:
        raise RuntimeError(f"No DICOM series found in {series_dir}")

    target_uid = series_uid or series_ids[0]
    if target_uid not in series_ids:
        found = ", ".join(series_ids)
        raise RuntimeError(f"Series UID {target_uid} not found in {series_dir}. Available: {found}")

    # Let SimpleITK decide ordering to honor slice spacing/orientation
    file_names = reader.GetGDCMSeriesFileNames(str(series_dir), target_uid)
    reader.SetFileNames(file_names)
    image = reader.Execute()

    output_path = _normalize_output_path(series_dir, output, target_uid)
    sitk.WriteImage(image, str(output_path), useCompression=compress)

    meta = {
        "series_uid": target_uid,
        "files": list(file_names),
        "size": list(image.GetSize()),
        "spacing": list(image.GetSpacing()),
        "origin": list(image.GetOrigin()),
        "direction": list(image.GetDirection()),
        "output": str(output_path),
        "compress": bool(compress),
    }

    if metadata_path:
        Path(metadata_path).parent.mkdir(parents=True, exist_ok=True)
        Path(metadata_path).write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return output_path, meta


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a DICOM series directory to NIfTI using SimpleITK")
    parser.add_argument("directory", help="Directory containing the DICOM series")
    parser.add_argument("-o", "--output", help="Output NIfTI path (.nii or .nii.gz)")
    parser.add_argument("--series-uid", help="Specific SeriesInstanceUID to export (if multiple series exist)")
    parser.add_argument("--no-compress", action="store_true", help="Disable gzip compression for output NIfTI")
    parser.add_argument("--metadata", help="Optional path to write JSON metadata about the export")
    args = parser.parse_args()

    try:
        output_path, meta = convert_series_to_nifti(
            Path(args.directory),
            series_uid=args.series_uid,
            output=args.output,
            compress=not args.no_compress,
            metadata_path=args.metadata,
        )
        print(f"NIfTI written to {output_path}")
        print(json.dumps(meta, indent=2))
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Conversion failed: {exc}") from exc


if __name__ == "__main__":
    main()
