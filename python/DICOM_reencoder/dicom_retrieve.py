#!/usr/bin/env python3
#
# dicom_retrieve.py
# Dicom-Tools-py
#
# Retrieves studies using C-MOVE or C-GET and writes received instances to disk.
#
# Thales Matheus Mendonça Santos - November 2025

"""
DICOM Retrieve (C-MOVE/C-GET) tool for retrieving studies from PACS.
This script allows retrieving DICOM studies from PACS servers using
the DICOM C-MOVE or C-GET protocols.
"""

import sys
import os
import argparse
from pathlib import Path
from pynetdicom import AE, evt, StoragePresentationContexts, debug_logger
from pynetdicom.sop_class import (
    PatientRootQueryRetrieveInformationModelMove,
    StudyRootQueryRetrieveInformationModelMove,
    PatientRootQueryRetrieveInformationModelGet,
    StudyRootQueryRetrieveInformationModelGet,
)
from pydicom.dataset import Dataset

# Optional: Enable debug logging
# debug_logger()


def handle_store(event, output_dir):
    """
    Handler for C-STORE requests (when receiving instances).

    Args:
        event: The C-STORE event
        output_dir: Directory to save received files

    Returns:
        Success status (0x0000)
    """
    ds = event.dataset
    ds.file_meta = event.file_meta

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename from SOP Instance UID
    sop_instance_uid = ds.SOPInstanceUID
    filename = f"{sop_instance_uid}.dcm"
    filepath = os.path.join(output_dir, filename)

    # Save the dataset
    ds.save_as(filepath, write_like_original=False)

    print(f"  ✓ Received and saved: {filename}")

    # Return success status
    return 0x0000


def create_retrieve_query(level, study_uid=None, series_uid=None, instance_uid=None):
    """
    Create a C-MOVE/C-GET query dataset.

    Args:
        level: Query level ('STUDY', 'SERIES', or 'IMAGE')
        study_uid: Study Instance UID
        series_uid: Series Instance UID
        instance_uid: SOP Instance UID

    Returns:
        Query dataset
    """
    ds = Dataset()
    ds.QueryRetrieveLevel = level

    if level == 'STUDY':
        if not study_uid:
            raise ValueError("Study UID required for STUDY level retrieval")
        ds.StudyInstanceUID = study_uid

    elif level == 'SERIES':
        if not study_uid or not series_uid:
            raise ValueError("Study UID and Series UID required for SERIES level retrieval")
        ds.StudyInstanceUID = study_uid
        ds.SeriesInstanceUID = series_uid

    elif level == 'IMAGE':
        if not study_uid or not series_uid or not instance_uid:
            raise ValueError("Study, Series, and Instance UIDs required for IMAGE level retrieval")
        ds.StudyInstanceUID = study_uid
        ds.SeriesInstanceUID = series_uid
        ds.SOPInstanceUID = instance_uid

    # Query/Retrieve operations fail silently when required identifiers are missing, so we enforce them early
    return ds


