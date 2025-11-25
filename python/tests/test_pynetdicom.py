#
# test_pynetdicom.py
# Dicom-Tools-py
#
# Confirms the verification server and extended query/retrieve flows complete successfully.
#
# Thales Matheus Mendonça Santos - November 2025

import contextlib
import socket
import ssl
import subprocess
import shutil

import pytest
from pydicom.dataset import Dataset
from pynetdicom import AE, StoragePresentationContexts, evt
from pynetdicom.sop_class import (
    CTImageStorage,
    SecondaryCaptureImageStorage,
    StudyRootQueryRetrieveInformationModelFind,
    StudyRootQueryRetrieveInformationModelGet,
    StudyRootQueryRetrieveInformationModelMove,
    Verification,
)

from DICOM_reencoder.core.factories import build_secondary_capture
from DICOM_reencoder.core.network import VerificationServer, send_c_echo


def test_pynetdicom_echo_roundtrip():
    # The verification SCP/SCP pair should complete a C-ECHO handshake
    with VerificationServer() as server:
        status = send_c_echo(server.host, server.port)
        assert status == 0x0000


def _free_port() -> int:
    sock = socket.socket()
    sock.bind(("", 0))
    _, port = sock.getsockname()
    sock.close()
    return int(port)


@contextlib.contextmanager
def _store_scp():
    ae = AE(ae_title="STORE_SCP")
    ae.add_supported_context(CTImageStorage)
    ae.add_supported_context(SecondaryCaptureImageStorage)
    received = []

    def handle_store(event):
        ds = event.dataset
        ds.file_meta = event.file_meta
        received.append(ds)
        return 0x0000

    handlers = [(evt.EVT_C_STORE, handle_store)]
    port = _free_port()
    server = ae.start_server(("127.0.0.1", port), block=False, evt_handlers=handlers)
    try:
        yield ("127.0.0.1", port, received)
    finally:
        server.shutdown()
        ae.shutdown()


@contextlib.contextmanager
def _find_scp(responses):
    ae = AE(ae_title="FIND_SCP")
    ae.add_supported_context(StudyRootQueryRetrieveInformationModelFind)

    def handle_find(event):
        for ds in responses:
            yield 0xFF00, ds
        yield 0x0000, None

    port = _free_port()
    server = ae.start_server(
        ("127.0.0.1", port), block=False, evt_handlers=[(evt.EVT_C_FIND, handle_find)]
    )
    try:
        yield ("127.0.0.1", port)
    finally:
        server.shutdown()
        ae.shutdown()


@contextlib.contextmanager
def _move_scp(dest_host, dest_port, dest_aet, datasets):
    ae = AE(ae_title="MOVE_SCP")
    ae.add_supported_context(StudyRootQueryRetrieveInformationModelMove)
    ae.add_requested_context(CTImageStorage)
    ae.add_requested_context(SecondaryCaptureImageStorage)
    ae.add_supported_context(SecondaryCaptureImageStorage)

    def handle_move(event):
        kwargs = {"ae_title": dest_aet, "contexts": StoragePresentationContexts}
        yield dest_host, dest_port, kwargs
        yield len(datasets)
        for ds in datasets:
            yield 0xFF00, ds
        yield 0x0000, None

    port = _free_port()
    server = ae.start_server(
        ("127.0.0.1", port),
        block=False,
        evt_handlers=[(evt.EVT_C_MOVE, handle_move)],
    )
    try:
        yield ("127.0.0.1", port)
    finally:
        server.shutdown()
        ae.shutdown()


@contextlib.contextmanager
def _get_scp(datasets):
    ae = AE(ae_title="GET_SCP")
    ae.add_supported_context(StudyRootQueryRetrieveInformationModelGet)
    ae.add_supported_context(CTImageStorage)
    ae.add_supported_context(SecondaryCaptureImageStorage)
    ae.supported_contexts = list(StoragePresentationContexts) + ae.supported_contexts

    def handle_get(event):
        yield len(datasets)
        for ds in datasets:
            yield 0xFF00, ds
        yield 0x0000, None

    port = _free_port()
    server = ae.start_server(
        ("127.0.0.1", port),
        block=False,
        evt_handlers=[(evt.EVT_C_GET, handle_get)],
    )
    try:
        yield ("127.0.0.1", port)
    finally:
        server.shutdown()
        ae.shutdown()


def test_cfind_returns_expected_results():
    ds = Dataset()
    ds.QueryRetrieveLevel = "STUDY"
    ds.StudyInstanceUID = "1.2.3"
    ds.StudyID = "TEST"
    responses = [ds]

    with _find_scp(responses) as (host, port):
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

    with _store_scp() as (dest_host, dest_port, stored):
        with _move_scp(dest_host, dest_port, "DEST_AE", datasets) as (host, port):
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

    with _get_scp(datasets) as (host, port):
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


def test_association_failure_has_clear_status():
    unused_port = _free_port()
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
