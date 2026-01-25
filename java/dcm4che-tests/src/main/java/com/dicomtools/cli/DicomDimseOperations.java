package com.dicomtools.cli;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.io.DicomOutputStream;
import org.dcm4che3.net.ApplicationEntity;
import org.dcm4che3.net.Association;
import org.dcm4che3.net.Connection;
import org.dcm4che3.net.DataWriterAdapter;
import org.dcm4che3.net.Device;
import org.dcm4che3.net.IncompatibleConnectionException;
import org.dcm4che3.net.Priority;
import org.dcm4che3.net.TransferCapability;
import org.dcm4che3.net.pdu.AAssociateRQ;
import org.dcm4che3.net.pdu.PresentationContext;
import org.dcm4che3.net.service.BasicCEchoSCP;
import org.dcm4che3.net.service.BasicCStoreSCP;
import org.dcm4che3.net.service.DicomServiceException;
import org.dcm4che3.net.service.DicomServiceRegistry;
import org.dcm4che3.util.UIDUtils;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.GeneralSecurityException;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

final class DicomDimseOperations {
    private DicomDimseOperations() {
    }

    static OperationResult echo(String host, int port, int timeoutMs, String callingAet, String calledAet) {
        Device device = new Device("dicomtools-echo");
        ApplicationEntity ae = new ApplicationEntity(callingAet);
        ae.setAssociationInitiator(true);
        ae.setAssociationAcceptor(false);
        Connection conn = new Connection();
        conn.setConnectTimeout(timeoutMs);
        conn.setHostname("127.0.0.1");
        ae.addConnection(conn);
        device.addConnection(conn);
        device.addApplicationEntity(ae);
        ae.addTransferCapability(new TransferCapability(null, UID.Verification,
                TransferCapability.Role.SCU, UID.ImplicitVRLittleEndian));

        Connection remote = new Connection();
        remote.setHostname(host);
        remote.setPort(port);
        remote.setConnectTimeout(timeoutMs);

        AAssociateRQ rq = new AAssociateRQ();
        rq.setCalledAET(calledAet);
        rq.setCallingAET(callingAet);
        rq.addPresentationContext(new PresentationContext(1, UID.Verification, UID.ImplicitVRLittleEndian));

        var executor = Executors.newSingleThreadExecutor();
        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
        device.setExecutor(executor);
        device.setScheduledExecutor(scheduler);

        Association as = null;
        try {
            as = ae.connect(remote, rq);
            var rsp = as.cecho();
            rsp.next();
            int status = rsp.getCommand().getInt(Tag.Status, -1);
            as.release();
            if (status == 0) {
                return OperationResult.success("C-ECHO succeeded to " + host + ":" + port);
            }
            return OperationResult.failure("C-ECHO failed with status " + status);
        } catch (DicomServiceException e) {
            return OperationResult.failure("C-ECHO DICOM error: " + e.getMessage());
        } catch (IOException | InterruptedException | IncompatibleConnectionException | GeneralSecurityException e) {
            return OperationResult.failure("C-ECHO error: " + e.getMessage());
        } finally {
            if (as != null && as.isReadyForDataTransfer()) {
                try {
                    as.release();
                } catch (Exception ignored) {
                }
            }
            executor.shutdown();
            scheduler.shutdown();
            try {
                executor.awaitTermination(2, TimeUnit.SECONDS);
                scheduler.awaitTermination(2, TimeUnit.SECONDS);
            } catch (InterruptedException ignored) {
                Thread.currentThread().interrupt();
            }
        }
    }

