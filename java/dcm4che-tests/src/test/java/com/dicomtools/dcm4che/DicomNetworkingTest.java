package com.dicomtools.dcm4che;

import com.dicomtools.cli.DicomOperations;
import com.dicomtools.cli.OperationResult;
import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.data.VR;
import org.dcm4che3.net.ApplicationEntity;
import org.dcm4che3.net.Association;
import org.dcm4che3.net.Connection;
import org.dcm4che3.net.Device;
import org.dcm4che3.net.TransferCapability;
import org.dcm4che3.net.pdu.PresentationContext;
import org.dcm4che3.net.Status;
import org.dcm4che3.net.DataWriterAdapter;
import org.dcm4che3.net.pdu.AAssociateRQ;
import org.dcm4che3.util.UIDUtils;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;

import java.io.IOException;
import java.net.ServerSocket;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class DicomNetworkingTest {

    @Test
    @Timeout(value = 15)
    void cEchoSucceedsAgainstLocalScp() throws Exception {
        int port = findOpenPort();
        try (LocalDicomServer server = LocalDicomServer.createEchoOnly("ECHO-SCP", port)) {
            OperationResult result = DicomOperations.echo("127.0.0.1", port, 2000, "ECHO-SCU", "ECHO-SCP");
            assertTrue(result.isSuccess(), "C-ECHO should succeed against local SCP");
        }
    }

    @Test
    @Timeout(value = 20)
    void cStoreRoundTripTransfersDataset() throws Exception {
        int port = findOpenPort();
        Attributes dataset = syntheticSecondaryCapture();
        try (LocalDicomServer server = LocalDicomServer.createEchoAndStore("STORE-SCP", port, dataset.getString(Tag.SOPClassUID))) {
            sendStore(dataset, port, "STORE-SCU", "STORE-SCP");
            List<Attributes> received = server.receivedInstances();
            assertEquals(1, received.size(), "SCP should capture one instance");
            Attributes stored = received.get(0);
            assertEquals(dataset.getString(Tag.SOPInstanceUID), stored.getString(Tag.SOPInstanceUID));
            assertEquals(dataset.getString(Tag.PatientName), stored.getString(Tag.PatientName));
            assertArrayEquals(dataset.getBytes(Tag.PixelData), stored.getBytes(Tag.PixelData));
            assertEquals(dataset.getInt(Tag.Rows, 0), stored.getInt(Tag.Rows, 0));
            assertEquals(dataset.getInt(Tag.Columns, 0), stored.getInt(Tag.Columns, 0));
        }
    }

    private void sendStore(Attributes dataset, int port, String callingAet, String calledAet) throws Exception {
        Device device = new Device("dicomtools-store-scu");
        ApplicationEntity ae = new ApplicationEntity(callingAet);
        ae.setAssociationInitiator(true);
        ae.setAssociationAcceptor(false);
        Connection conn = new Connection();
        conn.setConnectTimeout(2000);
        conn.setHostname("127.0.0.1");
        ae.addConnection(conn);
        device.addConnection(conn);
        device.addApplicationEntity(ae);
        ae.addTransferCapability(new TransferCapability(null, dataset.getString(Tag.SOPClassUID),
                TransferCapability.Role.SCU, UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));

        Connection remote = new Connection();
        remote.setHostname("127.0.0.1");
        remote.setPort(port);
        remote.setConnectTimeout(2000);
        remote.setRequestTimeout(2000);

        AAssociateRQ rq = new AAssociateRQ();
        rq.setCallingAET(callingAet);
        rq.setCalledAET(calledAet);
        rq.addPresentationContext(new PresentationContext(1, dataset.getString(Tag.SOPClassUID),
                UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));

        ExecutorService executor = Executors.newSingleThreadExecutor();
        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
        device.setExecutor(executor);
        device.setScheduledExecutor(scheduler);

        Association as = null;
        try {
            as = ae.connect(remote, rq);
            var rsp = as.cstore(dataset.getString(Tag.SOPClassUID), dataset.getString(Tag.SOPInstanceUID),
                    0, new DataWriterAdapter(dataset), UID.ExplicitVRLittleEndian);
            rsp.next();
            assertEquals(Status.Success, rsp.getCommand().getInt(Tag.Status, -1), "C-STORE response status");
            as.release();
        } finally {
            if (as != null && as.isReadyForDataTransfer()) {
                try {
                    as.release();
                } catch (Exception ignored) {
                }
            }
            executor.shutdown();
            scheduler.shutdown();
            executor.awaitTermination(2, TimeUnit.SECONDS);
            scheduler.awaitTermination(2, TimeUnit.SECONDS);
        }
    }

    private Attributes syntheticSecondaryCapture() {
        Attributes attrs = new Attributes();
        attrs.setString(Tag.SOPClassUID, VR.UI, UID.SecondaryCaptureImageStorage);
        attrs.setString(Tag.SOPInstanceUID, VR.UI, UIDUtils.createUID());
        attrs.setString(Tag.StudyInstanceUID, VR.UI, UIDUtils.createUID());
        attrs.setString(Tag.SeriesInstanceUID, VR.UI, UIDUtils.createUID());
        attrs.setString(Tag.Modality, VR.CS, "OT");
        attrs.setString(Tag.PatientName, VR.PN, "NETWORK^TEST");
        attrs.setString(Tag.PatientID, VR.LO, "NET-001");
        attrs.setInt(Tag.SamplesPerPixel, VR.US, 1);
        attrs.setString(Tag.PhotometricInterpretation, VR.CS, "MONOCHROME2");
        attrs.setInt(Tag.Rows, VR.US, 2);
        attrs.setInt(Tag.Columns, VR.US, 2);
        attrs.setInt(Tag.BitsAllocated, VR.US, 16);
        attrs.setInt(Tag.BitsStored, VR.US, 12);
        attrs.setInt(Tag.HighBit, VR.US, 11);
        attrs.setInt(Tag.PixelRepresentation, VR.US, 0);
        short[] pixels = new short[]{10, 20, 30, 40};
        byte[] buffer = new byte[pixels.length * 2];
        ByteBuffer.wrap(buffer).order(ByteOrder.LITTLE_ENDIAN).asShortBuffer().put(pixels);
        attrs.setBytes(Tag.PixelData, VR.OW, buffer);
        return attrs;
    }

    private static int findOpenPort() throws IOException {
        try (ServerSocket socket = new ServerSocket(0)) {
            return socket.getLocalPort();
        }
    }
}
