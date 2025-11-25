package com.dicomtools.cli;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.deident.DeIdentifier;
import org.dcm4che3.imageio.codec.Transcoder;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.io.DicomOutputStream;

import java.awt.image.BufferedImage;
import java.awt.image.Raster;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

final class DicomFileOperations {
    private DicomFileOperations() {
    }

    static OperationResult info(Path input) throws IOException {
        DicomIOUtils.DicomData data = DicomIOUtils.readDicom(input);
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

    static OperationResult anonymize(Path input, Path output) throws IOException {
        DicomIOUtils.DicomData data = DicomIOUtils.readDicom(input);
        Attributes attrs = new Attributes(data.dataset());
        Attributes fmi = DicomIOUtils.ensureFileMeta(attrs, data.fileMeta());

        DeIdentifier deIdentifier = new DeIdentifier();
        deIdentifier.deidentify(attrs);

        DicomIOUtils.ensureParent(output);
        try (DicomOutputStream dos = new DicomOutputStream(output.toFile())) {
            dos.writeDataset(fmi, attrs);
        }
        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put("output", output.toAbsolutePath().toString());
        meta.put("transferSyntax", fmi.getString(Tag.TransferSyntaxUID));
        return OperationResult.success("Anonymized to " + output, meta, output);
    }

    static OperationResult toImage(Path input, Path output, String format, int frame) throws IOException {
        String resolvedFormat = DicomIOUtils.resolveFormat(output, format);
        DicomIOUtils.ensureParent(output);
        BufferedImage image = DicomIOUtils.loadImage(input, frame);
        javax.imageio.ImageIO.write(image, resolvedFormat, output.toFile());

        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put("output", output.toAbsolutePath().toString());
        meta.put("width", image.getWidth());
        meta.put("height", image.getHeight());
        meta.put("format", resolvedFormat);
        return OperationResult.success("Saved image to " + output, meta, output);
    }

    static OperationResult transcode(Path input, Path output, String syntax) throws IOException {
        String tsuid = DicomIOUtils.mapTransferSyntax(syntax);
        DicomIOUtils.ensureParent(output);

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

    static OperationResult validate(Path input) {
        try (DicomInputStream dis = new DicomInputStream(input.toFile())) {
            dis.readDataset(-1, -1);
            return OperationResult.success("DICOM validated: " + input);
        } catch (Exception e) {
            return OperationResult.failure("Invalid DICOM: " + e.getMessage());
        }
    }

    static OperationResult dump(Path input, int maxWidth) throws IOException {
        DicomIOUtils.DicomData data = DicomIOUtils.readDicom(input);
        StringBuilder sb = new StringBuilder();
        if (data.fileMeta() != null) {
            sb.append("# File Meta Information\n");
            data.fileMeta().toStringBuilder(Integer.MAX_VALUE, maxWidth, sb);
        }
        sb.append("# Dataset\n");
        data.dataset().toStringBuilder(Integer.MAX_VALUE, maxWidth, sb);
        return OperationResult.success(sb.toString());
    }

    static OperationResult stats(Path input, int bins) throws IOException {
        BufferedImage image = DicomIOUtils.loadImage(input, 0);
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

}