def retrieve_with_move(host, port, aet, aec, move_destination, query_dataset,
                       query_model='StudyRoot'):
    """
    Retrieve using C-MOVE protocol.

    Args:
        host: PACS server hostname/IP
        port: PACS server port
        aet: Calling AE Title
        aec: Called AE Title (PACS)
        move_destination: AE Title where images should be sent
        query_dataset: Retrieve query dataset
        query_model: Query model ('PatientRoot' or 'StudyRoot')

    Returns:
        Number of instances moved
    """
    # Initialize Application Entity
    ae = AE(ae_title=aet)

    # Add requested presentation context for C-MOVE
    if query_model == 'PatientRoot':
        ae.add_requested_context(PatientRootQueryRetrieveInformationModelMove)
    else:  # StudyRoot
        ae.add_requested_context(StudyRootQueryRetrieveInformationModelMove)

    print(f"\nConnecting to PACS server for C-MOVE...")
    print(f"  Host: {host}:{port}")
    print(f"  Called AE: {aec}")
    print(f"  Calling AE: {aet}")
    print(f"  Move Destination: {move_destination}")
    print(f"{'='*80}\n")

    # Associate with peer AE
    assoc = ae.associate(host, port, ae_title=aec)

    moved_count = 0

    if assoc.is_established:
        print("✓ Association established\n")
        print(f"Sending C-MOVE request...")
        print(f"  Query Level: {query_dataset.QueryRetrieveLevel}")
        print(f"{'─'*80}\n")

        # Send C-MOVE request
        responses = assoc.send_c_move(
            query_dataset,
            move_destination,
            query_model=query_model
        )

        for (status, identifier) in responses:
            if status:
                # Print progress
                if status.Status in (0xFF00, 0xFF01):
                    # Pending
                    if hasattr(status, 'NumberOfRemainingSuboperations'):
                        remaining = status.NumberOfRemainingSuboperations
                        completed = status.NumberOfCompletedSuboperations
                        print(f"  Progress: {completed} completed, {remaining} remaining")

                elif status.Status == 0x0000:
                    # Success
                    if hasattr(status, 'NumberOfCompletedSuboperations'):
                        moved_count = status.NumberOfCompletedSuboperations
                    print(f"\n✓ C-MOVE successful")

                else:
                    # Warning or failure
                    print(f"\n⚠ C-MOVE status: 0x{status.Status:04X}")

        # Release the association
        assoc.release()
        print(f"✓ Association released\n")

    else:
        print(f"✗ Association rejected, aborted or never connected\n")
        return 0

    return moved_count


def retrieve_with_get(host, port, aet, aec, output_dir, query_dataset,
                      query_model='StudyRoot'):
    """
    Retrieve using C-GET protocol.

    Args:
        host: PACS server hostname/IP
        port: PACS server port
        aet: Calling AE Title
        aec: Called AE Title (PACS)
        output_dir: Directory to save received files
        query_dataset: Retrieve query dataset
        query_model: Query model ('PatientRoot' or 'StudyRoot')

    Returns:
        Number of instances retrieved
    """
    # Initialize Application Entity
    ae = AE(ae_title=aet)

    # Add requested presentation context for C-GET
    if query_model == 'PatientRoot':
        ae.add_requested_context(PatientRootQueryRetrieveInformationModelGet)
    else:  # StudyRoot
        ae.add_requested_context(StudyRootQueryRetrieveInformationModelGet)

    # Add storage presentation contexts (to receive instances)
    ae.requested_contexts = StoragePresentationContexts

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    print(f"\nConnecting to PACS server for C-GET...")
    print(f"  Host: {host}:{port}")
    print(f"  Called AE: {aec}")
    print(f"  Calling AE: {aet}")
    print(f"  Output Directory: {output_dir}")
    print(f"{'='*80}\n")

    # Set up event handler for C-STORE
    # Register a minimal C-STORE handler to capture incoming instances to disk
    handlers = [(evt.EVT_C_STORE, lambda event: handle_store(event, output_dir))]

    # Associate with peer AE
    assoc = ae.associate(host, port, ae_title=aec, evt_handlers=handlers)

    retrieved_count = 0

    if assoc.is_established:
        print("✓ Association established\n")
        print(f"Sending C-GET request...")
        print(f"  Query Level: {query_dataset.QueryRetrieveLevel}")
        print(f"{'─'*80}\n")

        print("Receiving instances:\n")

        # Send C-GET request
        responses = assoc.send_c_get(query_dataset, query_model=query_model)

        for (status, identifier) in responses:
            if status:
                # Print progress
                if status.Status in (0xFF00, 0xFF01):
                    # Pending
                    if hasattr(status, 'NumberOfRemainingSuboperations'):
                        remaining = status.NumberOfRemainingSuboperations
                        completed = status.NumberOfCompletedSuboperations
                        print(f"  Progress: {completed} completed, {remaining} remaining")

                elif status.Status == 0x0000:
                    # Success
                    if hasattr(status, 'NumberOfCompletedSuboperations'):
                        retrieved_count = status.NumberOfCompletedSuboperations
                    print(f"\n✓ C-GET successful")

                else:
                    # Warning or failure
                    print(f"\n⚠ C-GET status: 0x{status.Status:04X}")

        # Release the association
        assoc.release()
        print(f"✓ Association released\n")

    else:
        print(f"✗ Association rejected, aborted or never connected\n")
        return 0

    return retrieved_count


