package com.dicomtools.dcm4che;

import com.dicomtools.cli.DicomToolsCli;
import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.data.VR;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.net.ApplicationEntity;
import org.dcm4che3.net.Association;
import org.dcm4che3.net.Connection;
import org.dcm4che3.net.Device;
import org.dcm4che3.net.TransferCapability;
import org.dcm4che3.net.pdu.AAssociateRQ;
import org.dcm4che3.net.pdu.PresentationContext;
import org.dcm4che3.net.service.BasicCFindSCP;
import org.dcm4che3.net.service.BasicCMoveSCP;
import org.dcm4che3.net.service.BasicQueryTask;
import org.dcm4che3.net.service.BasicRetrieveTask;
import org.dcm4che3.net.service.DicomServiceRegistry;
import org.dcm4che3.net.service.InstanceLocator;
import org.dcm4che3.net.service.QueryTask;
import org.dcm4che3.net.service.RetrieveTask;
import org.dcm4che3.util.UIDUtils;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.net.ServerSocket;
import java.nio.file.Path;
import java.nio.file.Paths;
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

class DicomToolsCliIntegrationTest {
    private static final Path SAMPLE_DICOM = Paths.get("..", "..", "sample_series", "IM-0001-0001.dcm")
            .toAbsolutePath().normalize();

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
    void infoCommandReturnsSuccess() {
        int code = DicomToolsCli.execute("info", SAMPLE_DICOM.toString());
        assertEquals(0, code);
    }

    @Test
    void storeScuCliSendsToLocalScp() throws Exception {
        Attributes ds = readDicom(SAMPLE_DICOM);
        int port = openPort();
        try (LocalDicomServer scp = LocalDicomServer.createEchoAndStore("SCP", port, ds.getString(Tag.SOPClassUID))) {
            int code = DicomToolsCli.execute("store-scu", SAMPLE_DICOM.toString(), "--target", "127.0.0.1:" + port);
            assertEquals(0, code);
            TimeUnit.MILLISECONDS.sleep(100);
            assertEquals(1, scp.receivedInstances().size());
        }
    }

    @Test
    void findCliUsesQueryRetrieveServer() throws Exception {
        String patient = "CLI^FIND";
        Attributes ds = minimalStudy(patient);
        int port = openPort();
        QueryRetrieveServer server = QueryRetrieveServer.start(List.of(ds), port, "FIND-SCP", Map.of());
        resources.add(server);

        int code = DicomToolsCli.execute("find", "127.0.0.1:" + port, "--level", "STUDY",
                "--patient", patient, "--calling", "FIND-SCU", "--called", "FIND-SCP");
        assertEquals(0, code);
    }

    @Test
    void moveCliDeliversToDestinationStore() throws Exception {
        Attributes ds = minimalStudy("CLI^MOVE");
        ds.setString(Tag.SOPClassUID, VR.UI, UID.SecondaryCaptureImageStorage);

        int destPort = openPort();
        try (LocalDicomServer destStore = LocalDicomServer.createEchoAndStore("DEST", destPort, UID.SecondaryCaptureImageStorage)) {
            int port = openPort();
            QueryRetrieveServer server = QueryRetrieveServer.start(List.of(ds), port, "MOVE-SCP",
                    Map.of("DEST", new Destination("127.0.0.1", destPort, "DEST")));
            resources.add(server);

            int code = DicomToolsCli.execute("c-move", "127.0.0.1:" + port,
                    "--dest", "DEST", "--study", ds.getString(Tag.StudyInstanceUID));
            assertEquals(0, code);
            TimeUnit.MILLISECONDS.sleep(200);
            assertEquals(1, destStore.receivedInstances().size());
        }
    }

    @Test
    void storageCommitCliRequestsSuccess() throws Exception {
        int port = openPort();
        StorageCommitmentServer scp = StorageCommitmentServer.start(port);
        resources.add(scp);

        int code = DicomToolsCli.execute("stgcmt", "127.0.0.1:" + port, "--files", SAMPLE_DICOM.toString());
        assertEquals(0, code);
    }

