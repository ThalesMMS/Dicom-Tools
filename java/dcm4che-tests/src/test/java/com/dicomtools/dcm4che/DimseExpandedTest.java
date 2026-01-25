package com.dicomtools.dcm4che;

import com.dicomtools.cli.DicomOperations;
import com.dicomtools.cli.OperationResult;
import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.data.VR;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.net.ApplicationEntity;
import org.dcm4che3.net.Association;
import org.dcm4che3.net.Connection;
import org.dcm4che3.net.Device;
import org.dcm4che3.net.Priority;
import org.dcm4che3.net.Status;
import org.dcm4che3.net.TransferCapability;
import org.dcm4che3.net.pdu.AAssociateRQ;
import org.dcm4che3.net.pdu.PresentationContext;
import org.dcm4che3.net.service.BasicCFindSCP;
import org.dcm4che3.net.service.BasicCGetSCP;
import org.dcm4che3.net.service.BasicCMoveSCP;
import org.dcm4che3.net.service.BasicCStoreSCP;
import org.dcm4che3.net.service.BasicQueryTask;
import org.dcm4che3.net.service.BasicRetrieveTask;
import org.dcm4che3.net.service.DicomServiceRegistry;
import org.dcm4che3.net.service.InstanceLocator;
import org.dcm4che3.net.service.QueryTask;
import org.dcm4che3.net.service.RetrieveTask;
import org.dcm4che3.util.UIDUtils;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

@org.junit.jupiter.api.Tag("integration")
class DimseExpandedTest {

    @TempDir
    Path tempDir;

    private final List<AutoCloseable> resources = new ArrayList<>();

    @AfterEach
    void cleanup() throws Exception {
        Collections.reverse(resources);
        for (AutoCloseable c : resources) {
            try {
                c.close();
            } catch (Exception ignored) {
            }
        }
        resources.clear();
    }

    @Test
    void storeScuSendsToLocalScp() throws Exception {
        int port = openPort();
        Attributes ds = readDicom(TestData.sampleDicom());
        try (LocalDicomServer server = LocalDicomServer.createEchoAndStore("SCP", port, ds.getString(Tag.SOPClassUID))) {
            OperationResult result = DicomOperations.store(TestData.sampleDicom(), "127.0.0.1", port, 2000, "SCU", "SCP");
            assertTrue(result.isSuccess());
            TimeUnit.MILLISECONDS.sleep(100);
            assertEquals(1, server.receivedInstances().size());
            Attributes stored = server.receivedInstances().get(0);
            assertEquals(ds.getString(Tag.SOPInstanceUID), stored.getString(Tag.SOPInstanceUID));
        }
    }

    @Test
    void cfindReturnsMatches() throws Exception {
        int port = openPort();
        Attributes ds = minimalStudy("FIND^PATIENT");
        QueryRetrieveServer server = QueryRetrieveServer.start(List.of(ds), port, "FIND-SCP", Map.of());
        resources.add(server);

        OperationResult result = DicomOperations.cfind("127.0.0.1", port, "FIND-SCU", "FIND-SCP", "STUDY",
                Map.of(Tag.PatientName, "FIND^PATIENT"), 2000);
        assertTrue(result.isSuccess());
        Map<String, Object> meta = result.getMetadata();
        assertEquals(1, meta.get("count"));
    }

    @Test
    void cmoveDeliversToDestinationStore() throws Exception {
        int storePort = openPort();
        try (LocalDicomServer destStore = LocalDicomServer.createEchoAndStore("DEST", storePort, UID.SecondaryCaptureImageStorage)) {
            int port = openPort();
            Attributes ds = minimalStudy("MOVE^PAT");
            ds.setString(Tag.SOPClassUID, VR.UI, UID.SecondaryCaptureImageStorage);
            QueryRetrieveServer server = QueryRetrieveServer.start(List.of(ds), port, "MOVE-SCP", Map.of("DEST", new QueryRetrieveServer.Destination("127.0.0.1", storePort, "DEST")));
            resources.add(server);

            OperationResult move = DicomOperations.cmove("127.0.0.1", port, "MOVE-SCU", "MOVE-SCP", "DEST",
                    Map.of(Tag.PatientName, "MOVE^PAT"), 3000);
            assertTrue(move.isSuccess());
            TimeUnit.MILLISECONDS.sleep(200);
            assertEquals(1, destStore.receivedInstances().size());
        }
    }

