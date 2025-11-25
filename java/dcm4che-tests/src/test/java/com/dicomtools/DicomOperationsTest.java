package com.dicomtools;

import com.dicomtools.cli.DicomOperations;
import com.dicomtools.cli.OperationResult;
import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Sequence;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.data.VR;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.io.DicomOutputStream;
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

    @Test
    void structuredReportSummarizesContentSequence() throws Exception {
        Path srPath = tempDir.resolve("sample-sr.dcm");
        writeDicom(buildStructuredReport(), srPath);

        OperationResult result = DicomOperations.structuredReport(srPath);
        assertTrue(result.isSuccess());
        Map<String, Object> meta = result.getMetadata();
        List<?> entries = (List<?>) meta.get("entries");
        assertEquals(3, entries.size());
        Map<?, ?> first = (Map<?, ?>) entries.get(0);
        assertEquals(0, ((Number) first.get("level")).intValue());
        assertEquals("TEXT", first.get("valueType"));
        assertTrue(String.valueOf(first.get("conceptName")).contains("Findings"));
        Map<?, ?> child = (Map<?, ?>) entries.get(1);
        assertEquals(1, ((Number) child.get("level")).intValue());
        assertEquals("CODE", child.get("valueType"));
    }

    @Test
    void rtConsistencyDetectsReferencedPlanMismatch() throws Exception {
        String planUid = "1.2.3.4.plan";
        String studyUid = "1.2.3.4.study";
        String forUid = "1.2.3.4.for";

        Path planPath = tempDir.resolve("plan.dcm");
        Path dosePath = tempDir.resolve("dose.dcm");
        Path structPath = tempDir.resolve("struct.dcm");
        writeDicom(buildRtPlan(planUid, studyUid, forUid), planPath);
        writeDicom(buildRtDose(planUid, studyUid), dosePath);
        writeDicom(buildRtStruct(planUid, studyUid, forUid), structPath);

        OperationResult ok = DicomOperations.rtConsistency(planPath, dosePath, structPath);
        assertTrue(ok.isSuccess());
        assertEquals(0, ((List<?>) ok.getMetadata().get("issues")).size());

        Path badDosePath = tempDir.resolve("dose-bad.dcm");
        writeDicom(buildRtDose("9.9.9.bad", studyUid), badDosePath);
        OperationResult bad = DicomOperations.rtConsistency(planPath, badDosePath, structPath);
        assertFalse(bad.isSuccess());
        assertTrue(bad.getMessage().toLowerCase().contains("rtplan"));
    }

    private String readTagString(Path path, int tag) throws IOException {
        try (DicomInputStream dis = new DicomInputStream(path.toFile())) {
            dis.readFileMetaInformation();
            return dis.readDataset(-1, -1).getString(tag, "");
        }
    }

    private Attributes buildStructuredReport() {
        Attributes sr = new Attributes();
        sr.setString(Tag.SOPClassUID, VR.UI, UID.BasicTextSRStorage);
        sr.setString(Tag.SOPInstanceUID, VR.UI, "1.2.826.0.1.3680043.2.1125.1");
        Sequence top = sr.newSequence(Tag.ContentSequence, 2);

        Attributes finding = new Attributes();
        finding.setString(Tag.RelationshipType, VR.CS, "CONTAINS");
        finding.setString(Tag.ValueType, VR.CS, "TEXT");
        Sequence concept = finding.newSequence(Tag.ConceptNameCodeSequence, 1);
        Attributes code = new Attributes();
        code.setString(Tag.CodeValue, VR.SH, "121071");
        code.setString(Tag.CodingSchemeDesignator, VR.SH, "DCM");
        code.setString(Tag.CodeMeaning, VR.LO, "Findings");
        concept.add(code);
        finding.setString(Tag.TextValue, VR.UT, "No acute findings.");

        Sequence childSeq = finding.newSequence(Tag.ContentSequence, 1);
        Attributes child = new Attributes();
        child.setString(Tag.RelationshipType, VR.CS, "HAS PROPERTIES");
        child.setString(Tag.ValueType, VR.CS, "CODE");
        Sequence childConcept = child.newSequence(Tag.ConceptNameCodeSequence, 1);
        Attributes childCode = new Attributes();
        childCode.setString(Tag.CodeValue, VR.SH, "111001");
        childCode.setString(Tag.CodingSchemeDesignator, VR.SH, "99LOCAL");
        childCode.setString(Tag.CodeMeaning, VR.LO, "Severity");
        childConcept.add(childCode);
        childSeq.add(child);
        top.add(finding);

        Attributes conclusion = new Attributes();
        conclusion.setString(Tag.RelationshipType, VR.CS, "CONTAINS");
        conclusion.setString(Tag.ValueType, VR.CS, "TEXT");
        conclusion.setString(Tag.TextValue, VR.UT, "Patient stable.");
        top.add(conclusion);

        return sr;
    }

    private Attributes buildRtPlan(String planUid, String studyUid, String forUid) {
        Attributes plan = new Attributes();
        plan.setString(Tag.SOPClassUID, VR.UI, UID.RTPlanStorage);
        plan.setString(Tag.SOPInstanceUID, VR.UI, planUid);
        plan.setString(Tag.StudyInstanceUID, VR.UI, studyUid);
        plan.setString(Tag.FrameOfReferenceUID, VR.UI, forUid);
        return plan;
    }

    private Attributes buildRtDose(String planUid, String studyUid) {
        Attributes dose = new Attributes();
        dose.setString(Tag.SOPClassUID, VR.UI, UID.RTDoseStorage);
        dose.setString(Tag.SOPInstanceUID, VR.UI, planUid + ".dose");
        dose.setString(Tag.StudyInstanceUID, VR.UI, studyUid);
        Sequence refSeq = dose.newSequence(Tag.ReferencedRTPlanSequence, 1);
        Attributes ref = new Attributes();
        ref.setString(Tag.ReferencedSOPInstanceUID, VR.UI, planUid);
        refSeq.add(ref);
        return dose;
    }

    private Attributes buildRtStruct(String planUid, String studyUid, String forUid) {
        Attributes struct = new Attributes();
        struct.setString(Tag.SOPClassUID, VR.UI, UID.RTStructureSetStorage);
        struct.setString(Tag.SOPInstanceUID, VR.UI, planUid + ".struct");
        struct.setString(Tag.StudyInstanceUID, VR.UI, studyUid);
        struct.setString(Tag.FrameOfReferenceUID, VR.UI, forUid);
        Sequence refPlan = struct.newSequence(Tag.ReferencedRTPlanSequence, 1);
        Attributes ref = new Attributes();
        ref.setString(Tag.ReferencedSOPInstanceUID, VR.UI, planUid);
        refPlan.add(ref);
        return struct;
    }

    private void writeDicom(Attributes attrs, Path path) throws IOException {
        Attributes fmi = attrs.createFileMetaInformation(UID.ExplicitVRLittleEndian);
        try (DicomOutputStream dos = new DicomOutputStream(path.toFile())) {
            dos.writeDataset(fmi, attrs);
        }
    }
}