    private static int openPort() throws IOException {
        try (ServerSocket socket = new ServerSocket(0)) {
            return socket.getLocalPort();
        }
    }

    private Attributes minimalStudy(String patientName) throws IOException {
        Attributes attrs = readDicom(SAMPLE_DICOM);
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

    static final class Destination {
        final String host;
        final int port;
        final String aet;

        Destination(String host, int port, String aet) {
            this.host = host;
            this.port = port;
            this.aet = aet;
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
            Device device = new Device("qr-cli-scp");
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
                            return new Attributes(iterator.next());
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
                                Attributes dataset = (Attributes) inst.getObject();
                                return (out, transferSyntax) -> {
                                    try (var dos = new org.dcm4che3.io.DicomOutputStream(out, transferSyntax)) {
                                        dos.writeDataset(dataset.createFileMetaInformation(transferSyntax), dataset);
                                    }
                                };
                            }
                        };
                    } catch (Exception e) {
                        return null;
                    }
                }

                private Association connectStoreAssociation(Destination dest) throws IOException, org.dcm4che3.net.IncompatibleConnectionException, InterruptedException, java.security.GeneralSecurityException {
                    Device storeScu = new Device("move-store-scu");
                    ApplicationEntity ae = new ApplicationEntity("MOVE-SCU");
                    ae.setAssociationInitiator(true);
                    Connection conn = new Connection();
                    conn.setHostname("127.0.0.1");
                    storeScu.addConnection(conn);
                    ae.addConnection(conn);
                    storeScu.addApplicationEntity(ae);
                    ae.addTransferCapability(new TransferCapability(null, UID.SecondaryCaptureImageStorage,
                            TransferCapability.Role.SCU, UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));
                    ExecutorService exec = Executors.newSingleThreadExecutor();
                    ScheduledExecutorService sched = Executors.newSingleThreadScheduledExecutor();
                    storeScu.setExecutor(exec);
                    storeScu.setScheduledExecutor(sched);
                    closers.add(() -> {
                        exec.shutdownNow();
                        sched.shutdownNow();
                    });

                    Connection remote = new Connection();
                    remote.setHostname(dest.host);
                    remote.setPort(dest.port);

                    AAssociateRQ rq = new AAssociateRQ();
                    rq.setCallingAET("MOVE-SCU");
                    rq.setCalledAET(dest.aet);
                    rq.addPresentationContext(new PresentationContext(1, UID.SecondaryCaptureImageStorage,
                            UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));
                    Association as = ae.connect(remote, rq);
                    closers.add(as::release);
                    return as;
                }
            });

            registry.addDicomService(new org.dcm4che3.net.service.BasicCEchoSCP());
            ae.addTransferCapability(new TransferCapability(null, UID.StudyRootQueryRetrieveInformationModelFind,
                    TransferCapability.Role.SCP, UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));
            ae.addTransferCapability(new TransferCapability(null, UID.StudyRootQueryRetrieveInformationModelMove,
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
            extraClosers.forEach(c -> {
                try {
                    c.close();
                } catch (Exception ignored) {
                }
            });
            executor.shutdownNow();
            scheduler.shutdownNow();
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
            Device device = new Device("stgcmtscp-cli");
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
                        Attributes rsp = org.dcm4che3.net.Commands.mkNActionRSP(cmd, org.dcm4che3.net.Status.Success);
                        as.tryWriteDimseRSP(pc, rsp);
                    } else if (dimse == org.dcm4che3.net.Dimse.N_EVENT_REPORT_RQ) {
                        Attributes rsp = org.dcm4che3.net.Commands.mkNEventReportRSP(cmd, org.dcm4che3.net.Status.Success);
                        as.tryWriteDimseRSP(pc, rsp);
                    } else {
                        throw new org.dcm4che3.net.service.DicomServiceException(org.dcm4che3.net.Status.UnrecognizedOperation);
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
