#!/usr/bin/env python3
#
# transcode_dicom.py
# Dicom-Tools-py
#
# Transcodes DICOM transfer syntaxes using GDCM for compatibility conversions.
#
# Thales Matheus Mendonça Santos - November 2025

"""
Transcode DICOM files between transfer syntaxes using GDCM.

This is primarily useful for turning compressed datasets into Explicit VR
Little Endian (or other syntaxes) that downstream tools handle more reliably.
"""

import argparse
from pathlib import Path


def _require_gdcm():
    try:
        import gdcm
    except ImportError as exc:  # noqa: BLE001
        raise SystemExit("GDCM is required for dicom-transcode. Install with: pip install gdcm") from exc
    return gdcm


def _transfer_syntax(gdcm, name: str):
    name = name.lower()
    # Map friendly names to gdcm.TransferSyntax constants
    mapping = {
        "explicit": gdcm.TransferSyntax(gdcm.TransferSyntax.ExplicitVRLittleEndian),
        "implicit": gdcm.TransferSyntax(gdcm.TransferSyntax.ImplicitVRLittleEndian),
        "deflated": gdcm.TransferSyntax(gdcm.TransferSyntax.DeflatedExplicitVRLittleEndian),
        "jpeg-lossless": gdcm.TransferSyntax(gdcm.TransferSyntax.JPEGLosslessProcess14_1),
        "jpeg2000-lossless": gdcm.TransferSyntax(gdcm.TransferSyntax.JPEG2000Lossless),
        "rle": gdcm.TransferSyntax(gdcm.TransferSyntax.RLELossless),
    }
    if name not in mapping:
        options = ", ".join(mapping.keys())
        raise SystemExit(f"Unsupported syntax '{name}'. Choose one of: {options}")
    return mapping[name]


def transcode(input_path: Path, *, output: Path | None = None, syntax: str = "explicit") -> Path:
    gdcm = _require_gdcm()
    ts = _transfer_syntax(gdcm, syntax)

    reader = gdcm.ImageReader()
    reader.SetFileName(str(input_path))
    if not reader.Read():
        raise RuntimeError(f"Could not read DICOM file: {input_path}")

    changer = gdcm.ImageChangeTransferSyntax()
    changer.SetTransferSyntax(ts)
    changer.SetInput(reader.GetImage())
    if not changer.Change():
        raise RuntimeError(f"Failed to transcode {input_path} to {syntax}")

    # Default output adds the target syntax to the filename to avoid overwriting the source
    output_path = output or input_path.with_name(f"{input_path.stem}_{syntax}.dcm")
    writer = gdcm.ImageWriter()
    writer.SetFile(reader.GetFile())
    writer.SetFileName(str(output_path))
    writer.SetImage(changer.GetOutput())

    if not writer.Write():
        raise RuntimeError(f"Failed to write output file: {output_path}")

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcode DICOM transfer syntax using GDCM")
    parser.add_argument("input", help="Input DICOM file")
    parser.add_argument("-o", "--output", help="Output DICOM file (default: <name>_<syntax>.dcm)")
    parser.add_argument("--syntax", default="explicit",
                        help="Target syntax: explicit, implicit, deflated, jpeg-lossless, jpeg2000-lossless, rle")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else None

    try:
        result = transcode(input_path, output=output_path, syntax=args.syntax)
        print(f"Transcoded file written to: {result}")
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Transcode failed: {exc}") from exc


if __name__ == "__main__":
    main()
