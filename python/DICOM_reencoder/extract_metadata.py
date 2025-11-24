#!/usr/bin/env python3
#
# extract_metadata.py
# Dicom-Tools-py
#
# Reads a DICOM file and displays detailed metadata across patient, study, series, and image sections.
#
# Thales Matheus Mendonça Santos - November 2025

"""
Extract and display detailed DICOM metadata.
This script reads a DICOM file and displays comprehensive metadata information
in a structured format.
"""

import pydicom
import sys
import os
from datetime import datetime

def format_value(value):
    """Format DICOM values for better readability."""
    # DICOM stores many fields as multi-values or raw bytes; normalize them for display
    if isinstance(value, pydicom.multival.MultiValue):
        return ', '.join(str(v) for v in value)
    elif isinstance(value, bytes):
        try:
            return value.decode('utf-8', errors='ignore')
        except:
            return str(value)
    return str(value)

def extract_metadata(input_file):
    """Extract and display metadata from a DICOM file."""
    try:
        # Read the DICOM file
        dataset = pydicom.dcmread(input_file, force=True)

        print(f"\n{'='*80}")
        print(f"DICOM Metadata Extraction")
        print(f"{'='*80}")
        print(f"File: {input_file}\n")

        # Patient Information
        print(f"{'─'*80}")
        print("PATIENT INFORMATION")
        print(f"{'─'*80}")
        patient_fields = [
            'PatientName', 'PatientID', 'PatientBirthDate', 'PatientSex',
            'PatientAge', 'PatientWeight', 'PatientSize'
        ]
        for field in patient_fields:
            value = dataset.get(field, 'N/A')
            print(f"  {field:<25}: {format_value(value)}")

        # Study Information
        print(f"\n{'─'*80}")
        print("STUDY INFORMATION")
        print(f"{'─'*80}")
        study_fields = [
            'StudyDescription', 'StudyDate', 'StudyTime', 'StudyInstanceUID',
            'AccessionNumber', 'ReferringPhysicianName', 'StudyID'
        ]
        for field in study_fields:
            value = dataset.get(field, 'N/A')
            print(f"  {field:<25}: {format_value(value)}")

        # Series Information
        print(f"\n{'─'*80}")
        print("SERIES INFORMATION")
        print(f"{'─'*80}")
        series_fields = [
            'SeriesDescription', 'SeriesNumber', 'SeriesDate', 'SeriesTime',
            'SeriesInstanceUID', 'Modality', 'BodyPartExamined', 'ProtocolName'
        ]
        for field in series_fields:
            value = dataset.get(field, 'N/A')
            print(f"  {field:<25}: {format_value(value)}")

        # Image Information
        print(f"\n{'─'*80}")
        print("IMAGE INFORMATION")
        print(f"{'─'*80}")
        image_fields = [
            'InstanceNumber', 'ImageType', 'SOPClassUID', 'SOPInstanceUID',
            'ContentDate', 'ContentTime', 'AcquisitionDate', 'AcquisitionTime'
        ]
        for field in image_fields:
            value = dataset.get(field, 'N/A')
            print(f"  {field:<25}: {format_value(value)}")

        # Equipment Information
        print(f"\n{'─'*80}")
        print("EQUIPMENT INFORMATION")
        print(f"{'─'*80}")
        equipment_fields = [
            'Manufacturer', 'ManufacturerModelName', 'DeviceSerialNumber',
            'SoftwareVersions', 'InstitutionName', 'StationName'
        ]
        for field in equipment_fields:
            value = dataset.get(field, 'N/A')
            print(f"  {field:<25}: {format_value(value)}")

        # Image Acquisition Parameters
        print(f"\n{'─'*80}")
        print("IMAGE ACQUISITION PARAMETERS")
        print(f"{'─'*80}")
        acquisition_fields = [
            'SliceThickness', 'KVP', 'ExposureTime', 'XRayTubeCurrent',
            'Exposure', 'FilterType', 'ConvolutionKernel', 'DataCollectionDiameter'
        ]
        for field in acquisition_fields:
            value = dataset.get(field, 'N/A')
            print(f"  {field:<25}: {format_value(value)}")

        # Pixel Data Information
        if 'PixelData' in dataset:
            print(f"\n{'─'*80}")
            print("PIXEL DATA INFORMATION")
            print(f"{'─'*80}")
            pixel_fields = [
                'Rows', 'Columns', 'NumberOfFrames', 'BitsAllocated',
                'BitsStored', 'HighBit', 'PixelRepresentation',
                'PhotometricInterpretation', 'SamplesPerPixel', 'PlanarConfiguration'
            ]
            for field in pixel_fields:
                value = dataset.get(field, 'N/A')
                print(f"  {field:<25}: {format_value(value)}")

            # Calculate image size
            rows = dataset.get('Rows', 0)
            cols = dataset.get('Columns', 0)
            if rows and cols:
                print(f"  {'Image Dimensions':<25}: {cols} x {rows}")

        # Transfer Syntax
        print(f"\n{'─'*80}")
        print("TRANSFER SYNTAX")
        print(f"{'─'*80}")
        if hasattr(dataset, 'file_meta'):
            ts_uid = dataset.file_meta.get('TransferSyntaxUID', 'N/A')
            print(f"  Transfer Syntax UID      : {ts_uid}")
            if hasattr(ts_uid, 'name'):
                print(f"  Transfer Syntax Name     : {ts_uid.name}")
            if hasattr(ts_uid, 'is_compressed'):
                print(f"  Is Compressed            : {ts_uid.is_compressed}")

        print(f"\n{'='*80}\n")

        return dataset

    except Exception as e:
        print(f"Error reading DICOM file: {e}", file=sys.stderr)
        return None

def main():
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        print("Usage: dicom-extract-metadata <input_file>")
        if os.path.exists("1.dcm"):
            input_file = "1.dcm"
        else:
            sys.exit(1)

    extract_metadata(input_file)

if __name__ == "__main__":
    main()
