#!/usr/bin/env python3
#
# organize_dicom.py
# Dicom-Tools-py
#
# Organizes DICOM files into directory hierarchies by patient, study, series, or modality.
#
# Thales Matheus Mendonça Santos - November 2025

"""
Organize DICOM files into a structured directory hierarchy.
This script organizes DICOM files by patient, study, series, or modality,
creating a logical folder structure for better file management.
"""

import pydicom
import sys
import os
import shutil
import glob
import argparse
from pathlib import Path

def sanitize_filename(name):
    """
    Sanitize a string to be used as a filename or directory name.

    Args:
        name: String to sanitize

    Returns:
        Sanitized string safe for filesystem use
    """
    if not name or str(name) == 'N/A':
        return 'Unknown'

    # Convert to string and remove leading/trailing whitespace
    name = str(name).strip()

    # Replace characters that are invalid in filenames
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')

    # Replace multiple spaces with single space
    name = ' '.join(name.split())

    # Limit length
    if len(name) > 100:
        name = name[:100]

    # Fall back to a predictable placeholder when nothing remains
    return name if name else 'Unknown'

def organize_by_patient(source_dir, dest_dir, copy_mode=False, recursive=False):
    """
    Organize DICOM files by patient.
    Structure: PatientName/PatientID/files.dcm
    """
    print(f"\nOrganizing by Patient...")
    print(f"Source: {source_dir}")
    print(f"Destination: {dest_dir}")
    print(f"Mode: {'Copy' if copy_mode else 'Move'}")
    print(f"{'='*80}\n")

    # Find all DICOM files
    pattern = '**/*.dcm' if recursive else '*.dcm'
    files = glob.glob(os.path.join(source_dir, pattern), recursive=recursive)

    organized_count = 0
    error_count = 0

    for file_path in files:
        try:
            # Skip reading heavy pixel buffers; we only need header tags to sort files
            dataset = pydicom.dcmread(file_path, stop_before_pixels=True, force=True)

            patient_name = sanitize_filename(dataset.get('PatientName', 'Unknown'))
            patient_id = sanitize_filename(dataset.get('PatientID', 'Unknown'))

            # Create directory structure
            patient_dir = os.path.join(dest_dir, patient_name, patient_id)
            os.makedirs(patient_dir, exist_ok=True)

            # Destination file path
            dest_file = os.path.join(patient_dir, os.path.basename(file_path))

            # Copy or move
            if copy_mode:
                shutil.copy2(file_path, dest_file)
            else:
                shutil.move(file_path, dest_file)

            print(f"  ✓ {os.path.basename(file_path)} -> {patient_name}/{patient_id}/")
            organized_count += 1

        except Exception as e:
            print(f"  ✗ Error processing {os.path.basename(file_path)}: {e}")
            error_count += 1

    print(f"\n{'='*80}")
    print(f"Organization complete: {organized_count} files organized, {error_count} errors")
    print(f"{'='*80}\n")

def organize_by_study(source_dir, dest_dir, copy_mode=False, recursive=False):
    """
    Organize DICOM files by study.
    Structure: PatientName/StudyDate_StudyDescription/files.dcm
    """
    print(f"\nOrganizing by Study...")
    print(f"Source: {source_dir}")
    print(f"Destination: {dest_dir}")
    print(f"Mode: {'Copy' if copy_mode else 'Move'}")
    print(f"{'='*80}\n")

    pattern = '**/*.dcm' if recursive else '*.dcm'
    files = glob.glob(os.path.join(source_dir, pattern), recursive=recursive)

    organized_count = 0
    error_count = 0

    for file_path in files:
        try:
            dataset = pydicom.dcmread(file_path, stop_before_pixels=True, force=True)

            patient_name = sanitize_filename(dataset.get('PatientName', 'Unknown'))
            study_date = sanitize_filename(dataset.get('StudyDate', 'Unknown'))
            study_desc = sanitize_filename(dataset.get('StudyDescription', 'Study'))

            # Build a date/description folder to keep related instances together
            study_folder = f"{study_date}_{study_desc}"
            study_dir = os.path.join(dest_dir, patient_name, study_folder)
            os.makedirs(study_dir, exist_ok=True)

            # Destination file path
            dest_file = os.path.join(study_dir, os.path.basename(file_path))

            # Copy or move
            if copy_mode:
                shutil.copy2(file_path, dest_file)
            else:
                shutil.move(file_path, dest_file)

            print(f"  ✓ {os.path.basename(file_path)} -> {patient_name}/{study_folder}/")
            organized_count += 1

        except Exception as e:
            print(f"  ✗ Error processing {os.path.basename(file_path)}: {e}")
            error_count += 1

    print(f"\n{'='*80}")
    print(f"Organization complete: {organized_count} files organized, {error_count} errors")
    print(f"{'='*80}\n")

