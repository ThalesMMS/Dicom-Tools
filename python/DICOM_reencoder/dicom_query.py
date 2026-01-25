#!/usr/bin/env python3
#
# dicom_query.py
# Dicom-Tools-py
#
# Builds and executes C-FIND queries against PACS servers at patient, study, or series levels.
#
# Thales Matheus Mendonça Santos - November 2025

"""
DICOM Query (C-FIND) tool for querying DICOM servers.
This script allows querying PACS servers using the DICOM C-FIND protocol.
"""

import sys
import argparse
from datetime import datetime
from pynetdicom import AE, debug_logger
from pynetdicom.sop_class import (
    PatientRootQueryRetrieveInformationModelFind,
    StudyRootQueryRetrieveInformationModelFind,
    ModalityWorklistInformationFind
)
from pydicom.dataset import Dataset

# Optional: Enable debug logging
# debug_logger()


def create_patient_query(patient_name=None, patient_id=None):
    """Create a patient-level C-FIND query."""
    ds = Dataset()

    # Query/Retrieve Level
    ds.QueryRetrieveLevel = 'PATIENT'

    # Patient Information
    ds.PatientName = patient_name if patient_name else ''
    ds.PatientID = patient_id if patient_id else ''
    ds.PatientBirthDate = ''
    ds.PatientSex = ''

    # Leaving most fields blank tells the SCP to return them if available
    return ds


def create_study_query(patient_name=None, patient_id=None, study_date=None,
                       modality=None, study_description=None):
    """Create a study-level C-FIND query."""
    ds = Dataset()

    # Query/Retrieve Level
    ds.QueryRetrieveLevel = 'STUDY'

    # Patient Information
    ds.PatientName = patient_name if patient_name else ''
    ds.PatientID = patient_id if patient_id else ''
    ds.PatientBirthDate = ''
    ds.PatientSex = ''

    # Study Information
    ds.StudyInstanceUID = ''
    ds.StudyDate = study_date if study_date else ''
    ds.StudyTime = ''
    ds.StudyDescription = study_description if study_description else ''
    ds.AccessionNumber = ''
    ds.StudyID = ''
    ds.ModalitiesInStudy = modality if modality else ''
    ds.NumberOfStudyRelatedSeries = ''
    ds.NumberOfStudyRelatedInstances = ''

    # Include common study-level attributes so the response is populated with useful columns
    return ds


def create_series_query(study_instance_uid, modality=None, series_description=None):
    """Create a series-level C-FIND query."""
    ds = Dataset()

    # Query/Retrieve Level
    ds.QueryRetrieveLevel = 'SERIES'

    # Study Information
    ds.StudyInstanceUID = study_instance_uid

    # Series Information
    ds.SeriesInstanceUID = ''
    ds.SeriesNumber = ''
    ds.SeriesDescription = series_description if series_description else ''
    ds.Modality = modality if modality else ''
    ds.SeriesDate = ''
    ds.SeriesTime = ''
    ds.NumberOfSeriesRelatedInstances = ''

    # Series queries must carry the parent study UID or they will not match anything
    return ds


def query_pacs(host, port, aet, aec, query_dataset, query_model='StudyRoot'):
    """
    Query a PACS server using C-FIND.

    Args:
        host: PACS server hostname/IP
        port: PACS server port
        aet: Calling AE Title (this application)
        aec: Called AE Title (PACS server)
        query_dataset: Query dataset
        query_model: Query model ('PatientRoot' or 'StudyRoot')

    Returns:
        List of matching datasets
    """
    # Initialize Application Entity
    ae = AE(ae_title=aet)

    # Add requested presentation context
    if query_model == 'PatientRoot':
        ae.add_requested_context(PatientRootQueryRetrieveInformationModelFind)
    else:  # StudyRoot
        ae.add_requested_context(StudyRootQueryRetrieveInformationModelFind)

    results = []

    # Associate with peer AE
    print(f"\nConnecting to PACS server...")
    print(f"  Host: {host}:{port}")
    print(f"  AE Title: {aec}")
    print(f"  Calling AE: {aet}")
    print(f"{'='*80}\n")

    assoc = ae.associate(host, port, ae_title=aec)

    if assoc.is_established:
        print("✓ Association established\n")
        print(f"Sending C-FIND query...")
        print(f"  Query Level: {query_dataset.QueryRetrieveLevel}")
        print(f"{'─'*80}\n")

        # Send C-FIND request
        responses = assoc.send_c_find(query_dataset, query_model=query_model)

        for (status, identifier) in responses:
            if status:
                # If status is pending, identifier contains the match
                if status.Status in (0xFF00, 0xFF01):
                    results.append(identifier)
                else:
                    # Final status
                    if status.Status == 0x0000:
                        print(f"\n✓ Query successful")
                    else:
                        print(f"\n⚠ Query completed with status: 0x{status.Status:04X}")

        # Release the association
        assoc.release()
        print(f"✓ Association released\n")

    else:
        print(f"✗ Association rejected, aborted or never connected")
        print(f"{'='*80}\n")
        return []

    return results


