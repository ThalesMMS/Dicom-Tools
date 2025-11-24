#!/usr/bin/env python3
#
# validate_dicom.py
# Dicom-Tools-py
#
# Validates DICOM files for required metadata, pixel integrity, and formatting issues.
#
# Thales Matheus Mendonça Santos - November 2025

"""
Validate DICOM files for conformance and integrity.
This script checks DICOM files for proper structure, required tags,
and data integrity.
"""

from typing import Optional

import pydicom
import sys
import os

class DicomValidator:
    """DICOM file validator."""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []

    def _reset(self):
        self.errors = []
        self.warnings = []
        self.info = []

    def validate_file(self, file_path):
        """
        Validate a DICOM file.

        Args:
            file_path: Path to DICOM file to validate

        Returns:
            True if valid (no errors), False otherwise
        """
        self._reset()

        print(f"\n{'='*80}")
        print(f"DICOM File Validation")
        print(f"{'='*80}")
        print(f"File: {file_path}\n")

        # Check if file exists
        if not os.path.exists(file_path):
            self.errors.append(f"File does not exist: {file_path}")
            return False

        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            self.errors.append("File is empty")
            return False

        self.info.append(f"File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")

        # Try to read the file
        try:
            # `force=True` lets us surface more actionable errors on slightly malformed files
            dataset = pydicom.dcmread(file_path, force=True)
        except Exception as e:
            self.errors.append(f"Failed to read DICOM file: {e}")
            return False

        self._validate_preamble(file_path)
        return self.validate_dataset(dataset, file_path=file_path)

    def validate_dataset(self, dataset: pydicom.dataset.Dataset, *, file_path: Optional[str] = None,
                         display: bool = True) -> bool:
        """Validate an in-memory dataset; optionally reference its source path."""
        # Do not reset if called from validate_file which already wiped state
        if not self.info and not self.errors and not self.warnings:
            self._reset()

        if file_path:
            self._validate_preamble(file_path)

        if not hasattr(dataset, 'file_meta'):
            self.errors.append("Missing file meta information header")
        else:
            self._validate_file_meta(dataset.file_meta)

        self._validate_required_elements(dataset)
        self._validate_sop_class(dataset)
        self._validate_transfer_syntax(dataset)

        if 'PixelData' in dataset:
            self._validate_pixel_data(dataset)

        self._validate_uids(dataset)
        self._validate_dates_times(dataset)

        if display:
            self._print_results()

        return len(self.errors) == 0

    def _validate_preamble(self, file_path: str):
        try:
            with open(file_path, 'rb') as f:
                f.read(128)
                prefix = f.read(4)

                if prefix != b'DICM':
                    # Some writers omit the preamble; warn instead of failing to keep validation informative
                    self.warnings.append("Missing 'DICM' prefix (file may be implicit format)")
                else:
                    self.info.append("✓ Valid DICOM prefix found")
        except Exception as e:
            self.warnings.append(f"Could not check DICOM preamble: {e}")

    def _validate_file_meta(self, file_meta):
        """Validate file meta information."""
        # Minimal set of tags required by Part 10 to describe the encapsulated dataset
        required_meta = [
            'FileMetaInformationGroupLength',
            'FileMetaInformationVersion',
            'MediaStorageSOPClassUID',
            'MediaStorageSOPInstanceUID',
            'TransferSyntaxUID',
        ]

        for tag in required_meta:
            if tag not in file_meta:
                self.errors.append(f"Missing required file meta tag: {tag}")
            else:
                self.info.append(f"✓ {tag} present")

    def _validate_required_elements(self, dataset):
        """Validate required DICOM elements."""
        # Common required Type 1 elements
        required_elements = {
            'SOPClassUID': 'SOP Class UID',
            'SOPInstanceUID': 'SOP Instance UID',
            'StudyInstanceUID': 'Study Instance UID',
            'SeriesInstanceUID': 'Series Instance UID',
            'Modality': 'Modality',
        }

        for tag, description in required_elements.items():
            if tag not in dataset:
                self.errors.append(f"Missing required element: {description} ({tag})")
            elif not dataset.get(tag):
                self.errors.append(f"Empty required element: {description} ({tag})")
            else:
                self.info.append(f"✓ {description} present")

        # Type 2 elements (must be present but can be empty)
        type2_elements = {
            'PatientName': 'Patient Name',
            'PatientID': 'Patient ID',
            'StudyDate': 'Study Date',
            'StudyTime': 'Study Time',
        }

        for tag, description in type2_elements.items():
            if tag not in dataset:
                self.warnings.append(f"Missing Type 2 element: {description} ({tag})")

    def _validate_sop_class(self, dataset):
        """Validate SOP Class UID."""
        if 'SOPClassUID' in dataset:
            sop_class_uid = dataset.SOPClassUID
            try:
                sop_class_name = sop_class_uid.name
                self.info.append(f"✓ SOP Class: {sop_class_name}")
            except AttributeError:
                self.warnings.append(f"Unknown SOP Class UID: {sop_class_uid}")

    def _validate_transfer_syntax(self, dataset):
        """Validate transfer syntax."""
        if hasattr(dataset, 'file_meta') and 'TransferSyntaxUID' in dataset.file_meta:
            ts_uid = dataset.file_meta.TransferSyntaxUID
            try:
                ts_name = ts_uid.name
                self.info.append(f"✓ Transfer Syntax: {ts_name}")

                if hasattr(ts_uid, 'is_compressed'):
                    if ts_uid.is_compressed:
                        self.info.append(f"  Image is compressed")
                    else:
                        self.info.append(f"  Image is uncompressed")
            except AttributeError:
                self.warnings.append(f"Unknown Transfer Syntax UID: {ts_uid}")

    def _validate_pixel_data(self, dataset):
        """Validate pixel data."""
        try:
            # Check pixel data attributes
            required_pixel_attrs = ['Rows', 'Columns', 'BitsAllocated', 'BitsStored',
                                   'HighBit', 'PixelRepresentation', 'PhotometricInterpretation']

            for attr in required_pixel_attrs:
                if attr not in dataset:
                    self.errors.append(f"Missing required pixel attribute: {attr}")

            # Try to access pixel array
            try:
                # Accessing pixel_array forces decompression and reveals shape/dtype issues early
                pixel_array = dataset.pixel_array
                shape = pixel_array.shape
                dtype = pixel_array.dtype

                rows = dataset.get('Rows', 0)
                cols = dataset.get('Columns', 0)

                # Validate dimensions match
                if len(shape) >= 2:
                    actual_rows, actual_cols = shape[-2], shape[-1]
                    if actual_rows != rows or actual_cols != cols:
                        self.errors.append(
                            f"Pixel array dimensions ({actual_cols}x{actual_rows}) "
                            f"don't match metadata ({cols}x{rows})"
                        )
                    else:
                        self.info.append(f"✓ Pixel data: {cols}x{rows}, dtype={dtype}")

                # Check for multi-frame
                if len(shape) > 2:
                    frames = shape[0]
                    self.info.append(f"  Multi-frame image: {frames} frames")

            except Exception as e:
                self.errors.append(f"Cannot read pixel array: {e}")

        except Exception as e:
            self.errors.append(f"Error validating pixel data: {e}")

    def _validate_uids(self, dataset):
        """Validate UID format and uniqueness."""
        uid_tags = ['SOPInstanceUID', 'StudyInstanceUID', 'SeriesInstanceUID']

        for tag in uid_tags:
            if tag in dataset:
                uid = str(dataset.get(tag))

                # Check UID format (should contain only digits and dots)
                if not all(c.isdigit() or c == '.' for c in uid):
                    self.errors.append(f"Invalid UID format in {tag}: {uid}")

                # Check UID length (max 64 characters)
                if len(uid) > 64:
                    self.errors.append(f"UID too long in {tag}: {len(uid)} characters")

                # Check for leading/trailing dots
                if uid.startswith('.') or uid.endswith('.'):
                    self.errors.append(f"Invalid UID (leading/trailing dot) in {tag}")

    def _validate_dates_times(self, dataset):
        """Validate date and time format."""
        date_tags = ['StudyDate', 'SeriesDate', 'ContentDate', 'AcquisitionDate']
        time_tags = ['StudyTime', 'SeriesTime', 'ContentTime', 'AcquisitionTime']

        for tag in date_tags:
            if tag in dataset:
                date_str = str(dataset.get(tag))
                if date_str and not self._is_valid_dicom_date(date_str):
                    self.warnings.append(f"Invalid date format in {tag}: {date_str}")

        for tag in time_tags:
            if tag in dataset:
                time_str = str(dataset.get(tag))
                if time_str and not self._is_valid_dicom_time(time_str):
                    self.warnings.append(f"Invalid time format in {tag}: {time_str}")

    def _is_valid_dicom_date(self, date_str):
        """Check if date string is valid DICOM format (YYYYMMDD)."""
        if len(date_str) != 8:
            return False
        try:
            int(date_str)
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            return 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100
        except ValueError:
            return False

    def _is_valid_dicom_time(self, time_str):
        """Check if time string is valid DICOM format (HHMMSS.FFFFFF)."""
        if not time_str:
            return False
        try:
            parts = time_str.split('.')
            time_part = parts[0]
            if len(time_part) < 2:
                return False
            hour = int(time_part[:2])
            return 0 <= hour <= 23
        except (ValueError, IndexError):
            return False

    def _print_results(self):
        """Print validation results."""
        print(f"\n{'─'*80}")
        print("VALIDATION RESULTS")
        print(f"{'─'*80}\n")

        if self.info:
            print("Information:")
            for msg in self.info:
                print(f"  {msg}")
            print()

        if self.warnings:
            print("Warnings:")
            for msg in self.warnings:
                print(f"  ⚠ {msg}")
            print()

        if self.errors:
            print("Errors:")
            for msg in self.errors:
                print(f"  ✗ {msg}")
            print()

        print(f"{'='*80}")
        if self.errors:
            print(f"✗ VALIDATION FAILED - {len(self.errors)} error(s), {len(self.warnings)} warning(s)")
        elif self.warnings:
            print(f"⚠ VALIDATION PASSED WITH WARNINGS - {len(self.warnings)} warning(s)")
        else:
            print("✓ VALIDATION PASSED - No errors or warnings")
        print(f"{'='*80}\n")

def main():
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        print("Usage: dicom-validate <input_file>")
        if os.path.exists("1.dcm"):
            input_file = "1.dcm"
        else:
            sys.exit(1)

    validator = DicomValidator()
    is_valid = validator.validate_file(input_file)

    sys.exit(0 if is_valid else 1)

if __name__ == "__main__":
    main()
