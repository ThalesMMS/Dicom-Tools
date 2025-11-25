package com.dicomtools.cli;

import org.dcm4che3.data.Attributes;
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
import org.dcm4che3.net.Device;
import org.dcm4che3.net.IncompatibleConnectionException;
import org.dcm4che3.net.TransferCapability;
import org.dcm4che3.net.pdu.AAssociateRQ;
import org.dcm4che3.net.pdu.PresentationContext;
import org.dcm4che3.net.service.DicomServiceException;
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
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

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

    private static DicomData readDicom(Path input) throws IOException {
        try (DicomInputStream dis = new DicomInputStream(input.toFile())) {
            Attributes fmi = dis.readFileMetaInformation();
            Attributes attrs = dis.readDataset(-1, -1);
            return new DicomData(attrs, fmi);
        }
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
