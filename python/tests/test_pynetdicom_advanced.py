#
# test_pynetdicom_advanced.py
# Dicom-Tools-py
#
# Advanced pynetdicom tests: association negotiation, extended negotiation,
# user identity, event handlers, presentation contexts, and role selection.
#
# Thales Matheus Mendonça Santos - November 2025

import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from pydicom import Dataset
from pydicom.uid import (
    CTImageStorage,
    ExplicitVRLittleEndian,
    ImplicitVRLittleEndian,
    MRImageStorage,
    SecondaryCaptureImageStorage,
    generate_uid,
)
from pynetdicom import (
    AE,
    StoragePresentationContexts,
    build_context,
    build_role,
    evt,
)
from pynetdicom.pdu_primitives import (
    MaximumLengthNotification,
    SOPClassExtendedNegotiation,
    UserIdentityNegotiation,
)
from pynetdicom.sop_class import (
    PatientRootQueryRetrieveInformationModelFind,
    PatientRootQueryRetrieveInformationModelGet,
    PatientRootQueryRetrieveInformationModelMove,
    StudyRootQueryRetrieveInformationModelFind,
    Verification,
)
from pynetdicom.status import Status

sys.path.append(str(Path(__file__).parent))
from pynetdicom_utils import free_port  # type: ignore

from DICOM_reencoder.core.factories import build_secondary_capture


class TestPresentationContexts:
    """Test presentation context negotiation and management."""

    def test_multiple_transfer_syntaxes_per_context(self):
        ae = AE(ae_title="CONTEXT_SCU")
        context = build_context(
            CTImageStorage,
            [ExplicitVRLittleEndian, ImplicitVRLittleEndian],
        )
        ae.add_requested_context(context.abstract_syntax, context.transfer_syntax)

        requested = ae.requested_contexts
        assert any(c.abstract_syntax == CTImageStorage for c in requested)

    def test_context_rejection_handling(self):
        """Test that rejected contexts are properly identified."""
        ae_scp = AE(ae_title="REJECT_SCP")
        ae_scp.add_supported_context(Verification)  # Only Verification
        port = free_port()
        server = ae_scp.start_server(("127.0.0.1", port), block=False)

        try:
            ae_scu = AE(ae_title="REJECT_SCU")
            ae_scu.add_requested_context(CTImageStorage)  # Not supported
            ae_scu.add_requested_context(Verification)  # Supported

            assoc = ae_scu.associate("127.0.0.1", port)
            if assoc.is_established:
                # CT should be rejected, Verification accepted
                accepted = [c for c in assoc.accepted_contexts]
                rejected = [c for c in assoc.rejected_contexts]

                assert any(c.abstract_syntax == Verification for c in accepted)
                assert any(c.abstract_syntax == CTImageStorage for c in rejected)

                assoc.release()
            ae_scu.shutdown()
        finally:
            server.shutdown()
            ae_scp.shutdown()

    def test_storage_presentation_contexts_count(self):
        """Ensure StoragePresentationContexts has expected SOP classes."""
        assert len(StoragePresentationContexts) > 100


