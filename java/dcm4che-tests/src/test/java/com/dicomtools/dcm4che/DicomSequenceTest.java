package com.dicomtools.dcm4che;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

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
 * Tests dcm4che Sequence manipulation: creation, iteration, nesting, and persistence.
 */
class DicomSequenceTest {

    @TempDir
    Path tempDir;

    @Test
    void createsAndPopulatesSequence() {
        Attributes dataset = new Attributes();

        Sequence seq = dataset.newSequence(Tag.ReferencedStudySequence, 2);
        assertNotNull(seq, "Sequence should be created");
        assertEquals(0, seq.size(), "Sequence should initially be empty");

        Attributes item1 = new Attributes();
        item1.setString(Tag.ReferencedSOPClassUID, VR.UI, UID.CTImageStorage);
        item1.setString(Tag.ReferencedSOPInstanceUID, VR.UI, "1.2.3.4.5");
        seq.add(item1);

        Attributes item2 = new Attributes();
        item2.setString(Tag.ReferencedSOPClassUID, VR.UI, UID.MRImageStorage);
        item2.setString(Tag.ReferencedSOPInstanceUID, VR.UI, "1.2.3.4.6");
        seq.add(item2);

        assertEquals(2, seq.size(), "Sequence should contain two items");
    }

    @Test
    void iteratesOverSequenceItems() {
        Attributes dataset = new Attributes();
        Sequence seq = dataset.newSequence(Tag.OtherPatientIDsSequence, 3);

        for (int i = 0; i < 3; i++) {
            Attributes item = new Attributes();
            item.setString(Tag.PatientID, VR.LO, "ID_" + i);
            item.setString(Tag.TypeOfPatientID, VR.CS, "TEXT");
            seq.add(item);
        }

        int count = 0;
        for (Attributes item : seq) {
            assertNotNull(item.getString(Tag.PatientID));
            assertTrue(item.getString(Tag.PatientID).startsWith("ID_"));
            count++;
        }
        assertEquals(3, count, "Should iterate over all items");
    }

    @Test
    void createsNestedSequences() {
        Attributes dataset = new Attributes();
        Sequence outerSeq = dataset.newSequence(Tag.ContentSequence, 1);

        Attributes outerItem = new Attributes();
        outerItem.setString(Tag.ValueType, VR.CS, "CONTAINER");

        Sequence innerSeq = outerItem.newSequence(Tag.ContentSequence, 2);
        Attributes innerItem1 = new Attributes();
        innerItem1.setString(Tag.ValueType, VR.CS, "TEXT");
        innerItem1.setString(Tag.TextValue, VR.UT, "Nested text 1");
        innerSeq.add(innerItem1);

        Attributes innerItem2 = new Attributes();
        innerItem2.setString(Tag.ValueType, VR.CS, "TEXT");
        innerItem2.setString(Tag.TextValue, VR.UT, "Nested text 2");
        innerSeq.add(innerItem2);

        outerSeq.add(outerItem);

        // Verify nesting
        Sequence retrieved = dataset.getSequence(Tag.ContentSequence);
        assertNotNull(retrieved);
        assertEquals(1, retrieved.size());

        Attributes retrievedOuter = retrieved.get(0);
        Sequence retrievedInner = retrievedOuter.getSequence(Tag.ContentSequence);
        assertNotNull(retrievedInner);
        assertEquals(2, retrievedInner.size());
        assertEquals("Nested text 1", retrievedInner.get(0).getString(Tag.TextValue));
    }

    @Test
    void removesSequenceItems() {
        Attributes dataset = new Attributes();
        Sequence seq = dataset.newSequence(Tag.ReferencedSeriesSequence, 3);

        for (int i = 0; i < 3; i++) {
            Attributes item = new Attributes();
            item.setString(Tag.SeriesInstanceUID, VR.UI, "1.2.3." + i);
            seq.add(item);
        }

        assertEquals(3, seq.size());

        Attributes removed = seq.remove(1);
        assertEquals("1.2.3.1", removed.getString(Tag.SeriesInstanceUID));
        assertEquals(2, seq.size());

        seq.clear();
        assertEquals(0, seq.size());
    }

    @Test
    void persistsSequenceToFile() throws Exception {
        Attributes dataset = new Attributes();
        dataset.setString(Tag.PatientName, VR.PN, "Test^Patient");
        dataset.setString(Tag.PatientID, VR.LO, "12345");
        dataset.setString(Tag.Modality, VR.CS, "OT");
        dataset.setString(Tag.SOPClassUID, VR.UI, UID.SecondaryCaptureImageStorage);
        dataset.setString(Tag.SOPInstanceUID, VR.UI, "1.2.3.4.5.6.7.8.9");

        Sequence seq = dataset.newSequence(Tag.ReferencedStudySequence, 2);
        for (int i = 0; i < 2; i++) {
            Attributes item = new Attributes();
            item.setString(Tag.ReferencedSOPClassUID, VR.UI, UID.CTImageStorage);
            item.setString(Tag.ReferencedSOPInstanceUID, VR.UI, "1.2.3.4." + i);
            seq.add(item);
        }

        Attributes fmi = dataset.createFileMetaInformation(UID.ExplicitVRLittleEndian);
        Path output = tempDir.resolve("sequence_test.dcm");
        try (DicomOutputStream dos = new DicomOutputStream(output.toFile())) {
            dos.writeDataset(fmi, dataset);
        }

        // Read back and verify
        try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
            dis.readFileMetaInformation();
            Attributes reread = dis.readDataset(-1, -1);

            Sequence rereadSeq = reread.getSequence(Tag.ReferencedStudySequence);
            assertNotNull(rereadSeq, "Sequence should survive round trip");
            assertEquals(2, rereadSeq.size());
            assertEquals("1.2.3.4.0", rereadSeq.get(0).getString(Tag.ReferencedSOPInstanceUID));
            assertEquals("1.2.3.4.1", rereadSeq.get(1).getString(Tag.ReferencedSOPInstanceUID));
        }
    }

    @Test
    void handlesEmptySequence() {
        Attributes dataset = new Attributes();
        Sequence seq = dataset.newSequence(Tag.ReferencedImageSequence, 0);

        assertNotNull(seq);
        assertEquals(0, seq.size());
        assertTrue(seq.isEmpty());

        // Retrieving non-existent sequence returns null
        Sequence nonExistent = dataset.getSequence(Tag.ReferencedSeriesSequence);
        assertNull(nonExistent);
    }

    @Test
    void accessesSequenceItemsByIndex() {
        Attributes dataset = new Attributes();
        Sequence seq = dataset.newSequence(Tag.ProcedureCodeSequence, 3);

        String[] codes = {"CODE_A", "CODE_B", "CODE_C"};
        for (String code : codes) {
            Attributes item = new Attributes();
            item.setString(Tag.CodeValue, VR.SH, code);
            item.setString(Tag.CodingSchemeDesignator, VR.SH, "99LOCAL");
            item.setString(Tag.CodeMeaning, VR.LO, "Meaning of " + code);
            seq.add(item);
        }

        assertEquals("CODE_A", seq.get(0).getString(Tag.CodeValue));
        assertEquals("CODE_B", seq.get(1).getString(Tag.CodeValue));
        assertEquals("CODE_C", seq.get(2).getString(Tag.CodeValue));

        // Modify in place
        seq.get(1).setString(Tag.CodeValue, VR.SH, "CODE_B_MODIFIED");
        assertEquals("CODE_B_MODIFIED", seq.get(1).getString(Tag.CodeValue));
    }
}