def main():
    parser = argparse.ArgumentParser(
        description='Retrieve DICOM studies from PACS using C-MOVE or C-GET',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Retrieve study using C-GET
  %(prog)s -H pacs.example.com -p 11112 --study-uid 1.2.3.4.5 -o ./output

  # Retrieve study using C-MOVE
  %(prog)s -H pacs.example.com -p 11112 --study-uid 1.2.3.4.5 --use-move --move-dest MYAE

  # Retrieve series using C-GET
  %(prog)s -H pacs.example.com -p 11112 --study-uid 1.2.3.4.5 --series-uid 1.2.3.4.6 -o ./output

  # Retrieve with custom AE titles
  %(prog)s -H pacs.example.com -p 11112 --aet MYAE --aec PACSAE --study-uid 1.2.3.4.5 -o ./output

Notes:
  - C-GET retrieves directly to this application (recommended for most cases)
  - C-MOVE sends images to a third party (requires configured SCP)
  - Study UID is always required
  - Series UID is optional (retrieves entire study if not specified)
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

    # Retrieve parameters
    parser.add_argument('--study-uid', required=True,
                        help='Study Instance UID to retrieve')
    parser.add_argument('--series-uid',
                        help='Series Instance UID (optional, retrieves entire study if not specified)')
    parser.add_argument('--instance-uid',
                        help='SOP Instance UID (requires --series-uid)')

    # Protocol selection
    parser.add_argument('--use-move', action='store_true',
                        help='Use C-MOVE instead of C-GET')
    parser.add_argument('--move-dest',
                        help='Move destination AE Title (required for C-MOVE)')

    # Output options
    parser.add_argument('-o', '--output-dir', default='./dicom_retrieved',
                        help='Output directory for C-GET (default: ./dicom_retrieved)')

    # Query model
    parser.add_argument('--query-model', choices=['PatientRoot', 'StudyRoot'],
                        default='StudyRoot',
                        help='Query model (default: StudyRoot)')

    # Debug
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')

    args = parser.parse_args()

    # Enable debug logging if requested
    if args.debug:
        debug_logger()

    # Validate C-MOVE requirements
    if args.use_move and not args.move_dest:
        print("Error: --move-dest is required when using C-MOVE")
        return 1

    # Determine query level
    if args.instance_uid:
        if not args.series_uid:
            print("Error: --series-uid is required when using --instance-uid")
            return 1
        level = 'IMAGE'
    elif args.series_uid:
        level = 'SERIES'
    else:
        level = 'STUDY'

    # Create query dataset
    query_ds = create_retrieve_query(
        level,
        args.study_uid,
        args.series_uid,
        args.instance_uid
    )

    # Perform retrieval
    if args.use_move:
        count = retrieve_with_move(
            args.host,
            args.port,
            args.aet,
            args.aec,
            args.move_dest,
            query_ds,
            args.query_model
        )
        print(f"{'='*80}")
        print(f"✓ Retrieved {count} instance(s) via C-MOVE")
        print(f"  Instances sent to: {args.move_dest}")
        print(f"{'='*80}\n")

    else:
        count = retrieve_with_get(
            args.host,
            args.port,
            args.aet,
            args.aec,
            args.output_dir,
            query_ds,
            args.query_model
        )
        print(f"{'='*80}")
        print(f"✓ Retrieved {count} instance(s) via C-GET")
        print(f"  Saved to: {args.output_dir}")
        print(f"{'='*80}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
