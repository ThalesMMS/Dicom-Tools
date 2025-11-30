package com.dicomtools.dcm4che;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Path;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Sequence;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.data.VR;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.io.DicomOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/**
 * Testes de manipulação de tags DICOM.
 * Verifica adição, remoção, modificação e leitura de tags com diferentes VRs.
 */
class DicomTagManipulationTest {

    @TempDir
    Path tempDir;

    @Test
    void addsStringTag() throws Exception {
        Attributes attrs = new Attributes();
        attrs.setString(Tag.StudyDescription, VR.LO, "Test Study");

        assertEquals("Test Study", attrs.getString(Tag.StudyDescription));
        assertTrue(attrs.contains(Tag.StudyDescription));
    }

    @Test
    void modifiesExistingTag() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        String originalName = dataset.getString(Tag.PatientName);
        dataset.setString(Tag.PatientName, VR.PN, "Modified^Name");

        assertNotEquals(originalName, dataset.getString(Tag.PatientName));
        assertEquals("Modified^Name", dataset.getString(Tag.PatientName));
    }

    @Test
    void removesTag() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        assertTrue(dataset.contains(Tag.PatientName));
        dataset.remove(Tag.PatientName);
        assertFalse(dataset.contains(Tag.PatientName));
    }

    @Test
    void setsNumericTags() throws Exception {
        Attributes attrs = new Attributes();
        attrs.setInt(Tag.InstanceNumber, VR.IS, 42);
        attrs.setInt(Tag.Rows, VR.US, 512);
        attrs.setInt(Tag.Columns, VR.US, 512);
        attrs.setFloat(Tag.SliceThickness, VR.DS, 1.5f);
        attrs.setDouble(Tag.SliceLocation, VR.DS, 10.5);

        assertEquals(42, attrs.getInt(Tag.InstanceNumber, -1));
        assertEquals(512, attrs.getInt(Tag.Rows, 0));
        assertEquals(512, attrs.getInt(Tag.Columns, 0));
        assertEquals(1.5f, attrs.getFloat(Tag.SliceThickness, 0), 0.001f);
        assertEquals(10.5, attrs.getDouble(Tag.SliceLocation, 0), 0.001);
    }

    @Test
    void setsMultiValueTags() throws Exception {
        Attributes attrs = new Attributes();
        attrs.setDoubles(Tag.PixelSpacing, VR.DS, new double[]{0.5, 0.5});
        attrs.setInts(Tag.WindowCenter, VR.DS, new int[]{-600, 100});
        attrs.setStrings(Tag.FrameOfReferenceUID, VR.UI, new String[]{"1.2.3.4", "5.6.7.8"});

        double[] spacing = attrs.getDoubles(Tag.PixelSpacing);
        assertArrayEquals(new double[]{0.5, 0.5}, spacing, 1e-6);

        int[] centers = attrs.getInts(Tag.WindowCenter);
        assertArrayEquals(new int[]{-600, 100}, centers);
    }

    @Test
    void manipulatesSequenceTags() throws Exception {
        Attributes attrs = new Attributes();
        Sequence seq = attrs.newSequence(Tag.ReferencedImageSequence, 2);

        Attributes item1 = new Attributes();
        item1.setString(Tag.ReferencedSOPInstanceUID, VR.UI, "1.2.3.4.1");
        seq.add(item1);

        Attributes item2 = new Attributes();
        item2.setString(Tag.ReferencedSOPInstanceUID, VR.UI, "1.2.3.4.2");
        seq.add(item2);

        Sequence readSeq = attrs.getSequence(Tag.ReferencedImageSequence);
        assertNotNull(readSeq);
        assertEquals(2, readSeq.size());
        assertEquals("1.2.3.4.1", readSeq.get(0).getString(Tag.ReferencedSOPInstanceUID));
        assertEquals("1.2.3.4.2", readSeq.get(1).getString(Tag.ReferencedSOPInstanceUID));
    }

    @Test
    void preservesTagsAfterRoundTrip() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        // Modifica várias tags
        dataset.setString(Tag.PatientName, VR.PN, "RoundTrip^Test");
        dataset.setInt(Tag.InstanceNumber, VR.IS, 999);
        dataset.setDoubles(Tag.PixelSpacing, VR.DS, new double[]{0.3, 0.3});
        dataset.setString(Tag.StudyDescription, VR.LO, "Modified Study");

        Path output = tempDir.resolve("modified.dcm");
        writeDicom(dataset, output);

        // Lê de volta
        try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
            dis.readFileMetaInformation();
            Attributes read = dis.readDataset(-1, -1);

            assertEquals("RoundTrip^Test", read.getString(Tag.PatientName));
            assertEquals(999, read.getInt(Tag.InstanceNumber, -1));
            assertArrayEquals(new double[]{0.3, 0.3}, read.getDoubles(Tag.PixelSpacing), 1e-6);
            assertEquals("Modified Study", read.getString(Tag.StudyDescription));
        }
    }

    @Test
    void handlesPrivateTags() throws Exception {
        Attributes attrs = new Attributes();
        // Tag privada (grupo ímpar, elemento arbitrário)
        int privateTag = 0x0009 << 16 | 0x0010;
        attrs.setString(privateTag, VR.LO, "Private Data");

        assertTrue(attrs.contains(privateTag));
        assertEquals("Private Data", attrs.getString(privateTag));

        Path output = tempDir.resolve("private_tags.dcm");
        writeDicom(attrs, output);

        // Lê de volta
        try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
            dis.readFileMetaInformation();
            Attributes read = dis.readDataset(-1, -1);
            assertTrue(read.contains(privateTag));
            assertEquals("Private Data", read.getString(privateTag));
        }
    }

    @Test
    void handlesDifferentStringEncodings() throws Exception {
        Attributes attrs = new Attributes();
        attrs.setString(Tag.SOPClassUID, VR.UI, UID.CTImageStorage);
        attrs.setString(Tag.SOPInstanceUID, VR.UI, "1.2.3.4.5");
        attrs.setString(Tag.StudyInstanceUID, VR.UI, "1.2.3.4");
        attrs.setString(Tag.SeriesInstanceUID, VR.UI, "1.2.3.4.1");
        attrs.setString(Tag.PatientID, VR.LO, "TEST123");

        // Testa diferentes tipos de strings
        attrs.setString(Tag.PatientName, VR.PN, "Smith^John^Doe");
        attrs.setString(Tag.StudyDescription, VR.LO, "Long description with spaces");
        attrs.setString(Tag.SeriesDescription, VR.SH, "Short");

        assertEquals("Smith^John^Doe", attrs.getString(Tag.PatientName));
        assertEquals("Long description with spaces", attrs.getString(Tag.StudyDescription));
        assertEquals("Short", attrs.getString(Tag.SeriesDescription));
    }

    @Test
    void handlesDateAndTimeTags() throws Exception {
        Attributes attrs = new Attributes();
        attrs.setString(Tag.StudyDate, VR.DA, "20240101");
        attrs.setString(Tag.StudyTime, VR.TM, "120000");
        attrs.setString(Tag.SeriesDate, VR.DA, "20240102");
        attrs.setString(Tag.SeriesTime, VR.TM, "143025.123");

        assertEquals("20240101", attrs.getString(Tag.StudyDate));
        assertEquals("120000", attrs.getString(Tag.StudyTime));
        assertEquals("20240102", attrs.getString(Tag.SeriesDate));
        assertEquals("143025.123", attrs.getString(Tag.SeriesTime));
    }

    @Test
    void handlesNestedSequences() throws Exception {
        Attributes attrs = new Attributes();
        Sequence outerSeq = attrs.newSequence(Tag.ReferencedStudySequence, 1);
        Attributes outerItem = new Attributes();
        outerItem.setString(Tag.StudyInstanceUID, VR.UI, "1.2.3.4");

        Sequence innerSeq = outerItem.newSequence(Tag.ReferencedSeriesSequence, 1);
        Attributes innerItem = new Attributes();
        innerItem.setString(Tag.SeriesInstanceUID, VR.UI, "1.2.3.4.1");
        innerSeq.add(innerItem);

        outerSeq.add(outerItem);

        Sequence readOuter = attrs.getSequence(Tag.ReferencedStudySequence);
        assertNotNull(readOuter);
        assertEquals(1, readOuter.size());
        
        Attributes readOuterItem = readOuter.get(0);
        Sequence readInner = readOuterItem.getSequence(Tag.ReferencedSeriesSequence);
        assertNotNull(readInner);
        assertEquals(1, readInner.size());
        assertEquals("1.2.3.4.1", readInner.get(0).getString(Tag.SeriesInstanceUID));
    }

    @Test
    void handlesBulkDataTags() throws Exception {
        Attributes attrs = new Attributes();
        byte[] bulkData = new byte[1024];
        for (int i = 0; i < bulkData.length; i++) {
            bulkData[i] = (byte) (i % 256);
        }

        attrs.setBytes(Tag.PixelData, VR.OB, bulkData);

        byte[] readData = attrs.getBytes(Tag.PixelData);
        assertNotNull(readData);
        assertEquals(bulkData.length, readData.length);
        assertArrayEquals(bulkData, readData);
    }

    @Test
    void clearsAllTags() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        int originalSize = dataset.size();
        assertTrue(originalSize > 0);

        // Remove todas as tags exceto algumas obrigatórias
        for (int tag : dataset.tags()) {
            if (tag != Tag.SOPClassUID && tag != Tag.SOPInstanceUID) {
                dataset.remove(tag);
            }
        }

        assertTrue(dataset.size() < originalSize);
        assertTrue(dataset.contains(Tag.SOPClassUID));
        assertTrue(dataset.contains(Tag.SOPInstanceUID));
    }

    @Test
    void handlesTagOverwriting() throws Exception {
        Attributes attrs = new Attributes();
        attrs.setInt(Tag.InstanceNumber, VR.IS, 10);
        assertEquals(10, attrs.getInt(Tag.InstanceNumber, -1));

        // Sobrescreve com novo valor
        attrs.setInt(Tag.InstanceNumber, VR.IS, 20);
        assertEquals(20, attrs.getInt(Tag.InstanceNumber, -1));

        // Sobrescreve com tipo diferente (pode causar problemas, mas testa comportamento)
        attrs.setString(Tag.InstanceNumber, VR.IS, "30");
        assertEquals("30", attrs.getString(Tag.InstanceNumber));
    }

    private void writeDicom(Attributes attrs, Path path) throws IOException {
        Attributes fmi = attrs.createFileMetaInformation(UID.ExplicitVRLittleEndian);
        try (DicomOutputStream dos = new DicomOutputStream(path.toFile())) {
            dos.writeDataset(fmi, attrs);
        }
    }
}