def organize_by_series(source_dir, dest_dir, copy_mode=False, recursive=False):
    """
    Organize DICOM files by series.
    Structure: PatientName/StudyDate/SeriesNumber_SeriesDescription/files.dcm
    """
    print(f"\nOrganizing by Series...")
    print(f"Source: {source_dir}")
    print(f"Destination: {dest_dir}")
    print(f"Mode: {'Copy' if copy_mode else 'Move'}")
    print(f"{'='*80}\n")

    pattern = '**/*.dcm' if recursive else '*.dcm'
    files = glob.glob(os.path.join(source_dir, pattern), recursive=recursive)

    organized_count = 0
    error_count = 0

    for file_path in files:
        try:
            dataset = pydicom.dcmread(file_path, stop_before_pixels=True, force=True)

            patient_name = sanitize_filename(dataset.get('PatientName', 'Unknown'))
            study_date = sanitize_filename(dataset.get('StudyDate', 'Unknown'))
            series_num = sanitize_filename(dataset.get('SeriesNumber', '0'))
            series_desc = sanitize_filename(dataset.get('SeriesDescription', 'Series'))

            # Create directory structure
            series_folder = f"{series_num:0>3}_{series_desc}" if series_num.isdigit() else f"{series_num}_{series_desc}"
            series_dir = os.path.join(dest_dir, patient_name, study_date, series_folder)
            os.makedirs(series_dir, exist_ok=True)

            # Destination file path with instance number
            instance_num = dataset.get('InstanceNumber', '0')
            base_name = os.path.basename(file_path)
            name, ext = os.path.splitext(base_name)

            # Use the instance number when available so files sort in acquisition order
            if instance_num:
                dest_file = os.path.join(series_dir, f"{int(instance_num):04d}{ext}")
            else:
                dest_file = os.path.join(series_dir, base_name)

            # Avoid clobbering existing files by incrementing a suffix when needed
            counter = 1
            original_dest = dest_file
            while os.path.exists(dest_file):
                name_part, ext_part = os.path.splitext(original_dest)
                dest_file = f"{name_part}_{counter}{ext_part}"
                counter += 1

            # Copy or move
            if copy_mode:
                shutil.copy2(file_path, dest_file)
            else:
                shutil.move(file_path, dest_file)

            print(f"  ✓ {os.path.basename(file_path)} -> {patient_name}/{study_date}/{series_folder}/")
            organized_count += 1

        except Exception as e:
            print(f"  ✗ Error processing {os.path.basename(file_path)}: {e}")
            error_count += 1

    print(f"\n{'='*80}")
    print(f"Organization complete: {organized_count} files organized, {error_count} errors")
    print(f"{'='*80}\n")

def organize_by_modality(source_dir, dest_dir, copy_mode=False, recursive=False):
    """
    Organize DICOM files by modality.
    Structure: Modality/PatientName/files.dcm
    """
    print(f"\nOrganizing by Modality...")
    print(f"Source: {source_dir}")
    print(f"Destination: {dest_dir}")
    print(f"Mode: {'Copy' if copy_mode else 'Move'}")
    print(f"{'='*80}\n")

    pattern = '**/*.dcm' if recursive else '*.dcm'
    files = glob.glob(os.path.join(source_dir, pattern), recursive=recursive)

    organized_count = 0
    error_count = 0

    for file_path in files:
        try:
            dataset = pydicom.dcmread(file_path, stop_before_pixels=True, force=True)

            modality = sanitize_filename(dataset.get('Modality', 'Unknown'))
            patient_name = sanitize_filename(dataset.get('PatientName', 'Unknown'))

            # Create directory structure
            modality_dir = os.path.join(dest_dir, modality, patient_name)
            os.makedirs(modality_dir, exist_ok=True)

            # Destination file path
            dest_file = os.path.join(modality_dir, os.path.basename(file_path))

            # Copy or move
            if copy_mode:
                shutil.copy2(file_path, dest_file)
            else:
                shutil.move(file_path, dest_file)

            print(f"  ✓ {os.path.basename(file_path)} -> {modality}/{patient_name}/")
            organized_count += 1

        except Exception as e:
            print(f"  ✗ Error processing {os.path.basename(file_path)}: {e}")
            error_count += 1

    print(f"\n{'='*80}")
    print(f"Organization complete: {organized_count} files organized, {error_count} errors")
    print(f"{'='*80}\n")

def main():
    parser = argparse.ArgumentParser(
        description='Organize DICOM files into structured directories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Organization modes:
  patient  - PatientName/PatientID/
  study    - PatientName/StudyDate_StudyDescription/
  series   - PatientName/StudyDate/SeriesNumber_SeriesDescription/
  modality - Modality/PatientName/

Examples:
  # Organize by patient (move files)
  %(prog)s -s /source/dir -d /dest/dir -m patient

  # Organize by series (copy files, keep originals)
  %(prog)s -s /source/dir -d /dest/dir -m series --copy

  # Organize recursively
  %(prog)s -s /source/dir -d /dest/dir -m study -r
        '''
    )

    parser.add_argument('-s', '--source', required=True,
                        help='Source directory containing DICOM files')
    parser.add_argument('-d', '--destination', required=True,
                        help='Destination directory for organized files')
    parser.add_argument('-m', '--mode', required=True,
                        choices=['patient', 'study', 'series', 'modality'],
                        help='Organization mode')
    parser.add_argument('-c', '--copy', action='store_true',
                        help='Copy files instead of moving them')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='Search for DICOM files recursively')

    args = parser.parse_args()

    # Validate directories
    if not os.path.exists(args.source):
        print(f"Error: Source directory does not exist: {args.source}")
        return 1

    # Create destination if it doesn't exist
    os.makedirs(args.destination, exist_ok=True)

    # Organize based on mode
    if args.mode == 'patient':
        organize_by_patient(args.source, args.destination, args.copy, args.recursive)
    elif args.mode == 'study':
        organize_by_study(args.source, args.destination, args.copy, args.recursive)
    elif args.mode == 'series':
        organize_by_series(args.source, args.destination, args.copy, args.recursive)
    elif args.mode == 'modality':
        organize_by_modality(args.source, args.destination, args.copy, args.recursive)

    return 0

if __name__ == "__main__":
    sys.exit(main())
