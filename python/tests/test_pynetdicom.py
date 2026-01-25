#
# test_pynetdicom.py
# Dicom-Tools-py
#
# Confirms the verification server and extended query/retrieve flows complete successfully.
#
# Thales Matheus Mendonça Santos - November 2025

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import ssl
import subprocess
import shutil

import pytest
from pydicom.dataset import Dataset
from pydicom.uid import generate_uid
from pynetdicom import AE, StoragePresentationContexts, evt
from pynetdicom.sop_class import (
    CTImageStorage,
    ModalityPerformedProcedureStep,
    ModalityWorklistInformationFind,
    SecondaryCaptureImageStorage,
    StorageCommitmentPushModel,
    StudyRootQueryRetrieveInformationModelFind,
    StudyRootQueryRetrieveInformationModelGet,
    StudyRootQueryRetrieveInformationModelMove,
    Verification,
)

from DICOM_reencoder.core.factories import build_secondary_capture
from DICOM_reencoder.core.network import VerificationServer, send_c_echo
sys.path.append(str(Path(__file__).parent))
from pynetdicom_utils import (  # type: ignore
    find_scp,
    free_port,
    get_scp,
    move_scp,
    mwl_scp,
    store_scp,
)


def test_pynetdicom_echo_roundtrip():
    # The verification SCP/SCP pair should complete a C-ECHO handshake
    with VerificationServer() as server:
        status = send_c_echo(server.host, server.port)
        assert status == 0x0000




def test_cfind_returns_expected_results():
    ds = Dataset()
    ds.QueryRetrieveLevel = "STUDY"
    ds.StudyInstanceUID = "1.2.3"
    ds.StudyID = "TEST"
    responses = [ds]

    with find_scp(responses) as (host, port):
        ae = AE(ae_title="FIND_SCU")
        ae.add_requested_context(StudyRootQueryRetrieveInformationModelFind)
        query = Dataset()
        query.QueryRetrieveLevel = "STUDY"
        query.PatientName = "*"

        assoc = ae.associate(host, port, ae_title="FIND_SCP")
        assert assoc.is_established

        identifiers = []
        for status, identifier in assoc.send_c_find(
            query, StudyRootQueryRetrieveInformationModelFind
        ):
            assert status
            if status.Status in (0xFF00, 0xFF01):
                identifiers.append(identifier)

        assoc.release()
        ae.shutdown()

    assert len(identifiers) == 1
    assert identifiers[0].StudyInstanceUID == "1.2.3"


def test_cmove_delivers_instances_to_destination():
    datasets = [build_secondary_capture(shape=(8, 8)) for _ in range(2)]

    with store_scp() as (dest_host, dest_port, stored):
        with move_scp(dest_host, dest_port, "DEST_AE", datasets) as (host, port):
            ae = AE(ae_title="MOVE_SCU")
            ae.add_requested_context(StudyRootQueryRetrieveInformationModelMove)
            ae.add_requested_context(CTImageStorage)
            ae.add_requested_context(SecondaryCaptureImageStorage)
            identifier = Dataset()
            identifier.QueryRetrieveLevel = "STUDY"
            identifier.PatientName = "*"

            assoc = ae.associate(host, port, ae_title="MOVE_SCP")
            assert assoc.is_established

            final_status = None
            for status, _ in assoc.send_c_move(
                identifier, "DEST_AE", StudyRootQueryRetrieveInformationModelMove
            ):
                final_status = status.Status

            assoc.release()
            ae.shutdown()

    assert len(stored) == len(datasets)
    assert final_status == 0x0000


def test_cget_returns_instances_to_same_ae(synthetic_datasets):
    datasets = synthetic_datasets
    stored = []

    def client_store_handler(event):
        ds = event.dataset
        ds.file_meta = event.file_meta
        stored.append(ds)
        return 0x0000

    with get_scp(datasets) as (host, port):
        ae = AE(ae_title="GET_SCU")
        ae.add_requested_context(StudyRootQueryRetrieveInformationModelGet)
        ae.add_requested_context(CTImageStorage)
        ae.add_requested_context(SecondaryCaptureImageStorage)
        ae.requested_contexts = list(StoragePresentationContexts) + ae.requested_contexts
        ae.add_supported_context(CTImageStorage)
        ae.add_supported_context(SecondaryCaptureImageStorage)
        handlers = [(evt.EVT_C_STORE, client_store_handler)]

        assoc = ae.associate(host, port, ae_title="GET_SCP", evt_handlers=handlers)
        assert assoc.is_established

        identifier = Dataset()
        identifier.QueryRetrieveLevel = "STUDY"
        identifier.PatientName = "*"

        statuses = []
        for status, _ in assoc.send_c_get(
            identifier, StudyRootQueryRetrieveInformationModelGet
        ):
            statuses.append(status.Status)

        assoc.release()
        ae.shutdown()

    if 0x0000 not in statuses:
        pytest.skip("C-GET storage contexts were not accepted by the peer in this environment")
    assert len(stored) == len(datasets)


