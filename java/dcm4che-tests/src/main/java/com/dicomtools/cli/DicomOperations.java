package com.dicomtools.cli;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Sequence;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.deident.DeIdentifier;
import org.dcm4che3.imageio.codec.Transcoder;
import org.dcm4che3.imageio.plugins.dcm.DicomImageReadParam;
import org.dcm4che3.imageio.plugins.dcm.DicomImageReader;
import org.dcm4che3.imageio.plugins.dcm.DicomImageReaderSpi;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.io.DicomOutputStream;
import org.dcm4che3.net.ApplicationEntity;
import org.dcm4che3.net.Association;
import org.dcm4che3.net.Connection;
import org.dcm4che3.net.DataWriterAdapter;
import org.dcm4che3.net.Device;
import org.dcm4che3.net.IncompatibleConnectionException;
import org.dcm4che3.net.Priority;
import org.dcm4che3.net.PDVInputStream;
import org.dcm4che3.net.Status;
import org.dcm4che3.net.TransferCapability;
import org.dcm4che3.net.pdu.AAssociateRQ;
import org.dcm4che3.net.pdu.PresentationContext;
import org.dcm4che3.net.service.DicomServiceException;
import org.dcm4che3.net.service.BasicCStoreSCP;
import org.dcm4che3.net.service.BasicCEchoSCP;
import org.dcm4che3.net.service.DicomServiceRegistry;
import org.dcm4che3.util.UIDUtils;

import javax.imageio.ImageIO;
import javax.imageio.stream.ImageInputStream;
import java.awt.image.BufferedImage;
import java.awt.image.Raster;
import java.io.FileOutputStream;
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
import java.util.stream.Collectors;

public final class DicomOperations {
    private DicomOperations() {
    }

    public static OperationResult info(Path input) throws IOException {
        DicomData data = readDicom(input);
        Attributes attrs = data.dataset();
        Attributes fmi = data.fileMeta();

        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put("path", input.toAbsolutePath().toString());
        meta.put("sopClassUid", attrs.getString(Tag.SOPClassUID, ""));
        meta.put("sopClassName", UID.nameOf(attrs.getString(Tag.SOPClassUID, "")));
        meta.put("sopInstanceUid", attrs.getString(Tag.SOPInstanceUID, ""));
        meta.put("studyInstanceUid", attrs.getString(Tag.StudyInstanceUID, ""));
        meta.put("seriesInstanceUid", attrs.getString(Tag.SeriesInstanceUID, ""));
        meta.put("modality", attrs.getString(Tag.Modality, ""));
        meta.put("patientName", attrs.getString(Tag.PatientName, ""));
        meta.put("patientId", attrs.getString(Tag.PatientID, ""));
        meta.put("studyDescription", attrs.getString(Tag.StudyDescription, ""));
        meta.put("seriesDescription", attrs.getString(Tag.SeriesDescription, ""));
        meta.put("transferSyntax", fmi != null ? fmi.getString(Tag.TransferSyntaxUID, "") : "");
        meta.put("rows", attrs.getInt(Tag.Rows, -1));
        meta.put("columns", attrs.getInt(Tag.Columns, -1));
        meta.put("bitsStored", attrs.getInt(Tag.BitsStored, -1));
        meta.put("numberOfFrames", attrs.getInt(Tag.NumberOfFrames, 1));
        String[] imageTypes = attrs.getStrings(Tag.ImageType);
        meta.put("imageType", imageTypes != null ? String.join("\\", imageTypes) : "");
        meta.put("fileSize", Files.size(input));

        String summary = String.format(
                "SOPClass=%s Modality=%s Size=%dx%d Frames=%d",
                meta.get("sopClassName"),
                meta.get("modality"),
                meta.get("columns"),
                meta.get("rows"),
                meta.get("numberOfFrames"));
        return OperationResult.success(summary, meta, java.util.Collections.emptyList());
    }

    public static OperationResult anonymize(Path input, Path output) throws IOException {
        DicomData data = readDicom(input);
        Attributes attrs = new Attributes(data.dataset());
        Attributes fmi = ensureFileMeta(attrs, data.fileMeta());

        DeIdentifier deIdentifier = new DeIdentifier();
        deIdentifier.deidentify(attrs);

        ensureParent(output);
        try (DicomOutputStream dos = new DicomOutputStream(output.toFile())) {
            dos.writeDataset(fmi, attrs);
        }
        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put("output", output.toAbsolutePath().toString());
        meta.put("transferSyntax", fmi.getString(Tag.TransferSyntaxUID));
        return OperationResult.success("Anonymized to " + output, meta, output);
    }

