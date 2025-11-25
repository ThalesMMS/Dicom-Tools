package com.dicomtools.cli;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.imageio.plugins.dcm.DicomImageReadParam;
import org.dcm4che3.imageio.plugins.dcm.DicomImageReader;
import org.dcm4che3.imageio.plugins.dcm.DicomImageReaderSpi;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.util.UIDUtils;

import javax.imageio.ImageIO;
import javax.imageio.stream.ImageInputStream;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Shared I/O helpers for DICOM operations.
 */
final class DicomIOUtils {
    private DicomIOUtils() {
    }

    static DicomData readDicom(Path input) throws IOException {
        try (DicomInputStream dis = new DicomInputStream(input.toFile())) {
            Attributes fmi = dis.readFileMetaInformation();
            Attributes attrs = dis.readDataset(-1, -1);
            return new DicomData(attrs, fmi);
        }
    }

    static Attributes ensureFileMeta(Attributes attrs, Attributes fmi) {
        if (fmi != null) return fmi;
        String tsuid = attrs.getString(Tag.TransferSyntaxUID, UID.ExplicitVRLittleEndian);
        if (!attrs.containsValue(Tag.SOPInstanceUID)) {
            attrs.setString(Tag.SOPInstanceUID, org.dcm4che3.data.VR.UI, UIDUtils.createUID());
        }
        return attrs.createFileMetaInformation(tsuid);
    }

    static BufferedImage loadImage(Path input, int frame) throws IOException {
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

    static void ensureParent(Path output) throws IOException {
        Path parent = output.toAbsolutePath().getParent();
        if (parent != null) {
            Files.createDirectories(parent);
        }
    }

    static String resolveFormat(Path output, String format) {
        if (format != null && !format.isBlank()) {
            return format.toLowerCase();
        }
        String name = output.getFileName().toString().toLowerCase();
        if (name.endsWith(".jpg") || name.endsWith(".jpeg")) return "jpeg";
        if (name.endsWith(".png")) return "png";
        return "png";
    }

    static String mapTransferSyntax(String syntax) {
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

    record DicomData(Attributes dataset, Attributes fileMeta) {
    }
}
