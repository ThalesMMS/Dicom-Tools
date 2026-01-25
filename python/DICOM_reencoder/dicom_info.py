#!/usr/bin/env python3
#
# dicom_info.py
# Dicom-Tools-py
#
# Prints human-readable summaries of DICOM metadata and pixel characteristics.
#
# Thales Matheus Mendonça Santos - November 2025

"""
Display quick summary information about DICOM files.
This script provides a concise overview of DICOM file contents,
useful for quick inspection and triage.
"""

import pydicom
import sys
import os
from datetime import datetime

def format_bytes(size):
    """Format byte size to human-readable format."""
    # Simple unit walker that stops at the first size under 1024
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

def format_dicom_date(date_str):
    """Format DICOM date string to readable format."""
    if not date_str or len(date_str) != 8:
        return date_str
    try:
        dt = datetime.strptime(date_str, '%Y%m%d')
        return dt.strftime('%Y-%m-%d')
    except:
        return date_str

def format_dicom_time(time_str):
    """Format DICOM time string to readable format."""
    if not time_str:
        return time_str
    try:
        # Handle fractional seconds
        time_str = time_str.split('.')[0]
        if len(time_str) >= 6:
            return f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
        elif len(time_str) >= 4:
            return f"{time_str[:2]}:{time_str[2:4]}"
        elif len(time_str) >= 2:
            return f"{time_str[:2]}:00"
        return time_str
    except:
        return time_str

def display_dicom_info(file_path, verbose=False):
    """
    Display summary information about a DICOM file.

    Args:
        file_path: Path to DICOM file
        verbose: Show detailed information
    """
    try:
        # Get file size
        file_size = os.path.getsize(file_path)

        # Read DICOM file
        # `force=True` prevents failures on slightly non-compliant files often found in the wild
        dataset = pydicom.dcmread(file_path, force=True)

        print(f"\n{'='*80}")
        print(f"DICOM File Information")
        print(f"{'='*80}")
        print(f"File: {os.path.basename(file_path)}")
        print(f"Path: {os.path.abspath(file_path)}")
        print(f"Size: {format_bytes(file_size)}")
        print(f"{'='*80}\n")

        # Patient Information
        print("PATIENT")
        print(f"  Name               : {dataset.get('PatientName', 'N/A')}")
        print(f"  ID                 : {dataset.get('PatientID', 'N/A')}")
        print(f"  Birth Date         : {format_dicom_date(str(dataset.get('PatientBirthDate', 'N/A')))}")
        print(f"  Sex                : {dataset.get('PatientSex', 'N/A')}")
        print(f"  Age                : {dataset.get('PatientAge', 'N/A')}")

        # Study Information
        print(f"\nSTUDY")
        print(f"  Description        : {dataset.get('StudyDescription', 'N/A')}")
        print(f"  Date               : {format_dicom_date(str(dataset.get('StudyDate', 'N/A')))}")
        print(f"  Time               : {format_dicom_time(str(dataset.get('StudyTime', 'N/A')))}")
        print(f"  Study ID           : {dataset.get('StudyID', 'N/A')}")
        print(f"  Accession Number   : {dataset.get('AccessionNumber', 'N/A')}")

        # Series Information
        print(f"\nSERIES")
        print(f"  Description        : {dataset.get('SeriesDescription', 'N/A')}")
        print(f"  Number             : {dataset.get('SeriesNumber', 'N/A')}")
        print(f"  Modality           : {dataset.get('Modality', 'N/A')}")
        print(f"  Body Part          : {dataset.get('BodyPartExamined', 'N/A')}")
        print(f"  Protocol           : {dataset.get('ProtocolName', 'N/A')}")

        # Image Information
        print(f"\nIMAGE")
        print(f"  Instance Number    : {dataset.get('InstanceNumber', 'N/A')}")
        print(f"  SOP Class UID      : {dataset.get('SOPClassUID', 'N/A')}")

        # Get SOP Class name if available
        sop_class_uid = dataset.get('SOPClassUID')
        if sop_class_uid and hasattr(sop_class_uid, 'name'):
            print(f"  SOP Class Name     : {sop_class_uid.name}")

        # Pixel Data Information
        if 'PixelData' in dataset:
            print(f"\nIMAGE DATA")

            rows = dataset.get('Rows', 'N/A')
            cols = dataset.get('Columns', 'N/A')
            print(f"  Dimensions         : {cols} x {rows}")

            # Check for multi-frame
            try:
                pixel_array = dataset.pixel_array
                if len(pixel_array.shape) > 2:
                    frames = pixel_array.shape[0]
                    print(f"  Number of Frames   : {frames}")
            except:
                pass

            print(f"  Bits Allocated     : {dataset.get('BitsAllocated', 'N/A')}")
            print(f"  Bits Stored        : {dataset.get('BitsStored', 'N/A')}")
            print(f"  Photometric Int.   : {dataset.get('PhotometricInterpretation', 'N/A')}")
            print(f"  Pixel Representation: {dataset.get('PixelRepresentation', 'N/A')}")

            samples = dataset.get('SamplesPerPixel', 1)
            print(f"  Samples per Pixel  : {samples}")

        # Transfer Syntax
        print(f"\nTRANSFER SYNTAX")
        if hasattr(dataset, 'file_meta'):
            ts_uid = dataset.file_meta.get('TransferSyntaxUID', 'N/A')
            print(f"  UID                : {ts_uid}")

            if hasattr(ts_uid, 'name'):
                print(f"  Name               : {ts_uid.name}")

            if hasattr(ts_uid, 'is_compressed'):
                compression = "Yes" if ts_uid.is_compressed else "No"
                print(f"  Compressed         : {compression}")

        # Equipment Information
        if verbose:
            print(f"\nEQUIPMENT")
            print(f"  Manufacturer       : {dataset.get('Manufacturer', 'N/A')}")
            print(f"  Model              : {dataset.get('ManufacturerModelName', 'N/A')}")
            print(f"  Station Name       : {dataset.get('StationName', 'N/A')}")
            print(f"  Institution        : {dataset.get('InstitutionName', 'N/A')}")

        # UIDs
        if verbose:
            print(f"\nUNIQUE IDENTIFIERS")
            print(f"  Study Instance UID : {dataset.get('StudyInstanceUID', 'N/A')}")
            print(f"  Series Instance UID: {dataset.get('SeriesInstanceUID', 'N/A')}")
            print(f"  SOP Instance UID   : {dataset.get('SOPInstanceUID', 'N/A')}")

        print(f"\n{'='*80}\n")

        return dataset

    except Exception as e:
        print(f"\nError reading DICOM file: {e}", file=sys.stderr)
        import traceback
        if verbose:
            traceback.print_exc()
        return None