def display_results(results, query_level):
    """Display query results in a formatted table."""
    if not results:
        print("No results found.\n")
        return

    print(f"{'='*80}")
    print(f"Found {len(results)} result(s)")
    print(f"{'='*80}\n")

    for i, result in enumerate(results, 1):
        print(f"Result #{i}")
        print(f"{'─'*80}")

        if query_level == 'PATIENT':
            print(f"  Patient Name       : {result.get('PatientName', 'N/A')}")
            print(f"  Patient ID         : {result.get('PatientID', 'N/A')}")
            print(f"  Birth Date         : {result.get('PatientBirthDate', 'N/A')}")
            print(f"  Sex                : {result.get('PatientSex', 'N/A')}")

        elif query_level == 'STUDY':
            print(f"  Patient Name       : {result.get('PatientName', 'N/A')}")
            print(f"  Patient ID         : {result.get('PatientID', 'N/A')}")
            print(f"  Study Date         : {result.get('StudyDate', 'N/A')}")
            print(f"  Study Time         : {result.get('StudyTime', 'N/A')}")
            print(f"  Study Description  : {result.get('StudyDescription', 'N/A')}")
            print(f"  Accession Number   : {result.get('AccessionNumber', 'N/A')}")
            print(f"  Modalities         : {result.get('ModalitiesInStudy', 'N/A')}")
            print(f"  Number of Series   : {result.get('NumberOfStudyRelatedSeries', 'N/A')}")
            print(f"  Number of Instances: {result.get('NumberOfStudyRelatedInstances', 'N/A')}")
            print(f"  Study Instance UID : {result.get('StudyInstanceUID', 'N/A')}")

        elif query_level == 'SERIES':
            print(f"  Series Number      : {result.get('SeriesNumber', 'N/A')}")
            print(f"  Series Description : {result.get('SeriesDescription', 'N/A')}")
            print(f"  Modality           : {result.get('Modality', 'N/A')}")
            print(f"  Series Date        : {result.get('SeriesDate', 'N/A')}")
            print(f"  Number of Instances: {result.get('NumberOfSeriesRelatedInstances', 'N/A')}")
            print(f"  Series Instance UID: {result.get('SeriesInstanceUID', 'N/A')}")

        print()


def main():
    parser = argparse.ArgumentParser(
        description='Query DICOM PACS servers using C-FIND',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Query studies for a patient
  %(prog)s -H pacs.example.com -p 11112 --patient-name "Doe^John"

  # Query studies by date
  %(prog)s -H pacs.example.com -p 11112 --study-date 20240101-20241231

  # Query studies by modality
  %(prog)s -H pacs.example.com -p 11112 --modality CT

  # Query with custom AE titles
  %(prog)s -H pacs.example.com -p 11112 --aet MYAE --aec PACSAE --patient-id 12345

  # Query series for a study
  %(prog)s -H pacs.example.com -p 11112 --level SERIES --study-uid 1.2.3.4.5

Query Levels:
  PATIENT - Query for patients
  STUDY   - Query for studies (default)
  SERIES  - Query for series (requires --study-uid)

Date Formats:
  Single date: 20240101
  Date range:  20240101-20241231
  Wildcards:   2024*
        '''
    )

    # Connection parameters
    parser.add_argument('-H', '--host', required=True,
                        help='PACS server hostname or IP address')
    parser.add_argument('-p', '--port', type=int, default=11112,
                        help='PACS server port (default: 11112)')
    parser.add_argument('--aet', default='DICOMTOOLS',
                        help='Calling AE Title (default: DICOMTOOLS)')
    parser.add_argument('--aec', default='PACS',
                        help='Called AE Title (default: PACS)')

    # Query level
    parser.add_argument('-l', '--level', choices=['PATIENT', 'STUDY', 'SERIES'],
                        default='STUDY',
                        help='Query level (default: STUDY)')

    # Patient criteria
    parser.add_argument('--patient-name', help='Patient name (wildcards: *)')
    parser.add_argument('--patient-id', help='Patient ID')

    # Study criteria
    parser.add_argument('--study-date', help='Study date (YYYYMMDD or range)')
    parser.add_argument('--study-desc', help='Study description')
    parser.add_argument('--modality', help='Modality (e.g., CT, MR, CR)')
    parser.add_argument('--accession', help='Accession number')

    # Series criteria
    parser.add_argument('--study-uid', help='Study Instance UID (required for SERIES level)')
    parser.add_argument('--series-desc', help='Series description')

    # Query model
    parser.add_argument('--query-model', choices=['PatientRoot', 'StudyRoot'],
                        default='StudyRoot',
                        help='Query model (default: StudyRoot)')

    # Output options
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')

    args = parser.parse_args()

    # Enable debug logging if requested
    if args.debug:
        debug_logger()

    # Create query dataset based on level
    if args.level == 'PATIENT':
        query_ds = create_patient_query(args.patient_name, args.patient_id)

    elif args.level == 'STUDY':
        query_ds = create_study_query(
            args.patient_name,
            args.patient_id,
            args.study_date,
            args.modality,
            args.study_desc
        )

    elif args.level == 'SERIES':
        if not args.study_uid:
            print("Error: --study-uid is required for SERIES level queries")
            return 1

        query_ds = create_series_query(
            args.study_uid,
            args.modality,
            args.series_desc
        )

    # Perform query
    results = query_pacs(
        args.host,
        args.port,
        args.aet,
        args.aec,
        query_ds,
        args.query_model
    )

    # Display results
    display_results(results, args.level)

    return 0


if __name__ == "__main__":
    sys.exit(main())
