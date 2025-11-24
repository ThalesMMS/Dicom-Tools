#!/usr/bin/env python3
#
# search_dicom.py
# Dicom-Tools-py
#
# Searches DICOM files by metadata criteria with wildcard and regex support.
#
# Thales Matheus Mendonça Santos - November 2025

"""
Search DICOM files based on metadata criteria.
This script allows searching through DICOM files to find those matching
specific metadata criteria.
"""

import pydicom
import sys
import os
import glob
import re
import argparse
from datetime import datetime

def search_dicom_files(directory, criteria, recursive=False, output_format='table'):
    """
    Search for DICOM files matching criteria.

    Args:
        directory: Directory to search
        criteria: Dictionary of search criteria {tag: value}
        recursive: Search recursively
        output_format: Output format ('table', 'list', 'csv')

    Returns:
        List of matching files
    """
    print(f"\nSearching DICOM files...")
    print(f"Directory: {directory}")
    print(f"Recursive: {recursive}")
    print(f"{'='*80}\n")

    # Display search criteria
    print("Search Criteria:")
    for tag, value in criteria.items():
        print(f"  {tag}: {value}")
    print(f"\n{'─'*80}\n")

    # Find all DICOM files
    pattern = '**/*.dcm' if recursive else '*.dcm'
    all_files = glob.glob(os.path.join(directory, pattern), recursive=recursive)

    # Also check files without extension
    if not recursive:
        for file_path in glob.glob(os.path.join(directory, '*')):
            if os.path.isfile(file_path) and not file_path.endswith('.dcm'):
                try:
                    # Try to sniff header information without loading pixel data
                    pydicom.dcmread(file_path, stop_before_pixels=True, force=True)
                    all_files.append(file_path)
                except:
                    pass

    print(f"Found {len(all_files)} DICOM files to search\n")

    matching_files = []
    matched_data = []

    for file_path in all_files:
        try:
            # Load header only; skipping pixel buffers keeps the search fast
            dataset = pydicom.dcmread(file_path, stop_before_pixels=True, force=True)

            # Check if all criteria match
            match = True
            for tag, search_value in criteria.items():
                if tag not in dataset:
                    match = False
                    break

                file_value = str(dataset.get(tag, ''))

                # Support wildcard and regex matching
                if '*' in search_value:
                    # Wildcard matching
                    pattern = search_value.replace('*', '.*')
                    if not re.match(pattern, file_value, re.IGNORECASE):
                        match = False
                        break
                elif search_value.startswith('/') and search_value.endswith('/'):
                    # Regex matching
                    regex = search_value[1:-1]
                    if not re.search(regex, file_value, re.IGNORECASE):
                        match = False
                        break
                else:
                    # Exact or substring matching
                    if search_value.lower() not in file_value.lower():
                        match = False
                        break

            if match:
                matching_files.append(file_path)

                # Collect data for display
                file_data = {'file': os.path.basename(file_path)}
                for tag in criteria.keys():
                    file_data[tag] = str(dataset.get(tag, 'N/A'))

                # Add some additional useful fields
                file_data['Modality'] = str(dataset.get('Modality', 'N/A'))
                file_data['StudyDate'] = str(dataset.get('StudyDate', 'N/A'))

                matched_data.append(file_data)

        except Exception as e:
            # Silently skip files that can't be read
            pass

    # Display results
    print(f"{'='*80}")
    print(f"Found {len(matching_files)} matching files")
    print(f"{'='*80}\n")

    if matching_files:
        if output_format == 'table':
            display_table(matched_data)
        elif output_format == 'list':
            display_list(matching_files)
        elif output_format == 'csv':
            display_csv(matched_data)

    return matching_files

def display_table(data):
    """Display results in table format."""
    if not data:
        return

    # Get all unique keys
    all_keys = set()
    for row in data:
        all_keys.update(row.keys())

    keys = ['file'] + [k for k in sorted(all_keys) if k != 'file']

    # Calculate column widths
    col_widths = {}
    for key in keys:
        col_widths[key] = max(len(key), max(len(str(row.get(key, ''))) for row in data))
        col_widths[key] = min(col_widths[key], 40)  # Max width

    # Print header
    header = ' | '.join(k.ljust(col_widths[k]) for k in keys)
    print(header)
    print('-' * len(header))

    # Print rows
    for row in data:
        values = []
        for key in keys:
            value = str(row.get(key, 'N/A'))
            if len(value) > col_widths[key]:
                value = value[:col_widths[key]-3] + '...'
            values.append(value.ljust(col_widths[key]))
        print(' | '.join(values))

    print()

def display_list(files):
    """Display results as a simple list."""
    for i, file_path in enumerate(files, 1):
        print(f"{i:3d}. {file_path}")
    print()

def display_csv(data):
    """Display results in CSV format."""
    if not data:
        return

    # Get all unique keys
    all_keys = set()
    for row in data:
        all_keys.update(row.keys())

    keys = ['file'] + [k for k in sorted(all_keys) if k != 'file']

    # Print header
    print(','.join(keys))

    # Print rows
    for row in data:
        values = [f'"{row.get(key, "")}"' for key in keys]
        print(','.join(values))

    print()

