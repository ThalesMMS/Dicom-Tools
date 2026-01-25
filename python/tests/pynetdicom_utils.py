#
# pynetdicom_utils.py
# Shared helpers for pynetdicom tests.
#

from __future__ import annotations

import contextlib
import socket
from typing import Iterable, Iterator, Tuple

from pydicom.dataset import Dataset
from pynetdicom import AE, StoragePresentationContexts, evt
from pynetdicom.sop_class import (
    CTImageStorage,
    ModalityWorklistInformationFind,
    SecondaryCaptureImageStorage,
    StudyRootQueryRetrieveInformationModelFind,
    StudyRootQueryRetrieveInformationModelGet,
    StudyRootQueryRetrieveInformationModelMove,
)


def free_port() -> int:
    sock = socket.socket()
    sock.bind(("", 0))
    _, port = sock.getsockname()
    sock.close()
    return int(port)


@contextlib.contextmanager
def store_scp() -> Iterator[Tuple[str, int, list[Dataset]]]:
    ae = AE(ae_title="STORE_SCP")
    ae.add_supported_context(CTImageStorage)
    ae.add_supported_context(SecondaryCaptureImageStorage)
    received: list[Dataset] = []

    def handle_store(event):
        ds = event.dataset
        ds.file_meta = event.file_meta
        received.append(ds)
        return 0x0000

    handlers = [(evt.EVT_C_STORE, handle_store)]
    port = free_port()
    server = ae.start_server(("127.0.0.1", port), block=False, evt_handlers=handlers)
    try:
        yield ("127.0.0.1", port, received)
    finally:
        server.shutdown()
        ae.shutdown()


@contextlib.contextmanager
def find_scp(responses: Iterable[Dataset], model=StudyRootQueryRetrieveInformationModelFind):
    ae = AE(ae_title="FIND_SCP")
    ae.add_supported_context(model)

    def handle_find(event):
        for ds in responses:
            yield 0xFF00, ds
        yield 0x0000, None

    port = free_port()
    server = ae.start_server(
        ("127.0.0.1", port), block=False, evt_handlers=[(evt.EVT_C_FIND, handle_find)]
    )
    try:
        yield ("127.0.0.1", port)
    finally:
        server.shutdown()
        ae.shutdown()


@contextlib.contextmanager
def move_scp(dest_host: str, dest_port: int, dest_aet: str, datasets: list[Dataset]):
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

    port = free_port()
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
def get_scp(datasets: list[Dataset]):
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

    port = free_port()
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


@contextlib.contextmanager
def mwl_scp(responses: Iterable[Dataset]):
    with find_scp(responses, model=ModalityWorklistInformationFind) as info:
        yield info
