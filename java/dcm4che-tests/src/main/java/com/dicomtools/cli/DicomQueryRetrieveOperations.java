package com.dicomtools.cli;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Sequence;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.io.DicomOutputStream;
import org.dcm4che3.net.ApplicationEntity;
import org.dcm4che3.net.Association;
import org.dcm4che3.net.Connection;
import org.dcm4che3.net.Device;
import org.dcm4che3.net.Priority;
import org.dcm4che3.net.TransferCapability;
import org.dcm4che3.net.pdu.AAssociateRQ;
import org.dcm4che3.net.pdu.PresentationContext;
import org.dcm4che3.net.service.BasicCEchoSCP;
import org.dcm4che3.net.service.BasicCStoreSCP;
import org.dcm4che3.net.service.DicomServiceRegistry;
import org.dcm4che3.util.UIDUtils;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;

final class DicomQueryRetrieveOperations {
    private DicomQueryRetrieveOperations() {
    }

    static OperationResult cfind(String host, int port, String callingAet, String calledAet, String level, Map<Integer, String> filters, int timeoutMs) {
        String infoModel = switch (level.toUpperCase()) {
            case "PATIENT" -> UID.PatientRootQueryRetrieveInformationModelFind;
            case "STUDY" -> UID.StudyRootQueryRetrieveInformationModelFind;
            case "SERIES" -> UID.StudyRootQueryRetrieveInformationModelFind;
            case "WORKLIST", "MWL" -> UID.ModalityWorklistInformationModelFind;
            default -> UID.StudyRootQueryRetrieveInformationModelFind;
        };
        Attributes keys = new Attributes();
        keys.setString(Tag.QueryRetrieveLevel, org.dcm4che3.data.VR.CS, level.toUpperCase());
        for (Map.Entry<Integer, String> entry : filters.entrySet()) {
            keys.setString(entry.getKey(), org.dcm4che3.data.VR.LO, entry.getValue());
        }
        Device device = new Device("dicomtools-find-scu");
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
        ae.addTransferCapability(new TransferCapability(null, infoModel,
                TransferCapability.Role.SCU, UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));

        Connection remote = new Connection();
        remote.setHostname(host);
        remote.setPort(port);
        remote.setConnectTimeout(timeoutMs);
        remote.setRequestTimeout(timeoutMs);

        AAssociateRQ rq = new AAssociateRQ();
        rq.setCallingAET(callingAet);
        rq.setCalledAET(calledAet);
        rq.addPresentationContext(new PresentationContext(1, infoModel,
                UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));

        var executor = Executors.newSingleThreadExecutor();
        var scheduler = Executors.newSingleThreadScheduledExecutor();
        device.setExecutor(executor);
        device.setScheduledExecutor(scheduler);

        List<Map<String, Object>> matches = new ArrayList<>();
        Association as = null;
        try {
            as = ae.connect(remote, rq);
            var rsp = as.cfind(infoModel, Priority.NORMAL, keys, UID.ImplicitVRLittleEndian, 10);
            while (rsp.next()) {
                Attributes cmd = rsp.getCommand();
                int status = cmd.getInt(Tag.Status, -1);
                if (org.dcm4che3.net.Status.isPending(status)) {
                    Attributes data = rsp.getDataset();
                    if (data != null) {
                        matches.add(Map.of(
                                "patientName", data.getString(Tag.PatientName, ""),
                                "patientId", data.getString(Tag.PatientID, ""),
                                "studyInstanceUid", data.getString(Tag.StudyInstanceUID, ""),
                                "seriesInstanceUid", data.getString(Tag.SeriesInstanceUID, "")
                        ));
                    }
                } else if (status != org.dcm4che3.net.Status.Success) {
                    return OperationResult.failure("C-FIND failed with status " + Integer.toHexString(status));
                }
            }
            as.release();
            Map<String, Object> meta = new LinkedHashMap<>();
            meta.put("matches", matches);
            meta.put("count", matches.size());
            return OperationResult.success("C-FIND returned " + matches.size() + " matches", meta, java.util.Collections.emptyList());
        } catch (Exception e) {
            return OperationResult.failure("C-FIND error: " + e.getMessage());
        } finally {
            if (as != null && as.isReadyForDataTransfer()) {
                try {
                    as.release();
                } catch (Exception ignored) {
                }
            }
            executor.shutdown();
            scheduler.shutdown();
        }
    }