def compare_files(file1, file2):
    """Compare basic information between two DICOM files."""
    try:
        print(f"\n{'='*80}")
        print(f"DICOM File Comparison")
        print(f"{'='*80}\n")

        ds1 = pydicom.dcmread(file1, force=True)
        ds2 = pydicom.dcmread(file2, force=True)

        fields = [
            ('Patient Name', 'PatientName'),
            ('Patient ID', 'PatientID'),
            ('Study Date', 'StudyDate'),
            ('Modality', 'Modality'),
            ('Series Description', 'SeriesDescription'),
            ('Instance Number', 'InstanceNumber'),
            ('Rows', 'Rows'),
            ('Columns', 'Columns'),
            ('Bits Allocated', 'BitsAllocated'),
        ]

        print(f"{'Field':<25} {'File 1':<30} {'File 2':<30} {'Match'}")
        print(f"{'-'*95}")

        for label, tag in fields:
            val1 = str(ds1.get(tag, 'N/A'))
            val2 = str(ds2.get(tag, 'N/A'))
            match = '✓' if val1 == val2 else '✗'

            # Truncate long values
            if len(val1) > 27:
                val1 = val1[:24] + '...'
            if len(val2) > 27:
                val2 = val2[:24] + '...'

            print(f"{label:<25} {val1:<30} {val2:<30} {match}")

        print(f"\n{'='*80}\n")

    except Exception as e:
        print(f"Error comparing files: {e}", file=sys.stderr)

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Display DICOM file information')
    parser.add_argument('file', help='DICOM file to inspect')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show detailed information')
    parser.add_argument('-c', '--compare', help='Compare with another DICOM file')

    args = parser.parse_args()

    if args.compare:
        compare_files(args.file, args.compare)
    else:
        display_dicom_info(args.file, args.verbose)

if __name__ == "__main__":
    main()