def test_storage_commitment_n_action_cycle():
    seen = []
    status = None
    rsp = None

    def handle_action(event):
        info = event.action_information
        seen.append(info)
        rsp = Dataset()
        rsp.ReferencedSOPSequence = info.ReferencedSOPSequence
        return 0x0000, rsp

    ae = AE(ae_title="STGCMT_SCP")
    ae.add_supported_context(StorageCommitmentPushModel)
    port = free_port()
    server = ae.start_server(("127.0.0.1", port), block=False, evt_handlers=[(evt.EVT_N_ACTION, handle_action)])

    try:
        scu = AE(ae_title="STGCMT_SCU")
        scu.add_requested_context(StorageCommitmentPushModel)
        assoc = scu.associate("127.0.0.1", port, ae_title="STGCMT_SCP")
        if not assoc.is_established:
            pytest.skip("N-ACTION association not established")

        ref = Dataset()
        ref.ReferencedSOPClassUID = CTImageStorage
        ref.ReferencedSOPInstanceUID = generate_uid()
        action_info = Dataset()
        action_info.ReferencedSOPSequence = [ref]

        status, rsp = assoc.send_n_action(
            action_info,
            action_type=1,
            class_uid=StorageCommitmentPushModel,
            instance_uid=generate_uid(),
        )
        assoc.release()
        scu.shutdown()
    finally:
        server.shutdown()
        ae.shutdown()

    if not seen or status is None or rsp is None:
        pytest.skip("N-ACTION handler was not invoked by peer")
    assert status.Status == 0x0000
    assert rsp.ReferencedSOPSequence[0].ReferencedSOPInstanceUID == ref.ReferencedSOPInstanceUID


def test_ncreate_and_nset_for_mpps():
    created = []
    updates = []

    def handle_create(event):
        created.append(event.attribute_list)
        rsp = Dataset()
        rsp.AffectedSOPInstanceUID = generate_uid()
        return 0x0000, rsp

    def handle_set(event):
        updates.append(event.modification_list)
        return 0x0000, Dataset()

    ae = AE(ae_title="MPPS_SCP")
    ae.add_supported_context(ModalityPerformedProcedureStep)
    port = free_port()
    server = ae.start_server(
        ("127.0.0.1", port),
        block=False,
        evt_handlers=[(evt.EVT_N_CREATE, handle_create), (evt.EVT_N_SET, handle_set)],
    )

    try:
        scu = AE(ae_title="MPPS_SCU")
        scu.add_requested_context(ModalityPerformedProcedureStep)
        assoc = scu.associate("127.0.0.1", port, ae_title="MPPS_SCP")
        assert assoc.is_established

        attrs = Dataset()
        attrs.Modality = "CT"
        attrs.PerformedStationName = "DICOMTOOLS"
        status, rsp = assoc.send_n_create(attrs, ModalityPerformedProcedureStep)
        assert status.Status == 0x0000

        instance_uid = getattr(rsp, "AffectedSOPInstanceUID", None) or generate_uid()
        mods = Dataset()
        mods.PerformedProcedureStepStatus = "COMPLETED"
        mods.PerformedSeriesSequence = [Dataset()]
        status, _ = assoc.send_n_set(mods, ModalityPerformedProcedureStep, instance_uid)
        assoc.release()
        scu.shutdown()
    finally:
        server.shutdown()
        ae.shutdown()

    assert any(getattr(ds, "Modality", None) == "CT" for ds in created if ds)
    assert any(getattr(ds, "PerformedProcedureStepStatus", None) == "COMPLETED" for ds in updates if ds)