    static OperationResult store(Path input, String host, int port, int timeoutMs, String callingAet, String calledAet) {
        try {
            Attributes dataset = DicomIOUtils.readDicom(input).dataset();
            String sopClass = dataset.getString(Tag.SOPClassUID, UID.SecondaryCaptureImageStorage);
            String sopInstance = dataset.getString(Tag.SOPInstanceUID, UIDUtils.createUID());

            Device device = new Device("dicomtools-store-scu");
            ApplicationEntity ae = new ApplicationEntity(callingAet);
            ae.setAssociationInitiator(true);
            ae.setAssociationAcceptor(false);
            Connection conn = new Connection();
            conn.setConnectTimeout(timeoutMs);
            conn.setRequestTimeout(timeoutMs);
            conn.setHostname("127.0.0.1");
            ae.addConnection(conn);
            device.addConnection(conn);
            device.addApplicationEntity(ae);
            ae.addTransferCapability(new TransferCapability(null, sopClass,
                    TransferCapability.Role.SCU, UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));

            Connection remote = new Connection();
            remote.setHostname(host);
            remote.setPort(port);
            remote.setConnectTimeout(timeoutMs);
            remote.setRequestTimeout(timeoutMs);

            AAssociateRQ rq = new AAssociateRQ();
            rq.setCallingAET(callingAet);
            rq.setCalledAET(calledAet);
            rq.addPresentationContext(new PresentationContext(1, sopClass,
                    UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));

            ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
            var executor = Executors.newSingleThreadExecutor();
            device.setExecutor(executor);
            device.setScheduledExecutor(scheduler);

            Association as = null;
            try {
                as = ae.connect(remote, rq);
                var rsp = as.cstore(sopClass, sopInstance, Priority.NORMAL, new DataWriterAdapter(dataset), UID.ExplicitVRLittleEndian);
                rsp.next();
                int status = rsp.getCommand().getInt(Tag.Status, -1);
                as.release();
                if (status == org.dcm4che3.net.Status.Success) {
                    Map<String, Object> meta = Map.of(
                            "sopClassUid", sopClass,
                            "sopInstanceUid", sopInstance);
                    return OperationResult.success("C-STORE succeeded", meta, java.util.Collections.emptyList());
                }
                return OperationResult.failure("C-STORE failed with status " + Integer.toHexString(status));
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
        } catch (Exception e) {
            return OperationResult.failure("C-STORE error: " + e.getMessage());
        }
    }

    static OperationResult storeSCP(int port, String aet, Path outputDir, int durationSeconds) {
        List<Path> saved = new ArrayList<>();
        Device device = new Device("dicomtools-store-scp");
        ApplicationEntity ae = new ApplicationEntity(aet);
        ae.setAssociationAcceptor(true);
        ae.setAssociationInitiator(false);
        Connection conn = new Connection();
        conn.setPort(port);
        conn.setHostname("127.0.0.1");
        ae.addConnection(conn);
        device.addConnection(conn);
        device.addApplicationEntity(ae);

        DicomServiceRegistry registry = new DicomServiceRegistry();
        registry.addDicomService(new BasicCStoreSCP(UID.SecondaryCaptureImageStorage) {
            @Override
            protected void store(Association as, PresentationContext pc, Attributes rq, org.dcm4che3.net.PDVInputStream data, Attributes rsp) throws IOException {
                Attributes ds;
                try (DicomInputStream dis = new DicomInputStream(data)) {
                    dis.setIncludeBulkData(DicomInputStream.IncludeBulkData.YES);
                    ds = dis.readDataset(-1, -1);
                }
                String sopInstanceUid = ds.getString(Tag.SOPInstanceUID, UIDUtils.createUID());
                Files.createDirectories(outputDir);
                Path out = outputDir.resolve(sopInstanceUid + ".dcm");
                Attributes fmi = ds.createFileMetaInformation(UID.ExplicitVRLittleEndian);
                try (DicomOutputStream dos = new DicomOutputStream(out.toFile())) {
                    dos.writeDataset(fmi, ds);
                }
                synchronized (saved) {
                    saved.add(out);
                }
                rsp.setInt(Tag.Status, org.dcm4che3.data.VR.US, org.dcm4che3.net.Status.Success);
            }
        });
        registry.addDicomService(new BasicCEchoSCP());
        ae.addTransferCapability(new TransferCapability(null, UID.SecondaryCaptureImageStorage,
                TransferCapability.Role.SCP, UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));
        ae.addTransferCapability(new TransferCapability(null, UID.Verification,
                TransferCapability.Role.SCP, UID.ImplicitVRLittleEndian));
        device.setDimseRQHandler(registry);
        device.setAssociationHandler(new org.dcm4che3.net.AssociationHandler());

        ExecutorService executor = Executors.newSingleThreadExecutor();
        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
        device.setExecutor(executor);
        device.setScheduledExecutor(scheduler);

        try {
            device.bindConnections();
            TimeUnit.SECONDS.sleep(Math.max(1, durationSeconds));
        } catch (Exception e) {
            return OperationResult.failure("Store SCP error: " + e.getMessage());
        } finally {
            try {
                device.unbindConnections();
            } catch (Exception ignored) {
            }
            executor.shutdownNow();
            scheduler.shutdownNow();
        }
        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put("savedCount", saved.size());
        meta.put("savedFiles", saved.stream().map(Path::toString).toList());
        return OperationResult.success("Store SCP captured " + saved.size() + " instances", meta, saved);
    }
}