    static OperationResult cmove(String host, int port, String callingAet, String calledAet,
                                 String moveDestination, Map<Integer, String> filters, int timeoutMs) {
        String infoModel = UID.StudyRootQueryRetrieveInformationModelMove;
        Attributes keys = new Attributes();
        keys.setString(Tag.QueryRetrieveLevel, org.dcm4che3.data.VR.CS, "STUDY");
        for (Map.Entry<Integer, String> entry : filters.entrySet()) {
            keys.setString(entry.getKey(), org.dcm4che3.data.VR.LO, entry.getValue());
        }

        Device device = new Device("dicomtools-move-scu");
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
        ae.addTransferCapability(new TransferCapability(null, infoModel,
                TransferCapability.Role.SCU, UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));

        Connection remote = new Connection();
        remote.setHostname(host);
        remote.setPort(port);
        remote.setConnectTimeout(timeoutMs);
        remote.setRequestTimeout(timeoutMs);

        AAssociateRQ rq = new AAssociateRQ();
        rq.setCallingAET(callingAet);
        rq.setCalledAET(calledAet);
        rq.addPresentationContext(new PresentationContext(1, infoModel,
                UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));

        var executor = Executors.newSingleThreadExecutor();
        var scheduler = Executors.newSingleThreadScheduledExecutor();
        device.setExecutor(executor);
        device.setScheduledExecutor(scheduler);

        Association as = null;
        try {
            as = ae.connect(remote, rq);
            var rsp = as.cmove(infoModel, Priority.NORMAL, keys, moveDestination, UID.ImplicitVRLittleEndian);
            int status = org.dcm4che3.net.Status.Success;
            while (rsp.next()) {
                status = rsp.getCommand().getInt(Tag.Status, -1);
                if (!org.dcm4che3.net.Status.isPending(status) && status != org.dcm4che3.net.Status.Success) {
                    break;
                }
            }
            as.release();
            if (status == org.dcm4che3.net.Status.Success) {
                return OperationResult.success("C-MOVE succeeded for destination " + moveDestination);
            }
            return OperationResult.failure("C-MOVE failed with status " + Integer.toHexString(status));
        } catch (Exception e) {
            return OperationResult.failure("C-MOVE error: " + e.getMessage());
        } finally {
            if (as != null && as.isReadyForDataTransfer()) {
                try {
                    as.release();
                } catch (Exception ignored) {
                }
            }
            executor.shutdown();
            scheduler.shutdown();
        }
    }

