#!/usr/bin/env python3
#
# batch_process.py
# Dicom-Tools-py
#
# Offers batch operations for DICOM directories, including listing, decompression, anonymization, conversion, and validation.
#
# Thales Matheus Mendonça Santos - November 2025

"""
Batch process DICOM files in a directory.
This script allows applying various operations to multiple DICOM files at once,
including decompression, anonymization, conversion, and validation.
"""

import pydicom
import sys
import os
import glob
from pathlib import Path
import argparse

def find_dicom_files(directory, recursive=False):
    """
    Find all DICOM files in a directory.

    Args:
        directory: Directory to search
        recursive: Search recursively in subdirectories

    Returns:
        List of DICOM file paths
    """
    dicom_files = []
    patterns = ['*.dcm', '*.DCM', '*.dicom', '*.DICOM']

    if recursive:
        for pattern in patterns:
            dicom_files.extend(glob.glob(os.path.join(directory, '**', pattern), recursive=True))
    else:
        for pattern in patterns:
            dicom_files.extend(glob.glob(os.path.join(directory, pattern)))

    # Also check files without extension
    if not recursive:
        for file_path in glob.glob(os.path.join(directory, '*')):
            if os.path.isfile(file_path) and not any(file_path.endswith(ext) for ext in ['.dcm', '.DCM', '.dicom', '.DICOM']):
                try:
                    # Try to read as DICOM using header only; avoids loading large pixel data accidentally
                    pydicom.dcmread(file_path, stop_before_pixels=True, force=True)
                    dicom_files.append(file_path)
                except:
                    pass

    return sorted(set(dicom_files))

def decompress_batch(files, output_dir=None):
    """Decompress multiple DICOM files."""
    from pydicom.uid import ExplicitVRLittleEndian

    print(f"\nDecompressing {len(files)} files...")
    print(f"{'='*80}\n")

    success_count = 0
    error_count = 0

    for i, file_path in enumerate(files, 1):
        try:
            print(f"[{i}/{len(files)}] Processing: {os.path.basename(file_path)}")

            dataset = pydicom.dcmread(file_path, force=True)

            # Determine output path
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                base_name = os.path.basename(file_path)
                name, ext = os.path.splitext(base_name)
                output_path = os.path.join(output_dir, f"{name}_decompressed{ext}")
            else:
                dir_name = os.path.dirname(file_path)
                base_name = os.path.basename(file_path)
                name, ext = os.path.splitext(base_name)
                output_path = os.path.join(dir_name, f"{name}_decompressed{ext}")

            # Decompress if needed
            if dataset.file_meta.TransferSyntaxUID.is_compressed:
                dataset.decompress()
                dataset.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
                dataset.save_as(output_path)
                print(f"  ✓ Decompressed -> {output_path}")
                success_count += 1
            else:
                print(f"  ⊘ Already uncompressed, skipping")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            error_count += 1

    print(f"\n{'='*80}")
    print(f"Decompression complete: {success_count} successful, {error_count} errors")
    print(f"{'='*80}\n")

def anonymize_batch(files, output_dir=None):
    """Anonymize multiple DICOM files."""
    # Import the anonymization function
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from anonymize_dicom import anonymize_dicom

    print(f"\nAnonymizing {len(files)} files...")
    print(f"{'='*80}\n")

    success_count = 0
    error_count = 0

    for i, file_path in enumerate(files, 1):
        try:
            print(f"[{i}/{len(files)}] Processing: {os.path.basename(file_path)}")

            # Determine output path
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                base_name = os.path.basename(file_path)
                name, ext = os.path.splitext(base_name)
                output_path = os.path.join(output_dir, f"{name}_anonymized{ext}")
            else:
                output_path = None

            result = anonymize_dicom(file_path, output_path)
            if result:
                success_count += 1
            else:
                error_count += 1

        except Exception as e:
            print(f"  ✗ Error: {e}")
            error_count += 1

    print(f"\n{'='*80}")
    print(f"Anonymization complete: {success_count} successful, {error_count} errors")
    print(f"{'='*80}\n")

