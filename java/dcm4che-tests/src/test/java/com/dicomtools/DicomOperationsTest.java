package com.dicomtools;

import com.dicomtools.cli.DicomOperations;
import com.dicomtools.cli.OperationResult;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.io.DicomInputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class DicomOperationsTest {

    private static final Path SAMPLE_DICOM = Paths.get("..", "..", "sample_series", "IM-0001-0001.dcm").toAbsolutePath().normalize();

    @TempDir
    Path tempDir;

    @Test
    void infoReturnsBasicMetadata() throws Exception {
        OperationResult result = DicomOperations.info(SAMPLE_DICOM);
        Map<String, Object> meta = result.getMetadata();

        assertTrue(result.isSuccess());
        assertTrue(((Number) meta.get("rows")).intValue() > 0);
        assertTrue(((Number) meta.get("columns")).intValue() > 0);
        assertNotNull(meta.get("sopClassUid"));
        assertNotNull(meta.get("sopClassName"));
    }

    @Test
    void anonymizeProducesNewFileWithScrubbedPatient() throws Exception {
        Path output = tempDir.resolve("anon.dcm");
        String originalName = readTagString(SAMPLE_DICOM, Tag.PatientName);

        OperationResult result = DicomOperations.anonymize(SAMPLE_DICOM, output);
        assertTrue(result.isSuccess());
        assertTrue(Files.exists(output));

        String anonName = readTagString(output, Tag.PatientName);
        assertNotEquals(originalName, anonName);
    }

    @Test
    void toImageCreatesPng() throws Exception {
        Path output = tempDir.resolve("preview.png");
        OperationResult result = DicomOperations.toImage(SAMPLE_DICOM, output, "png", 0);
        assertTrue(result.isSuccess());
        assertTrue(Files.exists(output));

        BufferedImage img = ImageIO.read(output.toFile());
        assertNotNull(img);
        assertTrue(img.getWidth() > 0);
        assertTrue(img.getHeight() > 0);
    }

    @Test
    void transcodeChangesTransferSyntax() throws Exception {
        Path output = tempDir.resolve("transcoded.dcm");
        OperationResult result = DicomOperations.transcode(SAMPLE_DICOM, output, "implicit");
        assertTrue(result.isSuccess());
        assertTrue(Files.exists(output));

        try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
            String ts = dis.readFileMetaInformation().getString(Tag.TransferSyntaxUID);
            assertEquals(UID.ImplicitVRLittleEndian, ts);
        }
    }

    @Test
    void validateAcceptsSample() {
        OperationResult result = DicomOperations.validate(SAMPLE_DICOM);
        assertTrue(result.isSuccess());
    }

    @Test
    void dumpReturnsDatasetText() throws Exception {
        OperationResult result = DicomOperations.dump(SAMPLE_DICOM, 80);
        assertTrue(result.isSuccess());
        assertTrue(result.getMessage().contains("PatientName"));
    }

    @Test
    void statsReturnsHistogram() throws Exception {
        OperationResult result = DicomOperations.stats(SAMPLE_DICOM, 16);
        assertTrue(result.isSuccess());
        Map<String, Object> meta = result.getMetadata();
        assertEquals(16, ((Number) meta.get("bins")).intValue());
        List<?> histogram = (List<?>) meta.get("histogram");
        assertEquals(16, histogram.size());
        double min = ((Number) meta.get("min")).doubleValue();
        double max = ((Number) meta.get("max")).doubleValue();
        assertTrue(max >= min);
    }

    @Test
    void echoFailsGracefullyWhenServerUnavailable() {
        OperationResult result = DicomOperations.echo("127.0.0.1", 1, 500, "ECHO-SCU", "ANY-SCP");
        assertFalse(result.isSuccess());
        assertTrue(result.getMessage().toLowerCase().contains("echo"));
    }

    private String readTagString(Path path, int tag) throws IOException {
        try (DicomInputStream dis = new DicomInputStream(path.toFile())) {
            dis.readFileMetaInformation();
            return dis.readDataset(-1, -1).getString(tag, "");
        }
    }
}