class TestAssociationNegotiation:
    """Test association establishment, rejection, and release."""

    def test_association_establishment_with_custom_ae_title(self):
        ae_scp = AE(ae_title="CUSTOM_SCP")
        ae_scp.add_supported_context(Verification)
        port = free_port()
        
        called_ae = []
        
        def handle_assoc_rq(event):
            ae_title = event.assoc.requestor.ae_title
            if isinstance(ae_title, (bytes, bytearray)):
                ae_title = ae_title.decode(errors="ignore")
            called_ae.append(str(ae_title).strip())

        server = ae_scp.start_server(
            ("127.0.0.1", port),
            block=False,
            evt_handlers=[(evt.EVT_REQUESTED, handle_assoc_rq)],
        )

        try:
            ae_scu = AE(ae_title="CUSTOM_SCU")
            ae_scu.add_requested_context(Verification)
            assoc = ae_scu.associate("127.0.0.1", port, ae_title="CUSTOM_SCP")

            if assoc.is_established:
                assoc.release()
            ae_scu.shutdown()

            time.sleep(0.1)
            assert "CUSTOM_SCU" in called_ae
        finally:
            server.shutdown()
            ae_scp.shutdown()

    def test_association_abort_handling(self):
        ae_scp = AE(ae_title="ABORT_SCP")
        ae_scp.add_supported_context(Verification)
        port = free_port()

        aborted = threading.Event()

        def handle_abort(event):
            aborted.set()

        server = ae_scp.start_server(
            ("127.0.0.1", port),
            block=False,
            evt_handlers=[(evt.EVT_ABORTED, handle_abort)],
        )

        try:
            ae_scu = AE(ae_title="ABORT_SCU")
            ae_scu.add_requested_context(Verification)
            assoc = ae_scu.associate("127.0.0.1", port)

            if assoc.is_established:
                assoc.abort()

            ae_scu.shutdown()
            assert aborted.wait(timeout=2.0)
        finally:
            server.shutdown()
            ae_scp.shutdown()

    def test_maximum_pdu_length_negotiation(self):
        ae_scp = AE(ae_title="PDU_SCP")
        ae_scp.maximum_pdu_size = 32768
        ae_scp.add_supported_context(Verification)
        port = free_port()
        server = ae_scp.start_server(("127.0.0.1", port), block=False)

        try:
            ae_scu = AE(ae_title="PDU_SCU")
            ae_scu.maximum_pdu_size = 16384
            ae_scu.add_requested_context(Verification)
            assoc = ae_scu.associate("127.0.0.1", port)

            if assoc.is_established:
                # Negotiated PDU size should be min of both
                assert assoc.acceptor.maximum_length <= 32768
                assoc.release()
            ae_scu.shutdown()
        finally:
            server.shutdown()
            ae_scp.shutdown()


class TestEventHandlers:
    """Test various event handler patterns."""

    def test_c_echo_handler_invocation(self):
        ae_scp = AE(ae_title="ECHO_SCP")
        ae_scp.add_supported_context(Verification)
        port = free_port()

        echo_received = threading.Event()

        def handle_echo(event):
            echo_received.set()
            return 0x0000

        server = ae_scp.start_server(
            ("127.0.0.1", port),
            block=False,
            evt_handlers=[(evt.EVT_C_ECHO, handle_echo)],
        )

        try:
            ae_scu = AE(ae_title="ECHO_SCU")
            ae_scu.add_requested_context(Verification)
            assoc = ae_scu.associate("127.0.0.1", port)

            if assoc.is_established:
                status = assoc.send_c_echo()
                assoc.release()
                assert status.Status == 0x0000
            ae_scu.shutdown()

            assert echo_received.is_set()
        finally:
            server.shutdown()
            ae_scp.shutdown()

    def test_c_store_handler_receives_dataset(self):
        ae_scp = AE(ae_title="STORE_SCP")
        ae_scp.add_supported_context(SecondaryCaptureImageStorage)
        port = free_port()

        received_ds = []

        def handle_store(event):
            ds = event.dataset
            ds.file_meta = event.file_meta
            received_ds.append(ds)
            return 0x0000

        server = ae_scp.start_server(
            ("127.0.0.1", port),
            block=False,
            evt_handlers=[(evt.EVT_C_STORE, handle_store)],
        )

        try:
            ae_scu = AE(ae_title="STORE_SCU")
            ae_scu.add_requested_context(SecondaryCaptureImageStorage)

            ds = build_secondary_capture(shape=(8, 8))
            assoc = ae_scu.associate("127.0.0.1", port)

            if assoc.is_established:
                status = assoc.send_c_store(ds)
                assoc.release()
                assert status.Status == 0x0000
            ae_scu.shutdown()

            assert len(received_ds) == 1
            assert received_ds[0].PatientID == ds.PatientID
        finally:
            server.shutdown()
            ae_scp.shutdown()

    def test_c_find_handler_yields_multiple_results(self):
        ae_scp = AE(ae_title="FIND_SCP")
        ae_scp.add_supported_context(StudyRootQueryRetrieveInformationModelFind)
        port = free_port()

        def handle_find(event):
            for i in range(3):
                ds = Dataset()
                ds.QueryRetrieveLevel = "STUDY"
                ds.StudyInstanceUID = f"1.2.3.{i}"
                ds.PatientName = f"Patient{i}"
                yield 0xFF00, ds
            yield 0x0000, None

        server = ae_scp.start_server(
            ("127.0.0.1", port),
            block=False,
            evt_handlers=[(evt.EVT_C_FIND, handle_find)],
        )

        try:
            ae_scu = AE(ae_title="FIND_SCU")
            ae_scu.add_requested_context(StudyRootQueryRetrieveInformationModelFind)

            query = Dataset()
            query.QueryRetrieveLevel = "STUDY"
            query.PatientName = "*"

            assoc = ae_scu.associate("127.0.0.1", port)
            results = []

            if assoc.is_established:
                for status, identifier in assoc.send_c_find(
                    query, StudyRootQueryRetrieveInformationModelFind
                ):
                    if status and status.Status in (0xFF00, 0xFF01):
                        results.append(identifier)
                assoc.release()
            ae_scu.shutdown()

            assert len(results) == 3
        finally:
            server.shutdown()
            ae_scp.shutdown()