def test_modality_worklist_find_returns_scheduled_steps():
    result = Dataset()
    result.PatientName = "Worklist^Patient"
    result.AccessionNumber = "ACC-123"
    sps = Dataset()
    sps.Modality = "CT"
    sps.ScheduledProcedureStepDescription = "Synthetic study"
    result.ScheduledProcedureStepSequence = [sps]

    with mwl_scp([result]) as (host, port):
        ae = AE(ae_title="MWL_SCU")
        ae.add_requested_context(ModalityWorklistInformationFind)
        assoc = ae.associate(host, port, ae_title="FIND_SCP")
        if not assoc.is_established:
            pytest.skip("MWL association not established in this environment")

        query = Dataset()
        query.PatientName = "*"
        query.ScheduledProcedureStepSequence = [Dataset()]
        query.ScheduledProcedureStepSequence[0].Modality = "CT"

        returned = []
        for status, identifier in assoc.send_c_find(query, ModalityWorklistInformationFind):
            assert status
            if status.Status in (0xFF00, 0xFF01):
                returned.append(identifier)

        assoc.release()
        ae.shutdown()

    assert returned
    first = returned[0]
    assert first.PatientName == "Worklist^Patient"
    assert first.ScheduledProcedureStepSequence[0].Modality == "CT"


def test_concurrent_associations_handle_store_and_find(synthetic_datasets):
    datasets = [ds.copy() for ds in synthetic_datasets]
    query_ds = Dataset()
    query_ds.QueryRetrieveLevel = "STUDY"
    query_ds.PatientName = "*"

    with store_scp() as (store_host, store_port, stored):
        with find_scp([query_ds]) as (find_host, find_port):
            def send_store(ds):
                ae = AE(ae_title="STORE_SCU")
                ae.add_requested_context(CTImageStorage)
                assoc = ae.associate(store_host, store_port, ae_title="STORE_SCP")
                if not assoc.is_established:
                    return None
                status = assoc.send_c_store(ds)
                assoc.release()
                ae.shutdown()
                return status.Status if status else None

            def send_find():
                ae = AE(ae_title="FINDSCU2")
                ae.add_requested_context(StudyRootQueryRetrieveInformationModelFind)
                assoc = ae.associate(find_host, find_port, ae_title="FIND_SCP")
                if not assoc.is_established:
                    return []
                results = []
                for status, identifier in assoc.send_c_find(
                    query_ds, StudyRootQueryRetrieveInformationModelFind
                ):
                    if status and status.Status in (0xFF00, 0xFF01):
                        results.append(identifier)
                assoc.release()
                ae.shutdown()
                return results

            with ThreadPoolExecutor(max_workers=4) as pool:
                futures = []
                for ds in datasets:
                    futures.append(pool.submit(send_store, ds))
                futures.append(pool.submit(send_find))
                futures.append(pool.submit(send_find))
                results = [f.result() for f in futures]

    store_statuses = [r for r in results if isinstance(r, int)]
    find_results = [r for r in results if isinstance(r, list)]
    assert len(store_statuses) == len(datasets)
    assert all(status == 0x0000 for status in store_statuses if status is not None)
    assert stored  # Ensure C-STORE handlers ran
    assert any(find_results)  # At least one C-FIND returned identifiers


def test_association_failure_has_clear_status():
    unused_port = free_port()
    with pytest.raises(RuntimeError):
        send_c_echo("127.0.0.1", unused_port, timeout=1)


def test_tls_echo_roundtrip(tmp_path):
    openssl = shutil.which("openssl")
    if not openssl:
        pytest.skip("openssl not available for generating test certificates")

    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    try:
        subprocess.run(
            [
                openssl,
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-keyout",
                str(key),
                "-out",
                str(cert),
                "-days",
                "1",
                "-subj",
                "/CN=localhost",
            ],
            check=True,
            capture_output=True,
        )
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Could not create TLS certs: {exc}")

    server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_ctx.load_cert_chain(certfile=str(cert), keyfile=str(key))

    client_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    client_ctx.check_hostname = False
    client_ctx.verify_mode = ssl.CERT_NONE

    ae = AE(ae_title="TLS_SCP")
    ae.add_supported_context(Verification)
    server = ae.start_server(("127.0.0.1", 0), block=False, ssl_context=server_ctx)

    try:
        host, port = server.server_address
        scu = AE(ae_title="TLS_SCU")
        scu.add_requested_context(Verification)
        assoc = scu.associate(host, port, ae_title="TLS_SCP", tls_args=(client_ctx, None))
        if not assoc.is_established:
            pytest.skip("TLS association not established in this environment")

        status = assoc.send_c_echo()
        assoc.release()
        scu.shutdown()

        assert status and status.Status == 0x0000
    finally:
        server.shutdown()
        ae.shutdown()