    @Test
    @Disabled("C-GET server handshake unstable in lightweight test harness")
    void cgetStoresLocally() throws Exception {
        int port = openPort();
        Attributes ds = minimalStudy("GET^PAT");
        ds.setString(Tag.SOPClassUID, VR.UI, UID.SecondaryCaptureImageStorage);
        QueryRetrieveServer server = QueryRetrieveServer.start(List.of(ds), port, "GET-SCP", Map.of());
        resources.add(server);

        OperationResult got = DicomOperations.cget("127.0.0.1", port, "GET-SCU", "GET-SCP",
                Map.of(Tag.PatientName, "GET^PAT"), tempDir, 3000);
        assertTrue(got.isSuccess());
        assertEquals(1, ((Number) got.getMetadata().get("count")).intValue());
        assertEquals(1, got.getOutputFiles().size());
        assertTrue(Files.exists(got.getOutputFiles().get(0)));
    }

    @Test
    void storageCommitmentSucceeds() throws Exception {
        int port = openPort();
        try (StorageCommitmentServer scp = StorageCommitmentServer.start(port)) {
            OperationResult result = DicomOperations.storageCommit("127.0.0.1", port, "STGCMT-SCU", "STGCMT-SCP",
                    List.of(TestData.sampleDicom()), 2000);
            assertTrue(result.isSuccess());
        }
    }

    private static int openPort() throws IOException {
        try (java.net.ServerSocket socket = new java.net.ServerSocket(0)) {
            return socket.getLocalPort();
        }
    }

    private Attributes minimalStudy(String patientName) throws IOException {
        Attributes attrs = readDicom(TestData.sampleDicom());
        attrs.setString(Tag.PatientName, VR.PN, patientName);
        attrs.setString(Tag.PatientID, VR.LO, UIDUtils.createUID());
        attrs.setString(Tag.StudyInstanceUID, VR.UI, UIDUtils.createUID());
        attrs.setString(Tag.SeriesInstanceUID, VR.UI, UIDUtils.createUID());
        attrs.setString(Tag.SOPInstanceUID, VR.UI, UIDUtils.createUID());
        attrs.setString(Tag.QueryRetrieveLevel, VR.CS, "STUDY");
        return attrs;
    }

    private Attributes readDicom(Path path) throws IOException {
        try (DicomInputStream dis = new DicomInputStream(path.toFile())) {
            dis.readFileMetaInformation();
            return dis.readDataset(-1, -1);
        }
    }

    static final class QueryRetrieveServer implements AutoCloseable {
        private final Device device;
        private final ExecutorService executor;
        private final ScheduledExecutorService scheduler;
        private final List<AutoCloseable> extraClosers;

        private QueryRetrieveServer(Device device, ExecutorService executor, ScheduledExecutorService scheduler, List<AutoCloseable> closers) {
            this.device = device;
            this.executor = executor;
            this.scheduler = scheduler;
            this.extraClosers = closers;
        }