    static OperationResult cget(String host, int port, String callingAet, String calledAet,
                                Map<Integer, String> filters, Path outputDir, int timeoutMs) {
        String infoModel = UID.StudyRootQueryRetrieveInformationModelGet;
        Attributes keys = new Attributes();
        keys.setString(Tag.QueryRetrieveLevel, org.dcm4che3.data.VR.CS, "STUDY");
        for (Map.Entry<Integer, String> entry : filters.entrySet()) {
            keys.setString(entry.getKey(), org.dcm4che3.data.VR.LO, entry.getValue());
        }

        Device device = new Device("dicomtools-get-scu");
        ApplicationEntity ae = new ApplicationEntity(callingAet);
        ae.setAssociationInitiator(true);
        ae.setAssociationAcceptor(true);
        Connection conn = new Connection();
        conn.setConnectTimeout(timeoutMs);
        conn.setRequestTimeout(timeoutMs);
        conn.setHostname("127.0.0.1");
        ae.addConnection(conn);
        device.addConnection(conn);
        device.addApplicationEntity(ae);
        ae.addTransferCapability(new TransferCapability(null, infoModel,
                TransferCapability.Role.SCU, UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));
        ae.addTransferCapability(new TransferCapability(null, UID.SecondaryCaptureImageStorage,
                TransferCapability.Role.SCP, UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));

        List<Path> stored = new ArrayList<>();
        DicomServiceRegistry registry = new DicomServiceRegistry();
        registry.addDicomService(new BasicCStoreSCP(UID.SecondaryCaptureImageStorage) {
            @Override
            protected void store(Association as, PresentationContext pc, Attributes rq, org.dcm4che3.net.PDVInputStream data, Attributes rsp) throws IOException {
                Attributes ds;
                try (DicomInputStream dis = new DicomInputStream(data)) {
                    dis.setIncludeBulkData(DicomInputStream.IncludeBulkData.YES);
                    ds = dis.readDataset(-1, -1);
                }
                Files.createDirectories(outputDir);
                String sopInstanceUid = ds.getString(Tag.SOPInstanceUID, UIDUtils.createUID());
                Path out = outputDir.resolve(sopInstanceUid + ".dcm");
                Attributes fmi = ds.createFileMetaInformation(UID.ExplicitVRLittleEndian);
                try (DicomOutputStream dos = new DicomOutputStream(out.toFile())) {
                    dos.writeDataset(fmi, ds);
                }
                synchronized (stored) {
                    stored.add(out);
                }
                rsp.setInt(Tag.Status, org.dcm4che3.data.VR.US, org.dcm4che3.net.Status.Success);
            }
        });
        registry.addDicomService(new BasicCEchoSCP());
        device.setDimseRQHandler(registry);
        device.setAssociationHandler(new org.dcm4che3.net.AssociationHandler());

        Connection remote = new Connection();
        remote.setHostname(host);
        remote.setPort(port);
        remote.setConnectTimeout(timeoutMs);
        remote.setRequestTimeout(timeoutMs);

        AAssociateRQ rq = new AAssociateRQ();
        rq.setCallingAET(callingAet);
        rq.setCalledAET(calledAet);
        rq.addPresentationContext(new PresentationContext(1, infoModel,
                UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));
        rq.addPresentationContext(new PresentationContext(3, UID.SecondaryCaptureImageStorage,
                UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));

        var executor = Executors.newSingleThreadExecutor();
        var scheduler = Executors.newSingleThreadScheduledExecutor();
        device.setExecutor(executor);
        device.setScheduledExecutor(scheduler);

        Association as = null;
        try {
            as = ae.connect(remote, rq);
            var rsp = as.cget(infoModel, Priority.NORMAL, keys, UID.ImplicitVRLittleEndian);
            int status = org.dcm4che3.net.Status.Success;
            while (rsp.next()) {
                status = rsp.getCommand().getInt(Tag.Status, -1);
                if (!org.dcm4che3.net.Status.isPending(status) && status != org.dcm4che3.net.Status.Success) {
                    break;
                }
            }
            as.waitForOutstandingRSP();
            as.release();
            Map<String, Object> meta = new LinkedHashMap<>();
            meta.put("stored", stored.stream().map(Path::toString).toList());
            meta.put("count", stored.size());
            if (status == org.dcm4che3.net.Status.Success) {
                return OperationResult.success("C-GET stored " + stored.size() + " instances", meta, stored);
            }
            return OperationResult.failure("C-GET failed with status " + Integer.toHexString(status));
        } catch (Exception e) {
            return OperationResult.failure("C-GET error: " + e.getMessage());
        } finally {
            if (as != null && as.isReadyForDataTransfer()) {
                try {
                    as.release();
                } catch (Exception ignored) {
                }
            }
            executor.shutdown();
            scheduler.shutdown();
        }
    }