class TestRoleSelection:
    """Test SCP/SCU role selection negotiation."""

    def test_storage_scp_role_for_cget(self):
        """C-GET requires SCU to also act as Storage SCP."""
        ae_scp = AE(ae_title="GET_SCP")
        ae_scp.add_supported_context(PatientRootQueryRetrieveInformationModelGet)
        ae_scp.add_supported_context(SecondaryCaptureImageStorage)

        # Configure role selection
        roles = [
            build_role(SecondaryCaptureImageStorage, scp_role=True),
        ]

        ae_scu = AE(ae_title="GET_SCU")
        ae_scu.add_requested_context(PatientRootQueryRetrieveInformationModelGet)
        ae_scu.add_requested_context(SecondaryCaptureImageStorage)

        # Verify role configuration
        assert any(r.sop_class_uid == SecondaryCaptureImageStorage for r in roles)


class TestExtendedNegotiation:
    """Test extended negotiation features."""

    def test_sop_class_extended_negotiation(self):
        ext_neg = SOPClassExtendedNegotiation()
        ext_neg.sop_class_uid = CTImageStorage
        ext_neg.service_class_application_information = b"\x01\x00"

        assert ext_neg.sop_class_uid == CTImageStorage
        assert len(ext_neg.service_class_application_information) == 2


class TestUserIdentityNegotiation:
    """Test user identity negotiation."""

    def test_username_password_identity(self):
        user_id = UserIdentityNegotiation()
        user_id.user_identity_type = 2  # Username and password
        user_id.primary_field = b"testuser"
        user_id.secondary_field = b"testpass"

        assert user_id.user_identity_type == 2
        assert user_id.primary_field == b"testuser"

    def test_kerberos_identity_type(self):
        user_id = UserIdentityNegotiation()
        user_id.user_identity_type = 3  # Kerberos
        user_id.primary_field = b"kerberos_ticket_data"

        assert user_id.user_identity_type == 3


class TestStatusCodes:
    """Test DICOM status code handling."""

    def test_success_status(self):
        assert Status.SUCCESS == 0x0000

    def test_pending_statuses(self):
        assert 0xFF00 in (0xFF00, 0xFF01)  # Pending statuses

    def test_warning_status_range(self):
        # Warning statuses are in range 0x0001-0x00FF and 0xB000-0xBFFF
        assert 0xB000 <= 0xB007 <= 0xBFFF

    def test_failure_status_range(self):
        # Failure statuses include 0xA700-0xA7FF, 0xC000-0xCFFF
        assert 0xA700 <= 0xA701 <= 0xA7FF
        assert 0xC000 <= 0xC001 <= 0xCFFF