        static QueryRetrieveServer start(List<Attributes> instances, int port, String aet, Map<String, Destination> destinations) throws Exception {
            List<AutoCloseable> closers = new ArrayList<>();
            Device device = new Device("qr-test-scp");
            ApplicationEntity ae = new ApplicationEntity(aet);
            ae.setAssociationAcceptor(true);
            Connection conn = new Connection();
            conn.setPort(port);
            conn.setHostname("127.0.0.1");
            ae.addConnection(conn);
            device.addConnection(conn);
            device.addApplicationEntity(ae);

            DicomServiceRegistry registry = new DicomServiceRegistry();
            registry.addDicomService(new BasicCFindSCP(UID.StudyRootQueryRetrieveInformationModelFind) {
                @Override
                protected QueryTask calculateMatches(Association as, PresentationContext pc, Attributes rq, Attributes keys) {
                    Iterator<Attributes> iterator = instances.iterator();
                    return new BasicQueryTask(as, pc, rq, keys) {
                        @Override
                        protected Attributes nextMatch() {
                            if (!iterator.hasNext()) return null;
                            Attributes match = new Attributes(iterator.next());
                            return match;
                        }
                    };
                }
            });

            registry.addDicomService(new BasicCGetSCP(UID.StudyRootQueryRetrieveInformationModelGet) {
                @Override
                protected RetrieveTask calculateMatches(Association as, PresentationContext pc, Attributes rq, Attributes keys) {
                    List<InstanceLocator> locators = instances.stream()
                            .map(attr -> {
                                InstanceLocator loc = new InstanceLocator(attr.getString(Tag.SOPClassUID), attr.getString(Tag.SOPInstanceUID),
                                        UID.ExplicitVRLittleEndian, "");
                                loc.setObject(attr);
                                return loc;
                            }).collect(Collectors.toList());
                    return new BasicRetrieveTask<>(org.dcm4che3.net.Dimse.C_GET_RQ, as, pc, rq, locators, as) {
                        @Override
                        protected org.dcm4che3.net.DataWriter createDataWriter(InstanceLocator inst, String tsuid) {
                            Attributes ds = (Attributes) inst.getObject();
                            return (out, transferSyntax) -> {
                                try (var dos = new org.dcm4che3.io.DicomOutputStream(out, transferSyntax)) {
                                    dos.writeDataset(ds.createFileMetaInformation(transferSyntax), ds);
                                }
                            };
                        }
                    };
                }
            });

            registry.addDicomService(new BasicCMoveSCP(UID.StudyRootQueryRetrieveInformationModelMove) {
                @Override
                protected RetrieveTask calculateMatches(Association as, PresentationContext pc, Attributes rq, Attributes keys) {
                    String destAet = rq.getString(Tag.MoveDestination, "");
                    Destination dest = destinations.get(destAet);
                    if (dest == null) return null;
                    List<InstanceLocator> locators = instances.stream()
                            .map(attr -> {
                                InstanceLocator loc = new InstanceLocator(attr.getString(Tag.SOPClassUID), attr.getString(Tag.SOPInstanceUID),
                                        UID.ExplicitVRLittleEndian, "");
                                loc.setObject(attr);
                                return loc;
                            }).collect(Collectors.toList());

                    try {
                        Association storeAs = connectStoreAssociation(dest);
                        return new BasicRetrieveTask<>(org.dcm4che3.net.Dimse.C_MOVE_RQ, as, pc, rq, locators, storeAs) {
                            @Override
                            protected org.dcm4che3.net.DataWriter createDataWriter(InstanceLocator inst, String tsuid) {
                                Attributes ds = (Attributes) inst.getObject();
                                return (out, transferSyntax) -> {
                                    try (var dos = new org.dcm4che3.io.DicomOutputStream(out, transferSyntax)) {
                                        dos.writeDataset(ds.createFileMetaInformation(transferSyntax), ds);
                                    }
                                };
                            }
                        };
                    } catch (Exception e) {
                        return null;
                    }
                }

                private Association connectStoreAssociation(Destination dest) throws IOException, InterruptedException, org.dcm4che3.net.IncompatibleConnectionException, java.security.GeneralSecurityException {
                    Device storeDevice = new Device("qr-store-scu");
                    ApplicationEntity storeAe = new ApplicationEntity("MOVE-SCP");
                    storeAe.setAssociationInitiator(true);
                    storeAe.setAssociationAcceptor(false);
                    Connection local = new Connection();
                    local.setHostname("127.0.0.1");
                    storeAe.addConnection(local);
                    storeDevice.addConnection(local);
                    storeDevice.addApplicationEntity(storeAe);
                    storeAe.addTransferCapability(new TransferCapability(null, UID.SecondaryCaptureImageStorage,
                            TransferCapability.Role.SCU, UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));

                    Connection remote = new Connection();
                    remote.setHostname(dest.host());
                    remote.setPort(dest.port());
                    remote.setConnectTimeout(2000);
                    remote.setRequestTimeout(2000);

                    AAssociateRQ rq = new AAssociateRQ();
                    rq.setCallingAET("MOVE-SCP");
                    rq.setCalledAET(dest.aet());
                    rq.addPresentationContext(new PresentationContext(11, UID.SecondaryCaptureImageStorage,
                            UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));
                    ExecutorService ex = Executors.newSingleThreadExecutor();
                    ScheduledExecutorService sch = Executors.newSingleThreadScheduledExecutor();
                    storeDevice.setExecutor(ex);
                    storeDevice.setScheduledExecutor(sch);
                    Association as = storeAe.connect(remote, rq);
                    // ensure executors are stopped on close
                    closers.add(() -> {
                        try {
                            if (as.isReadyForDataTransfer()) as.release();
                        } catch (Exception ignored) {
                        }
                        ex.shutdown();
                        sch.shutdown();
                    });
                    return as;
                }
            });

            registry.addDicomService(new BasicCStoreSCP(UID.SecondaryCaptureImageStorage) {
                @Override
                protected void store(Association as, PresentationContext pc, Attributes rq, org.dcm4che3.net.PDVInputStream data, Attributes rsp) throws IOException {
                    rsp.setInt(Tag.Status, VR.US, Status.Success);
                }
            });

            registry.addDicomService(new org.dcm4che3.net.service.BasicCEchoSCP());
            ae.addTransferCapability(new TransferCapability(null, UID.StudyRootQueryRetrieveInformationModelFind,
                    TransferCapability.Role.SCP, UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));
            ae.addTransferCapability(new TransferCapability(null, UID.StudyRootQueryRetrieveInformationModelGet,
                    TransferCapability.Role.SCP, UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));
            ae.addTransferCapability(new TransferCapability(null, UID.StudyRootQueryRetrieveInformationModelMove,
                    TransferCapability.Role.SCP, UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));
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
            device.bindConnections();
            return new QueryRetrieveServer(device, executor, scheduler, closers);
        }

