#
# network.py
# Dicom-Tools-py
#
# Implements minimal pynetdicom helpers for verification servers and echo requests.
#
# Thales Matheus Mendonça Santos - November 2025

"""Small helpers for pynetdicom-backed verification."""

import socket
from typing import Optional

from pynetdicom import AE, evt
from pynetdicom.sop_class import Verification


def _pick_free_port() -> int:
    # Bind to port 0 to let the OS choose a free ephemeral port
    sock = socket.socket()
    sock.bind(("", 0))
    _, port = sock.getsockname()
    sock.close()
    return int(port)


class VerificationServer:
    """Context manager that spins up a verification (C-ECHO) SCP."""

    def __init__(self, host: str = "127.0.0.1", port: Optional[int] = None, ae_title: str = "DICOMTOOLS_SCP"):
        self.host = host
        self.port = port or _pick_free_port()
        self.ae_title = ae_title
        self._ae = AE(ae_title=ae_title)
        self._ae.add_supported_context(Verification)
        self._scp = None

    def __enter__(self):
        def handle_echo(event):
            return 0x0000

        # Register a basic handler that simply acknowledges C-ECHO requests
        handlers = [(evt.EVT_C_ECHO, handle_echo)]
        self._scp = self._ae.start_server((self.host, self.port), block=False, evt_handlers=handlers)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._scp:
            self._scp.shutdown()
        self._ae.shutdown()


def send_c_echo(host: str, port: int, *, calling_aet: str = "DICOMTOOLS_SCU", called_aet: str = "DICOMTOOLS_SCP",
                timeout: int = 5) -> int:
    """Send a C-ECHO request and return the Status code."""
    ae = AE(ae_title=calling_aet)
    ae.add_requested_context(Verification)

    ae.acse_timeout = timeout
    ae.dimse_timeout = timeout
    ae.network_timeout = timeout

    assoc = ae.associate(host, port, ae_title=called_aet, ext_neg=None, max_pdu=16382)
    if assoc is None:
        raise RuntimeError("Association was not established")

    try:
        if not assoc.is_established:
            raise RuntimeError("Association was not established")
        status = assoc.send_c_echo()
        if status is None:
            raise RuntimeError("No status returned from C-ECHO")
        return int(status.Status)
    finally:
        if assoc and assoc.is_established:
            # Ensure network resources are cleaned up even when exceptions occur
            assoc.release()
