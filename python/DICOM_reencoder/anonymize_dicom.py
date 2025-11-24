#!/usr/bin/env python3
#
# anonymize_dicom.py
# Dicom-Tools-py
#
# Provides anonymization utilities that strip PHI from DICOM datasets while preserving clinical content.
#
# Thales Matheus Mendonça Santos - November 2025

"""
Anonymize DICOM files by removing or replacing patient identifiable information.
This script creates an anonymized copy of a DICOM file, removing PHI (Protected Health Information)
while preserving the medical image data and necessary technical metadata.
"""

import pydicom
import sys
import os
from datetime import datetime, timedelta
import hashlib

def generate_anonymous_id(original_id):
    """Generate a consistent anonymous ID using hash."""
    return hashlib.sha256(str(original_id).encode()).hexdigest()[:16].upper()

def anonymize_dicom(input_file, output_file=None, patient_prefix="ANON"):
    """
    Anonymize a DICOM file by removing or replacing patient information.

    Args:
        input_file: Path to input DICOM file
        output_file: Path to output anonymized file (default: input_anonymized.dcm)
        patient_prefix: Prefix for anonymized patient ID
    """
    try:
        # Read the DICOM file
        dataset = pydicom.dcmread(input_file, force=True)

        if output_file is None:
            base, ext = os.path.splitext(input_file)
            output_file = f"{base}_anonymized{ext}"

        print(f"\nAnonymizing DICOM file: {input_file}")
        print(f"{'='*80}")

        # Store original patient ID for hash generation
        original_patient_id = dataset.get('PatientID', 'UNKNOWN')
        anonymous_id = f"{patient_prefix}_{generate_anonymous_id(original_patient_id)}"

        # Patient Information - Remove or replace
        patient_tags_to_anonymize = {
            'PatientName': 'ANONYMOUS^PATIENT',
            'PatientID': anonymous_id,
            'PatientBirthDate': '',
            'PatientSex': '',
            'PatientAge': '',
            'PatientWeight': '',
            'PatientSize': '',
            'PatientAddress': '',
            'PatientTelephoneNumbers': '',
            'PatientMotherBirthName': '',
            'MilitaryRank': '',
            'EthnicGroup': '',
            'Occupation': '',
            'AdditionalPatientHistory': '',
            'PatientComments': '',
            'ResponsiblePerson': '',
            'ResponsibleOrganization': '',
        }

        for tag, value in patient_tags_to_anonymize.items():
            if tag in dataset:
                # Replace sensitive tag values with neutral placeholders
                dataset.data_element(tag).value = value
                print(f"  ✓ Anonymized: {tag}")

        # Remove patient birth date but preserve age if possible
        if 'PatientBirthDate' in dataset and 'StudyDate' in dataset:
            try:
                birth_date = datetime.strptime(dataset.PatientBirthDate, '%Y%m%d')
                study_date = datetime.strptime(dataset.StudyDate, '%Y%m%d')
                age = (study_date - birth_date).days // 365
                dataset.PatientAge = f"{age:03d}Y"
            except:
                pass

        # Study Information - Anonymize referring physician and other identifiable info
        study_tags_to_anonymize = {
            'ReferringPhysicianName': 'ANONYMIZED',
            'ReferringPhysicianAddress': '',
            'ReferringPhysicianTelephoneNumbers': '',
            'ReferringPhysicianIdentificationSequence': None,
            'PhysiciansOfRecord': 'ANONYMIZED',
            'PerformingPhysicianName': 'ANONYMIZED',
            'OperatorsName': 'ANONYMIZED',
            'InstitutionName': 'ANONYMIZED',
            'InstitutionAddress': '',
            'InstitutionalDepartmentName': '',
            'StationName': '',
        }

        for tag, value in study_tags_to_anonymize.items():
            if tag in dataset:
                if value is None:
                    # Some tags are sequences that are safer to drop entirely
                    delattr(dataset, tag)
                else:
                    dataset.data_element(tag).value = value
                print(f"  ✓ Anonymized: {tag}")

        # Remove or anonymize dates (shift by random offset for consistency)
        # We'll shift all dates by the same offset to maintain temporal relationships
        date_offset_days = hash(original_patient_id) % 365  # Consistent offset based on patient ID

        date_tags = [
            'StudyDate', 'SeriesDate', 'AcquisitionDate', 'ContentDate',
            'InstanceCreationDate', 'PerformedProcedureStepStartDate'
        ]

        for tag in date_tags:
            if tag in dataset and dataset.get(tag):
                try:
                    original_date = datetime.strptime(dataset.data_element(tag).value, '%Y%m%d')
                    anonymized_date = original_date - timedelta(days=date_offset_days)
                    dataset.data_element(tag).value = anonymized_date.strftime('%Y%m%d')
                    print(f"  ✓ Date shifted: {tag}")
                except:
                    dataset.data_element(tag).value = ''

        # Remove UIDs that might contain identifiable information
        # But keep critical UIDs for DICOM integrity
        uid_tags_to_regenerate = [
            'StudyInstanceUID',
            'SeriesInstanceUID',
            'SOPInstanceUID',
        ]

        print(f"\n  Generating new UIDs...")
        for tag in uid_tags_to_regenerate:
            if tag in dataset:
                # Generate new UID based on original UID + anonymous ID for consistency
                original_uid = dataset.get(tag, '')
                seed = f"{anonymous_id}_{original_uid}"
                new_uid_suffix = generate_anonymous_id(seed)
                # Use pydicom's UID generation with our seed
                new_uid = f"1.2.826.0.1.3680043.8.498.{new_uid_suffix}"
                dataset.data_element(tag).value = new_uid
                print(f"  ✓ Regenerated: {tag}")

        # Remove other potentially identifying tags
        tags_to_remove = [
            'AccessionNumber',
            'IssuerOfPatientID',
            'OtherPatientIDs',
            'OtherPatientNames',
            'PatientBirthName',
            'PatientInsurancePlanCodeSequence',
            'PatientPrimaryLanguageCodeSequence',
            'RequestingPhysician',
            'RequestingService',
            'RequestAttributesSequence',
            'ScheduledProcedureStepDescription',
            'PerformedProcedureStepDescription',
        ]

        for tag in tags_to_remove:
            if tag in dataset:
                delattr(dataset, tag)
                print(f"  ✓ Removed: {tag}")

        # Remove private tags (manufacturer-specific tags that might contain PHI)
        dataset.remove_private_tags()
        print(f"  ✓ Removed all private tags")

        # Save anonymized file
        dataset.save_as(output_file)

        print(f"\n{'='*80}")
        print(f"✓ Anonymization complete!")
        print(f"  Original Patient ID: {original_patient_id}")
        print(f"  Anonymous ID: {anonymous_id}")
        print(f"  Output file: {output_file}")
        print(f"{'='*80}\n")

        return dataset

    except Exception as e:
        print(f"Error anonymizing DICOM file: {e}", file=sys.stderr)
        return None

def main():
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        print("Usage: dicom-anonymize <input_file> [output_file]")
        if os.path.exists("1.dcm"):
            input_file = "1.dcm"
            output_file = None
        else:
            sys.exit(1)

    anonymize_dicom(input_file, output_file)

if __name__ == "__main__":
    main()