    static OperationResult storageCommit(String host, int port, String callingAet, String calledAet,
                                         List<Path> instances, int timeoutMs) {
        Device device = new Device("dicomtools-stgcmtscu");
        ApplicationEntity ae = new ApplicationEntity(callingAet);
        ae.setAssociationInitiator(true);
        ae.setAssociationAcceptor(true);
        Connection conn = new Connection();
        conn.setConnectTimeout(timeoutMs);
        conn.setRequestTimeout(timeoutMs);
        conn.setHostname("127.0.0.1");
        ae.addConnection(conn);
        device.addConnection(conn);
        device.addApplicationEntity(ae);
        ae.addTransferCapability(new TransferCapability(null, UID.StorageCommitmentPushModel,
                TransferCapability.Role.SCU, UID.ImplicitVRLittleEndian));
        ae.addTransferCapability(new TransferCapability(null, UID.StorageCommitmentPushModel,
                TransferCapability.Role.SCP, UID.ImplicitVRLittleEndian));

        DicomServiceRegistry registry = new DicomServiceRegistry();
        registry.addDicomService(new BasicCEchoSCP());
        device.setDimseRQHandler(registry);
        device.setAssociationHandler(new org.dcm4che3.net.AssociationHandler());

        Connection remote = new Connection();
        remote.setHostname(host);
        remote.setPort(port);
        remote.setConnectTimeout(timeoutMs);
        remote.setRequestTimeout(timeoutMs);

        AAssociateRQ rq = new AAssociateRQ();
        rq.setCallingAET(callingAet);
        rq.setCalledAET(calledAet);
        rq.addPresentationContext(new PresentationContext(1, UID.StorageCommitmentPushModel,
                UID.ImplicitVRLittleEndian));

        var executor = Executors.newSingleThreadExecutor();
        var scheduler = Executors.newSingleThreadScheduledExecutor();
        device.setExecutor(executor);
        device.setScheduledExecutor(scheduler);

        Attributes actionInfo = new Attributes();
        Sequence seq = actionInfo.newSequence(Tag.ReferencedSOPSequence, instances.size());
        for (Path path : instances) {
            try {
                Attributes ds = DicomIOUtils.readDicom(path).dataset();
                Attributes ref = new Attributes();
                ref.setString(Tag.ReferencedSOPClassUID, org.dcm4che3.data.VR.UI, ds.getString(Tag.SOPClassUID, ""));
                ref.setString(Tag.ReferencedSOPInstanceUID, org.dcm4che3.data.VR.UI, ds.getString(Tag.SOPInstanceUID, ""));
                seq.add(ref);
            } catch (IOException ignored) {
            }
        }

        Association as = null;
        try {
            as = ae.connect(remote, rq);
            var rsp = as.naction(UID.StorageCommitmentPushModel, UID.StorageCommitmentPushModelInstance,
                    1, actionInfo, UID.ImplicitVRLittleEndian);
            rsp.next();
            int status = rsp.getCommand().getInt(Tag.Status, -1);
            if (status != org.dcm4che3.net.Status.Success && status != org.dcm4che3.net.Status.Pending) {
                return OperationResult.failure("Storage Commitment N-ACTION failed with status " + Integer.toHexString(status));
            }
            as.waitForOutstandingRSP();
            as.release();
            Map<String, Object> meta = Map.of("referenced", instances.stream().map(Path::toString).toList());
            return OperationResult.success("Storage Commitment requested for " + instances.size() + " instances", meta, java.util.Collections.emptyList());
        } catch (Exception e) {
            return OperationResult.failure("Storage Commitment error: " + e.getMessage());
        } finally {
            if (as != null && as.isReadyForDataTransfer()) {
                try {
                    as.release();
                } catch (Exception ignored) {
                }
            }
            executor.shutdown();
            scheduler.shutdown();
        }
    }
}