    public static OperationResult toImage(Path input, Path output, String format, int frame) throws IOException {
        String resolvedFormat = resolveFormat(output, format);
        ensureParent(output);
        BufferedImage image = loadImage(input, frame);
        ImageIO.write(image, resolvedFormat, output.toFile());

        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put("output", output.toAbsolutePath().toString());
        meta.put("width", image.getWidth());
        meta.put("height", image.getHeight());
        meta.put("format", resolvedFormat);
        return OperationResult.success("Saved image to " + output, meta, output);
    }

    public static OperationResult transcode(Path input, Path output, String syntax) throws IOException {
        String tsuid = mapTransferSyntax(syntax);
        ensureParent(output);

        try (Transcoder transcoder = new Transcoder(input.toFile())) {
            transcoder.setIncludeFileMetaInformation(true);
            transcoder.setDestinationTransferSyntax(tsuid);
            transcoder.transcode((t, dataset) -> new FileOutputStream(output.toFile()));
        }

        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put("output", output.toAbsolutePath().toString());
        meta.put("transferSyntax", tsuid);
        return OperationResult.success("Transcoded to " + tsuid + " at " + output, meta, output);
    }

    public static OperationResult validate(Path input) {
        try (DicomInputStream dis = new DicomInputStream(input.toFile())) {
            dis.readDataset(-1, -1);
            return OperationResult.success("DICOM validated: " + input);
        } catch (Exception e) {
            return OperationResult.failure("Invalid DICOM: " + e.getMessage());
        }
    }

    public static OperationResult dump(Path input, int maxWidth) throws IOException {
        DicomData data = readDicom(input);
        StringBuilder sb = new StringBuilder();
        if (data.fileMeta() != null) {
            sb.append("# File Meta Information\n");
            data.fileMeta().toStringBuilder(Integer.MAX_VALUE, maxWidth, sb);
        }
        sb.append("# Dataset\n");
        data.dataset().toStringBuilder(Integer.MAX_VALUE, maxWidth, sb);
        return OperationResult.success(sb.toString());
    }

    public static OperationResult stats(Path input, int bins) throws IOException {
        BufferedImage image = loadImage(input, 0);
        Raster raster = image.getData();

        long count = (long) raster.getWidth() * raster.getHeight();
        double min = Double.POSITIVE_INFINITY;
        double max = Double.NEGATIVE_INFINITY;
        long sum = 0;

        for (int y = 0; y < raster.getHeight(); y++) {
            for (int x = 0; x < raster.getWidth(); x++) {
                int sample = raster.getSample(x, y, 0);
                min = Math.min(min, sample);
                max = Math.max(max, sample);
                sum += sample;
            }
        }

        double mean = sum / (double) count;
        double varianceSum = 0.0;
        for (int y = 0; y < raster.getHeight(); y++) {
            for (int x = 0; x < raster.getWidth(); x++) {
                double diff = raster.getSample(x, y, 0) - mean;
                varianceSum += diff * diff;
            }
        }
        double stddev = Math.sqrt(varianceSum / count);

        List<Long> histogram = new ArrayList<>(bins);
        for (int i = 0; i < bins; i++) histogram.add(0L);
        if (max == min) {
            histogram.set(0, count);
        } else {
            double range = max - min;
            for (int y = 0; y < raster.getHeight(); y++) {
                for (int x = 0; x < raster.getWidth(); x++) {
                    double value = raster.getSample(x, y, 0);
                    int bin = (int) Math.floor((value - min) / range * (bins - 1));
                    histogram.set(bin, histogram.get(bin) + 1);
                }
            }
        }

        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put("width", raster.getWidth());
        meta.put("height", raster.getHeight());
        meta.put("min", min);
        meta.put("max", max);
        meta.put("mean", mean);
        meta.put("stddev", stddev);
        meta.put("bins", bins);
        meta.put("histogram", histogram);

        return OperationResult.success("Computed stats for " + input, meta, java.util.Collections.emptyList());
    }