def search_by_patient(directory, patient_name=None, patient_id=None, recursive=False):
    """Search by patient information."""
    criteria = {}
    if patient_name:
        criteria['PatientName'] = patient_name
    if patient_id:
        criteria['PatientID'] = patient_id

    return search_dicom_files(directory, criteria, recursive)

def search_by_study(directory, study_desc=None, study_date=None, modality=None, recursive=False):
    """Search by study information."""
    criteria = {}
    if study_desc:
        criteria['StudyDescription'] = study_desc
    if study_date:
        criteria['StudyDate'] = study_date
    if modality:
        criteria['Modality'] = modality

    return search_dicom_files(directory, criteria, recursive)

def search_by_date_range(directory, start_date, end_date, recursive=False):
    """
    Search for files within a date range.

    Args:
        directory: Directory to search
        start_date: Start date (YYYYMMDD)
        end_date: End date (YYYYMMDD)
        recursive: Search recursively
    """
    print(f"\nSearching DICOM files by date range...")
    print(f"Directory: {directory}")
    print(f"Date range: {start_date} to {end_date}")
    print(f"{'='*80}\n")

    pattern = '**/*.dcm' if recursive else '*.dcm'
    all_files = glob.glob(os.path.join(directory, pattern), recursive=recursive)

    matching_files = []

    try:
        # Parse dates upfront so invalid formats fail fast
        start = datetime.strptime(start_date, '%Y%m%d')
        end = datetime.strptime(end_date, '%Y%m%d')
    except ValueError:
        print("Error: Dates must be in YYYYMMDD format")
        return []

    for file_path in all_files:
        try:
            dataset = pydicom.dcmread(file_path, stop_before_pixels=True, force=True)
            study_date_str = str(dataset.get('StudyDate', ''))

            if study_date_str and len(study_date_str) == 8:
                study_date = datetime.strptime(study_date_str, '%Y%m%d')

                if start <= study_date <= end:
                    matching_files.append(file_path)
                    print(f"  ✓ {os.path.basename(file_path)} - {study_date.strftime('%Y-%m-%d')}")

        except Exception as e:
            pass

    print(f"\n{'='*80}")
    print(f"Found {len(matching_files)} files in date range")
    print(f"{'='*80}\n")

    return matching_files

def main():
    parser = argparse.ArgumentParser(
        description='Search DICOM files by metadata criteria',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Search Examples:
  # Search by patient name
  %(prog)s -d /path/to/dicoms --patient-name "Doe*"

  # Search by modality
  %(prog)s -d /path/to/dicoms --modality CT

  # Search by study description (partial match)
  %(prog)s -d /path/to/dicoms --study-desc "chest"

  # Custom tag search
  %(prog)s -d /path/to/dicoms -t PatientID=12345 -t Modality=MR

  # Date range search
  %(prog)s -d /path/to/dicoms --date-range 20240101 20241231

  # Export results to CSV
  %(prog)s -d /path/to/dicoms --modality CT --format csv

Wildcard Matching:
  Use * for wildcard matching: "Doe*" matches "Doe^John", "Doe^Jane", etc.

Regex Matching:
  Use /regex/ for regex patterns: "/^CT.*/" matches any string starting with "CT"
        '''
    )

    parser.add_argument('-d', '--directory', required=True,
                        help='Directory to search')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='Search recursively')
    parser.add_argument('--format', choices=['table', 'list', 'csv'], default='table',
                        help='Output format (default: table)')

    # Patient search
    parser.add_argument('--patient-name', help='Patient name to search')
    parser.add_argument('--patient-id', help='Patient ID to search')

    # Study search
    parser.add_argument('--study-desc', help='Study description to search')
    parser.add_argument('--study-date', help='Study date (YYYYMMDD)')
    parser.add_argument('--modality', help='Modality to search')

    # Date range
    parser.add_argument('--date-range', nargs=2, metavar=('START', 'END'),
                        help='Search by date range (YYYYMMDD YYYYMMDD)')

    # Custom tag search
    parser.add_argument('-t', '--tag', action='append', metavar='TAG=VALUE',
                        help='Custom tag search (can be used multiple times)')

    args = parser.parse_args()

    # Date range search
    if args.date_range:
        search_by_date_range(args.directory, args.date_range[0], args.date_range[1], args.recursive)
        return 0

    # Build criteria dictionary
    criteria = {}

    # Patient criteria
    if args.patient_name:
        criteria['PatientName'] = args.patient_name
    if args.patient_id:
        criteria['PatientID'] = args.patient_id

    # Study criteria
    if args.study_desc:
        criteria['StudyDescription'] = args.study_desc
    if args.study_date:
        criteria['StudyDate'] = args.study_date
    if args.modality:
        criteria['Modality'] = args.modality

    # Custom tag criteria
    if args.tag:
        for tag_spec in args.tag:
            if '=' not in tag_spec:
                print(f"Error: Invalid tag specification: {tag_spec}")
                print("Format should be: TagName=Value")
                return 1
            tag_name, value = tag_spec.split('=', 1)
            criteria[tag_name.strip()] = value.strip()

    if not criteria:
        print("Error: No search criteria specified")
        parser.print_help()
        return 1

    # Perform search
    search_dicom_files(args.directory, criteria, args.recursive, args.format)

    return 0

if __name__ == "__main__":
    sys.exit(main())