def convert_batch(files, output_dir=None, output_format='png'):
    """Convert multiple DICOM files to images."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from convert_to_image import convert_dicom_to_image

    print(f"\nConverting {len(files)} files to {output_format.upper()}...")
    print(f"{'='*80}\n")

    success_count = 0
    error_count = 0

    for i, file_path in enumerate(files, 1):
        try:
            print(f"[{i}/{len(files)}] Processing: {os.path.basename(file_path)}")

            # Determine output path
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                base_name = os.path.basename(file_path)
                name, ext = os.path.splitext(base_name)
                output_path = os.path.join(output_dir, f"{name}.{output_format}")
            else:
                output_path = None

            result = convert_dicom_to_image(file_path, output_path, output_format)
            if result:
                success_count += 1
            else:
                error_count += 1

        except Exception as e:
            print(f"  ✗ Error: {e}")
            error_count += 1

    print(f"\n{'='*80}")
    print(f"Conversion complete: {success_count} successful, {error_count} errors")
    print(f"{'='*80}\n")

def validate_batch(files):
    """Validate multiple DICOM files."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from validate_dicom import DicomValidator

    print(f"\nValidating {len(files)} files...")
    print(f"{'='*80}\n")

    valid_count = 0
    invalid_count = 0
    validator = DicomValidator()

    for i, file_path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] Validating: {os.path.basename(file_path)}")

        is_valid = validator.validate_file(file_path)
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1

    print(f"\n{'='*80}")
    print(f"Validation complete: {valid_count} valid, {invalid_count} invalid")
    print(f"{'='*80}\n")

def list_files(files):
    """List DICOM files with basic information."""
    print(f"\nFound {len(files)} DICOM files:")
    print(f"{'='*80}\n")

    total_size = 0

    for i, file_path in enumerate(files, 1):
        try:
            dataset = pydicom.dcmread(file_path, stop_before_pixels=True, force=True)
            file_size = os.path.getsize(file_path)
            total_size += file_size

            modality = dataset.get('Modality', 'N/A')
            patient_id = dataset.get('PatientID', 'N/A')
            study_date = dataset.get('StudyDate', 'N/A')

            print(f"[{i:3d}] {os.path.basename(file_path)}")
            print(f"      Size: {file_size:,} bytes | Modality: {modality} | "
                  f"Patient: {patient_id} | Date: {study_date}")

        except Exception as e:
            print(f"[{i:3d}] {os.path.basename(file_path)} - Error: {e}")

    print(f"\n{'='*80}")
    print(f"Total: {len(files)} files, {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
    print(f"{'='*80}\n")

def main():
    parser = argparse.ArgumentParser(
        description='Batch process DICOM files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s -d /path/to/dicoms -o list
  %(prog)s -d /path/to/dicoms -o decompress --output-dir ./decompressed
  %(prog)s -d /path/to/dicoms -o anonymize -r
  %(prog)s -d /path/to/dicoms -o convert --format png
  %(prog)s -d /path/to/dicoms -o validate
        '''
    )

    parser.add_argument('-d', '--directory', default='.',
                        help='Directory containing DICOM files (default: current directory)')
    parser.add_argument('-o', '--operation', required=True,
                        choices=['list', 'decompress', 'anonymize', 'convert', 'validate'],
                        help='Operation to perform')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='Search for DICOM files recursively')
    parser.add_argument('--output-dir', help='Output directory for processed files')
    parser.add_argument('--format', default='png', choices=['png', 'jpeg'],
                        help='Output format for image conversion (default: png)')

    args = parser.parse_args()

    # Find DICOM files
    print(f"Searching for DICOM files in: {args.directory}")
    if args.recursive:
        print("  (recursive search enabled)")

    files = find_dicom_files(args.directory, args.recursive)

    if not files:
        print("No DICOM files found.")
        return 1

    # Perform operation
    if args.operation == 'list':
        list_files(files)
    elif args.operation == 'decompress':
        decompress_batch(files, args.output_dir)
    elif args.operation == 'anonymize':
        anonymize_batch(files, args.output_dir)
    elif args.operation == 'convert':
        convert_batch(files, args.output_dir, args.format)
    elif args.operation == 'validate':
        validate_batch(files)

    return 0

if __name__ == "__main__":
    sys.exit(main())
