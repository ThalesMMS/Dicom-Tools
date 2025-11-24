#
# test_pynetdicom.py
# Dicom-Tools-py
#
# Confirms the verification server and client complete C-ECHO handshakes successfully.
#
# Thales Matheus Mendonça Santos - November 2025

from DICOM_reencoder.core.network import VerificationServer, send_c_echo


def test_pynetdicom_echo_roundtrip():
    # The verification SCP/SCP pair should complete a C-ECHO handshake
    with VerificationServer() as server:
        status = send_c_echo(server.host, server.port)
        assert status == 0x0000