    public static OperationResult echo(String host, int port, int timeoutMs, String callingAet, String calledAet) {
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

    /**
     * Parse a Structured Report and return a flattened view of ContentSequence with basic code/text values.
     */
    public static OperationResult structuredReport(Path input) throws IOException {
        DicomData data = readDicom(input);
        Attributes attrs = data.dataset();
        List<Map<String, Object>> entries = new ArrayList<>();

        Sequence content = attrs.getSequence(Tag.ContentSequence);
        if (content != null) {
            for (Attributes item : content) {
                collectSrNodes(item, 0, entries);
            }
        }

        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put("sopClassUid", attrs.getString(Tag.SOPClassUID, ""));
        meta.put("sopClassName", UID.nameOf(attrs.getString(Tag.SOPClassUID, "")));
        meta.put("entryCount", entries.size());
        meta.put("entries", entries);

        String message = entries.isEmpty()
                ? "Structured Report parsed but ContentSequence is empty"
                : "Structured Report parsed with " + entries.size() + " content items";
        return OperationResult.success(message, meta, java.util.Collections.emptyList());
    }

    /**
     * Cross-check RTPLAN/RTDOSE/RTSTRUCT links (StudyInstanceUID, FrameOfReferenceUID, ReferencedRTPlanSequence).
     */
    public static OperationResult rtConsistency(Path planPath, Path dosePath, Path structPath) throws IOException {
        Attributes plan = planPath != null ? readDicom(planPath).dataset() : null;
        Attributes dose = dosePath != null ? readDicom(dosePath).dataset() : null;
        Attributes struct = structPath != null ? readDicom(structPath).dataset() : null;

        String planUid = plan != null ? plan.getString(Tag.SOPInstanceUID, "") : "";
        String planStudy = plan != null ? plan.getString(Tag.StudyInstanceUID, "") : "";
        String planFor = plan != null ? plan.getString(Tag.FrameOfReferenceUID, "") : "";

        List<String> issues = new ArrayList<>();
        Map<String, Object> meta = new LinkedHashMap<>();

        if (plan != null) meta.put("plan", summarizeRt(planPath, plan));
        if (dose != null) meta.put("dose", summarizeRt(dosePath, dose));
        if (struct != null) meta.put("struct", summarizeRt(structPath, struct));

        if (plan != null && dose != null) {
            if (!referencesPlan(dose, planUid)) {
                issues.add("RTDOSE does not reference supplied RTPLAN " + planUid);
            }
            String doseStudy = dose.getString(Tag.StudyInstanceUID, "");
            if (!planStudy.isBlank() && !doseStudy.isBlank() && !planStudy.equals(doseStudy)) {
                issues.add("StudyInstanceUID mismatch between RTPLAN and RTDOSE");
            }
        }

        if (plan != null && struct != null) {
            String structStudy = struct.getString(Tag.StudyInstanceUID, "");
            if (!planStudy.isBlank() && !structStudy.isBlank() && !planStudy.equals(structStudy)) {
                issues.add("StudyInstanceUID mismatch between RTPLAN and RTSTRUCT");
            }
            String structFor = struct.getString(Tag.FrameOfReferenceUID, "");
            if (!planFor.isBlank() && !structFor.isBlank() && !planFor.equals(structFor)) {
                issues.add("FrameOfReferenceUID mismatch between RTPLAN and RTSTRUCT");
            }
            Sequence refPlanSeq = struct.getSequence(Tag.ReferencedRTPlanSequence);
            if (refPlanSeq != null && !refPlanSeq.isEmpty() && !referencesPlan(struct, planUid)) {
                issues.add("RTSTRUCT references a different RTPLAN than supplied");
            }
        }

        if (!issues.isEmpty()) {
            meta.put("issues", issues);
            return OperationResult.failure("RT consistency check failed: " + String.join("; ", issues), meta);
        }

        meta.put("issues", java.util.Collections.emptyList());
        return OperationResult.success("RT references are consistent", meta, java.util.Collections.emptyList());
    }

    public static OperationResult store(Path input, String host, int port, int timeoutMs, String callingAet, String calledAet) {
        try {
            Attributes dataset = readDicom(input).dataset();
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
                if (status == Status.Success) {
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

    public static OperationResult storeSCP(int port, String aet, Path outputDir, int durationSeconds) {
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
                rsp.setInt(Tag.Status, org.dcm4che3.data.VR.US, Status.Success);
            }
        });
        registry.addDicomService(new org.dcm4che3.net.service.BasicCEchoSCP());
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

    public static OperationResult cfind(String host, int port, String callingAet, String calledAet, String level, Map<Integer, String> filters, int timeoutMs) {
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
                if (Status.isPending(status)) {
                    Attributes data = rsp.getDataset();
                    if (data != null) {
                        matches.add(Map.of(
                                "patientName", data.getString(Tag.PatientName, ""),
                                "patientId", data.getString(Tag.PatientID, ""),
                                "studyInstanceUid", data.getString(Tag.StudyInstanceUID, ""),
                                "seriesInstanceUid", data.getString(Tag.SeriesInstanceUID, "")
                        ));
                    }
                } else if (status != Status.Success) {
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

    public static OperationResult cmove(String host, int port, String callingAet, String calledAet,
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
            int status = Status.Success;
            while (rsp.next()) {
                status = rsp.getCommand().getInt(Tag.Status, -1);
                if (!Status.isPending(status) && status != Status.Success) {
                    break;
                }
            }
            as.release();
            if (status == Status.Success) {
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

    public static OperationResult cget(String host, int port, String callingAet, String calledAet,
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
                rsp.setInt(Tag.Status, org.dcm4che3.data.VR.US, Status.Success);
            }
        });
        registry.addDicomService(new org.dcm4che3.net.service.BasicCEchoSCP());
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
            int status = Status.Success;
            while (rsp.next()) {
                status = rsp.getCommand().getInt(Tag.Status, -1);
                if (!Status.isPending(status) && status != Status.Success) {
                    break;
                }
            }
            as.waitForOutstandingRSP();
            as.release();
            Map<String, Object> meta = new LinkedHashMap<>();
            meta.put("stored", stored.stream().map(Path::toString).toList());
            meta.put("count", stored.size());
            if (status == Status.Success) {
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

    public static OperationResult storageCommit(String host, int port, String callingAet, String calledAet,
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
        registry.addDicomService(new org.dcm4che3.net.service.BasicCEchoSCP());
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
                Attributes ds = readDicom(path).dataset();
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
            if (status != Status.Success && status != Status.Pending) {
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

    private static DicomData readDicom(Path input) throws IOException {
        try (DicomInputStream dis = new DicomInputStream(input.toFile())) {
            Attributes fmi = dis.readFileMetaInformation();
            Attributes attrs = dis.readDataset(-1, -1);
            return new DicomData(attrs, fmi);
        }
    }

    private static void collectSrNodes(Attributes item, int level, List<Map<String, Object>> entries) {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("level", level);
        row.put("relationship", item.getString(Tag.RelationshipType, ""));
        row.put("valueType", item.getString(Tag.ValueType, ""));
        row.put("conceptName", codeDisplay(item.getSequence(Tag.ConceptNameCodeSequence)));
        row.put("codeMeaning", codeMeaning(item.getSequence(Tag.ConceptNameCodeSequence)));
        row.put("codeValue", codeValue(item.getSequence(Tag.ConceptNameCodeSequence)));
        row.put("textValue", item.getString(Tag.TextValue, ""));
        row.put("numericValue", item.getString(Tag.NumericValue, ""));
        entries.add(row);

        Sequence nested = item.getSequence(Tag.ContentSequence);
        if (nested != null) {
            for (Attributes child : nested) {
                collectSrNodes(child, level + 1, entries);
            }
        }
    }

    private static Map<String, Object> summarizeRt(Path path, Attributes attrs) {
        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("path", path != null ? path.toAbsolutePath().toString() : "");
        summary.put("sopClassUid", attrs.getString(Tag.SOPClassUID, ""));
        summary.put("sopClassName", UID.nameOf(attrs.getString(Tag.SOPClassUID, "")));
        summary.put("sopInstanceUid", attrs.getString(Tag.SOPInstanceUID, ""));
        summary.put("studyInstanceUid", attrs.getString(Tag.StudyInstanceUID, ""));
        summary.put("seriesInstanceUid", attrs.getString(Tag.SeriesInstanceUID, ""));
        summary.put("frameOfReferenceUid", attrs.getString(Tag.FrameOfReferenceUID, ""));
        summary.put("referencedPlanUids", findReferencedPlanUids(attrs));
        return summary;
    }

    private static List<String> findReferencedPlanUids(Attributes attrs) {
        Sequence seq = attrs.getSequence(Tag.ReferencedRTPlanSequence);
        if (seq == null || seq.isEmpty()) {
            return java.util.Collections.emptyList();
        }
        return seq.stream()
                .map(a -> a.getString(Tag.ReferencedSOPInstanceUID, ""))
                .filter(s -> s != null && !s.isBlank())
                .collect(Collectors.toList());
    }

    private static boolean referencesPlan(Attributes attrs, String planUid) {
        if (planUid == null || planUid.isBlank()) return false;
        return findReferencedPlanUids(attrs).stream().anyMatch(planUid::equals);
    }

    private static String codeMeaning(Sequence seq) {
        if (seq == null || seq.isEmpty()) return "";
        return seq.get(0).getString(Tag.CodeMeaning, "");
    }

    private static String codeValue(Sequence seq) {
        if (seq == null || seq.isEmpty()) return "";
        return seq.get(0).getString(Tag.CodeValue, "");
    }

    private static String codeDisplay(Sequence seq) {
        if (seq == null || seq.isEmpty()) return "";
        Attributes code = seq.get(0);
        String meaning = code.getString(Tag.CodeMeaning, "");
        String value = code.getString(Tag.CodeValue, "");
        String scheme = code.getString(Tag.CodingSchemeDesignator, "");
        if (!meaning.isBlank() && !value.isBlank() && !scheme.isBlank()) {
            return meaning + " [" + scheme + ":" + value + "]";
        }
        if (!meaning.isBlank() && !value.isBlank()) {
            return meaning + " [" + value + "]";
        }
        return meaning.isBlank() ? value : meaning;
    }

    private static Attributes ensureFileMeta(Attributes attrs, Attributes fmi) {
        if (fmi != null) return fmi;
        String tsuid = attrs.getString(Tag.TransferSyntaxUID, UID.ExplicitVRLittleEndian);
        if (!attrs.containsValue(Tag.SOPInstanceUID)) {
            attrs.setString(Tag.SOPInstanceUID, org.dcm4che3.data.VR.UI, UIDUtils.createUID());
        }
        return attrs.createFileMetaInformation(tsuid);
    }

    private static BufferedImage loadImage(Path input, int frame) throws IOException {
        ImageIO.scanForPlugins();
        try (ImageInputStream iis = ImageIO.createImageInputStream(input.toFile())) {
            DicomImageReader reader = new DicomImageReader(new DicomImageReaderSpi());
            reader.setInput(iis);
            DicomImageReadParam param = (DicomImageReadParam) reader.getDefaultReadParam();
            BufferedImage image = reader.read(frame, param);
            reader.dispose();
            return image;
        }
    }

    private static void ensureParent(Path output) throws IOException {
        Path parent = output.toAbsolutePath().getParent();
        if (parent != null) {
            Files.createDirectories(parent);
        }
    }

    private static String resolveFormat(Path output, String format) {
        if (format != null && !format.isBlank()) {
            return format.toLowerCase();
        }
        String name = output.getFileName().toString().toLowerCase();
        if (name.endsWith(".jpg") || name.endsWith(".jpeg")) return "jpeg";
        if (name.endsWith(".png")) return "png";
        return "png";
    }

    private static String mapTransferSyntax(String syntax) {
        if (syntax == null || syntax.isBlank()) {
            return UID.ExplicitVRLittleEndian;
        }
        return switch (syntax.toLowerCase()) {
            case "implicit" -> UID.ImplicitVRLittleEndian;
            case "big-endian", "be" -> UID.ExplicitVRBigEndian;
            case "deflated" -> UID.DeflatedExplicitVRLittleEndian;
            case "jpeg2000", "j2k" -> UID.JPEG2000Lossless;
            case "rle" -> UID.RLELossless;
            default -> UID.ExplicitVRLittleEndian;
        };
    }

    private record DicomData(Attributes dataset, Attributes fileMeta) {
    }
}