        @Override
        public void close() {
            try {
                device.unbindConnections();
            } catch (Exception ignored) {
            }
            executor.shutdownNow();
            scheduler.shutdownNow();
            for (AutoCloseable c : extraClosers) {
                try {
                    c.close();
                } catch (Exception ignored) {
                }
            }
        }

        record Destination(String host, int port, String aet) {
        }
    }

    static final class StorageCommitmentServer implements AutoCloseable {
        private final Device device;
        private final ExecutorService executor;
        private final ScheduledExecutorService scheduler;

        private StorageCommitmentServer(Device device, ExecutorService executor, ScheduledExecutorService scheduler) {
            this.device = device;
            this.executor = executor;
            this.scheduler = scheduler;
        }

        static StorageCommitmentServer start(int port) throws Exception {
            Device device = new Device("stgcmtscp");
            ApplicationEntity ae = new ApplicationEntity("STGCMT-SCP");
            ae.setAssociationAcceptor(true);
            Connection conn = new Connection();
            conn.setHostname("127.0.0.1");
            conn.setPort(port);
            ae.addConnection(conn);
            device.addConnection(conn);
            device.addApplicationEntity(ae);

            DicomServiceRegistry registry = new DicomServiceRegistry();
            registry.addDicomService(new org.dcm4che3.net.service.AbstractDicomService(UID.StorageCommitmentPushModel) {
                @Override
                public void onDimseRQ(Association as, PresentationContext pc, org.dcm4che3.net.Dimse dimse, Attributes cmd, Attributes data) throws IOException {
                    if (dimse == org.dcm4che3.net.Dimse.N_ACTION_RQ) {
                        Attributes rsp = org.dcm4che3.net.Commands.mkNActionRSP(cmd, Status.Success);
                        as.tryWriteDimseRSP(pc, rsp);
                    } else if (dimse == org.dcm4che3.net.Dimse.N_EVENT_REPORT_RQ) {
                        Attributes rsp = org.dcm4che3.net.Commands.mkNEventReportRSP(cmd, Status.Success);
                        as.tryWriteDimseRSP(pc, rsp);
                    } else {
                        throw new org.dcm4che3.net.service.DicomServiceException(Status.UnrecognizedOperation);
                    }
                }
            });
            registry.addDicomService(new org.dcm4che3.net.service.BasicCEchoSCP());
            ae.addTransferCapability(new TransferCapability(null, UID.StorageCommitmentPushModel,
                    TransferCapability.Role.SCP, UID.ImplicitVRLittleEndian));
            ae.addTransferCapability(new TransferCapability(null, UID.Verification,
                    TransferCapability.Role.SCP, UID.ImplicitVRLittleEndian));

            device.setAssociationHandler(new org.dcm4che3.net.AssociationHandler());
            device.setDimseRQHandler(registry);
            ExecutorService executor = Executors.newSingleThreadExecutor();
            ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
            device.setExecutor(executor);
            device.setScheduledExecutor(scheduler);
            device.bindConnections();
            return new StorageCommitmentServer(device, executor, scheduler);
        }

        @Override
        public void close() {
            try {
                device.unbindConnections();
            } catch (Exception ignored) {
            }
            executor.shutdownNow();
            scheduler.shutdownNow();
        }
    }
}
