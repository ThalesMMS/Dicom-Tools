#
# cli.py
# Dicom-Tools-py
#
# Supplies the unified command-line entry point that wires high-level DICOM utilities to subcommands.
#
# Thales Matheus Mendonça Santos - November 2025

"""Unified CLI front-end for DICOM Tools."""

import argparse
import json
from pathlib import Path

import numpy as np

from . import web_interface
from .anonymize_dicom import anonymize_dicom
from .core import calculate_statistics, frame_to_png_bytes, load_dataset, save_dataset, summarize_metadata
from .core.network import send_c_echo


def cmd_summary(args: argparse.Namespace) -> None:
    dataset = load_dataset(args.file)
    summary = summarize_metadata(dataset)
    if args.json:
        print(json.dumps(summary, indent=2))
        return

    # Keep the human-readable output compact so it fits nicely in terminals
    print("Patient  ", summary["patient"])
    print("Study    ", summary["study"])
    print("Series   ", summary["series"])
    print("Image    ", summary["image"])


def cmd_stats(args: argparse.Namespace) -> None:
    dataset = load_dataset(args.file)
    stats = calculate_statistics(dataset.pixel_array if dataset.pixel_array.ndim == 2 else dataset.pixel_array[0])
    # Sorted keys provide deterministic ordering between runs
    for key in sorted(stats.keys()):
        print(f"{key:>12}: {stats[key]}")


def cmd_png(args: argparse.Namespace) -> None:
    dataset = load_dataset(args.file)
    png_bytes = frame_to_png_bytes(dataset, frame_index=args.frame)
    png_bytes.seek(0)
    output = Path(args.output or f"{Path(args.file).stem}.png")
    output.write_bytes(png_bytes.read())
    print(f"Saved {output}")


def cmd_anonymize(args: argparse.Namespace) -> None:
    inferred_output = args.output or str(Path(args.file).with_name(f"{Path(args.file).stem}_anonymized{Path(args.file).suffix}"))
    anonymize_dicom(args.file, args.output)
    print(f"Anonymized file written to {inferred_output}")


def cmd_echo(args: argparse.Namespace) -> None:
    status = send_c_echo(args.host, args.port)
    print(f"C-ECHO status: 0x{status:04x}")


def cmd_web(args: argparse.Namespace) -> None:
    web_interface.app.run(host=args.host, port=args.port, debug=args.debug)


def cmd_volume(args: argparse.Namespace) -> None:
    from .volume_builder import build_volume

    directory = Path(args.directory)
    volume, _, metadata = build_volume(directory)

    if args.preview:
        print(json.dumps(metadata, indent=2))
        return

    output_path = Path(args.output) if args.output else Path("output") / f"{directory.name}_volume.npy"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, volume)

    meta_path = Path(args.metadata) if args.metadata else output_path.with_suffix(".json")
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Volume saved to {output_path} (shape={metadata['shape']}, dtype={metadata['dtype']})")
    print(f"Metadata written to {meta_path}")


def cmd_nifti(args: argparse.Namespace) -> None:
    from .series_to_nifti import convert_series_to_nifti

    output_path, meta = convert_series_to_nifti(
        Path(args.directory),
        series_uid=args.series_uid,
        output=args.output,
        compress=not args.no_compress,
        metadata_path=args.metadata,
    )
    print(f"NIfTI saved to {output_path}")
    print(json.dumps(meta, indent=2))


def cmd_transcode(args: argparse.Namespace) -> None:
    from .transcode_dicom import transcode

    output_path = transcode(Path(args.file), output=Path(args.output) if args.output else None, syntax=args.syntax)
    print(f"Transcoded DICOM written to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="dicom-tools", description="Multi-tool CLI for DICOM utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    summary = sub.add_parser("summary", help="Print condensed DICOM metadata")
    summary.add_argument("file", help="Path to a DICOM file")
    summary.add_argument("--json", action="store_true", help="Emit JSON metadata")
    summary.set_defaults(func=cmd_summary)

    stats = sub.add_parser("stats", help="Compute pixel statistics for a DICOM file")
    stats.add_argument("file")
    stats.set_defaults(func=cmd_stats)

    png = sub.add_parser("png", help="Export a frame to PNG")
    png.add_argument("file")
    png.add_argument("--frame", type=int, default=0, help="Frame index for multi-frame datasets")
    png.add_argument("-o", "--output", help="Output PNG path")
    png.set_defaults(func=cmd_png)

    anonymize = sub.add_parser("anonymize", help="Anonymize a DICOM file")
    anonymize.add_argument("file")
    anonymize.add_argument("-o", "--output", help="Output path")
    anonymize.set_defaults(func=cmd_anonymize)

    echo = sub.add_parser("echo", help="Send a C-ECHO to a remote host")
    echo.add_argument("host", nargs="?", default="127.0.0.1")
    echo.add_argument("--port", type=int, default=11112)
    echo.set_defaults(func=cmd_echo)

    web = sub.add_parser("web", help="Launch the web interface")
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", type=int, default=5000)
    web.add_argument("--debug", action="store_true")
    web.set_defaults(func=cmd_web)

    volume = sub.add_parser("volume", help="Build a 3D volume from a DICOM directory")
    volume.add_argument("directory", help="Directory containing DICOM slices")
    volume.add_argument("-o", "--output", help="Output .npy path (default: output/<dir>_volume.npy)")
    volume.add_argument("--metadata", help="Optional metadata JSON path (default: alongside .npy)")
    volume.add_argument("--preview", action="store_true", help="Only print metadata without writing files")
    volume.set_defaults(func=cmd_volume)

    nifti = sub.add_parser("nifti", help="Export a DICOM series to NIfTI using SimpleITK")
    nifti.add_argument("directory", help="Directory containing the DICOM series")
    nifti.add_argument("-o", "--output", help="Output .nii/.nii.gz path")
    nifti.add_argument("--series-uid", help="SeriesInstanceUID to export when multiple series exist")
    nifti.add_argument("--no-compress", action="store_true", help="Disable gzip compression")
    nifti.add_argument("--metadata", help="Optional metadata JSON path")
    nifti.set_defaults(func=cmd_nifti)

    transcode = sub.add_parser("transcode", help="Transcode a DICOM file to a different transfer syntax using GDCM")
    transcode.add_argument("file", help="Input DICOM file")
    transcode.add_argument("-o", "--output", help="Output file (default: <stem>_<syntax>.dcm)")
    transcode.add_argument("--syntax", default="explicit",
                           help="Target syntax: explicit, implicit, deflated, jpeg-lossless, jpeg2000-lossless, rle")
    transcode.set_defaults(func=cmd_transcode)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
