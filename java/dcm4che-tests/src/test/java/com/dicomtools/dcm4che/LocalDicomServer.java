package com.dicomtools.dcm4che;

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
import org.dcm4che3.net.AssociationHandler;
import org.dcm4che3.net.service.BasicCEchoSCP;
import org.dcm4che3.net.service.BasicCStoreSCP;
import org.dcm4che3.net.service.DicomServiceRegistry;
import org.dcm4che3.net.pdu.PresentationContext;
import org.dcm4che3.net.PDVInputStream;
import org.dcm4che3.net.Status;

import java.io.IOException;
import java.security.GeneralSecurityException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;

/**
 * Lightweight local SCP used in tests to validate networking scenarios without external daemons.
 */
final class LocalDicomServer implements AutoCloseable {
    private final Device device;
    private final ApplicationEntity ae;
    private final Connection connection;
    private final ExecutorService executor;
    private final ScheduledExecutorService scheduler;
    private final List<Attributes> receivedInstances = new ArrayList<>();

    private LocalDicomServer(String aet, int port, boolean enableStore, String storeSopClass) throws IOException, InterruptedException {
        this.device = new Device("dicomtools-test-scp");
        this.ae = new ApplicationEntity(aet);
        this.ae.setAssociationAcceptor(true);
        this.ae.setAssociationInitiator(false);
        this.connection = new Connection();
        this.connection.setPort(port);
        this.connection.setHostname("127.0.0.1");
        this.ae.addConnection(connection);
        this.device.addConnection(connection);
        this.device.addApplicationEntity(ae);

        DicomServiceRegistry registry = new DicomServiceRegistry();
        registry.addDicomService(new BasicCEchoSCP());
        this.ae.addTransferCapability(new TransferCapability(null, UID.Verification,
                TransferCapability.Role.SCP, UID.ImplicitVRLittleEndian));

        if (enableStore) {
            var storeScp = new BasicCStoreSCP(storeSopClass) {
                @Override
                protected void store(Association as, PresentationContext pc, Attributes rq, PDVInputStream data, Attributes rsp) throws IOException {
                    Attributes dataset;
                    try (DicomInputStream dis = new DicomInputStream(data)) {
                        dis.setIncludeBulkData(DicomInputStream.IncludeBulkData.YES);
                        dataset = dis.readDataset(-1, -1);
                    }
                    synchronized (receivedInstances) {
                        receivedInstances.add(dataset);
                    }
                    rsp.setInt(Tag.Status, VR.US, Status.Success);
                }
            };
            registry.addDicomService(storeScp);
            this.ae.addTransferCapability(new TransferCapability(null, storeSopClass,
                    TransferCapability.Role.SCP, UID.ExplicitVRLittleEndian, UID.ImplicitVRLittleEndian));
        }

        this.device.setDimseRQHandler(registry);
        this.device.setAssociationHandler(new AssociationHandler());

        this.executor = Executors.newCachedThreadPool();
        this.scheduler = Executors.newSingleThreadScheduledExecutor();
        this.device.setExecutor(executor);
        this.device.setScheduledExecutor(scheduler);

        try {
            this.device.bindConnections();
        } catch (GeneralSecurityException e) {
            throw new IOException("Failed to bind DICOM server", e);
        }
    }

    static LocalDicomServer createEchoOnly(String aet, int port) throws IOException, InterruptedException {
        return new LocalDicomServer(aet, port, false, null);
    }

    static LocalDicomServer createEchoAndStore(String aet, int port, String storeSopClass) throws IOException, InterruptedException {
        return new LocalDicomServer(aet, port, true, storeSopClass);
    }

    int getPort() {
        return connection.getPort();
    }

    List<Attributes> receivedInstances() {
        synchronized (receivedInstances) {
            return new ArrayList<>(receivedInstances);
        }
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