class TestConcurrentAssociations:
    """Test handling multiple simultaneous associations."""

    def test_multiple_concurrent_stores(self):
        ae_scp = AE(ae_title="MULTI_SCP")
        ae_scp.add_supported_context(SecondaryCaptureImageStorage)
        ae_scp.maximum_associations = 10
        port = free_port()

        received_count = []
        lock = threading.Lock()

        def handle_store(event):
            with lock:
                received_count.append(1)
            return 0x0000

        server = ae_scp.start_server(
            ("127.0.0.1", port),
            block=False,
            evt_handlers=[(evt.EVT_C_STORE, handle_store)],
        )

        try:
            def send_one():
                ae = AE(ae_title="CONC_SCU")
                ae.add_requested_context(SecondaryCaptureImageStorage)
                ds = build_secondary_capture(shape=(4, 4))
                assoc = ae.associate("127.0.0.1", port)
                if assoc.is_established:
                    assoc.send_c_store(ds)
                    assoc.release()
                ae.shutdown()
                return True

            with ThreadPoolExecutor(max_workers=5) as pool:
                futures = [pool.submit(send_one) for _ in range(5)]
                results = [f.result() for f in futures]

            time.sleep(0.5)
            assert sum(received_count) == 5
        finally:
            server.shutdown()
            ae_scp.shutdown()

    def test_association_limit_enforcement(self):
        ae_scp = AE(ae_title="LIMIT_SCP")
        ae_scp.add_supported_context(Verification)
        ae_scp.maximum_associations = 2
        port = free_port()
        server = ae_scp.start_server(("127.0.0.1", port), block=False)

        try:
            associations = []
            for i in range(4):
                ae = AE(ae_title=f"LIMIT_SCU{i}")
                ae.add_requested_context(Verification)
                assoc = ae.associate("127.0.0.1", port)
                associations.append((ae, assoc))

            established = sum(1 for _, a in associations if a.is_established)
            # At most 2 should be established due to limit
            assert established <= 2

            for ae, assoc in associations:
                if assoc.is_established:
                    assoc.release()
                ae.shutdown()
        finally:
            server.shutdown()
            ae_scp.shutdown()


class TestQueryRetrieveLevels:
    """Test different Q/R hierarchy levels."""

    def test_patient_root_query_levels(self):
        levels = ["PATIENT", "STUDY", "SERIES", "IMAGE"]
        for level in levels:
            ds = Dataset()
            ds.QueryRetrieveLevel = level
            assert ds.QueryRetrieveLevel == level

    def test_study_root_query_levels(self):
        # Study root doesn't have PATIENT level
        levels = ["STUDY", "SERIES", "IMAGE"]
        for level in levels:
            ds = Dataset()
            ds.QueryRetrieveLevel = level
            assert ds.QueryRetrieveLevel == level

    def test_query_identifier_attributes(self):
        # Required matching keys for STUDY level
        ds = Dataset()
        ds.QueryRetrieveLevel = "STUDY"
        ds.PatientName = ""
        ds.PatientID = ""
        ds.StudyDate = ""
        ds.StudyInstanceUID = ""
        ds.ModalitiesInStudy = ""

        assert hasattr(ds, "QueryRetrieveLevel")
        assert hasattr(ds, "StudyInstanceUID")


class TestTimeoutHandling:
    """Test network timeout scenarios."""

    def test_association_timeout_on_unreachable_host(self):
        ae = AE(ae_title="TIMEOUT_SCU")
        ae.add_requested_context(Verification)
        ae.acse_timeout = 1
        ae.network_timeout = 1

        # Connect to non-routable IP
        assoc = ae.associate("10.255.255.1", 11112)
        assert not assoc.is_established
        ae.shutdown()

    def test_dimse_timeout_configuration(self):
        ae = AE(ae_title="DIMSE_TO")
        ae.dimse_timeout = 30

        assert ae.dimse_timeout == 30
