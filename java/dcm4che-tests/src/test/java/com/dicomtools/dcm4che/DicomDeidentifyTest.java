package com.dicomtools.dcm4che;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Path;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Sequence;
import org.dcm4che3.data.Tag;
import org.dcm4che3.deident.DeIdentifier;
import org.dcm4che3.io.DicomInputStream;
import org.junit.jupiter.api.Test;

class DicomDeidentifyTest {

    @Test
    void stripsPhiAndMarksDatasetAsDeidentified() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        Attributes deidentified = new Attributes(dataset);
        String originalName = dataset.getString(Tag.PatientName);
        String originalId = dataset.getString(Tag.PatientID);
        String originalSopInstanceUid = dataset.getString(Tag.SOPInstanceUID);

        DeIdentifier deIdentifier = new DeIdentifier(
                DeIdentifier.Option.RetainUIDsOption,
                DeIdentifier.Option.RetainPatientIDHashOption);
        deIdentifier.deidentify(deidentified);

        assertEquals("YES", deidentified.getString(Tag.PatientIdentityRemoved));
        assertEquals(originalSopInstanceUid, deidentified.getString(Tag.SOPInstanceUID));

        String scrubbedName = deidentified.getString(Tag.PatientName);
        assertNotEquals(originalName, scrubbedName);

        String scrubbedId = deidentified.getString(Tag.PatientID);
        assertNotEquals(originalId, scrubbedId);
        assertNotNull(scrubbedId, "PatientID should be replaced with a hash");

        Sequence methods = deidentified.getSequence(Tag.DeidentificationMethodCodeSequence);
        assertNotNull(methods, "DeidentificationMethodCodeSequence should be populated");
        assertTrue(methods.size() >= 1, "Should record at least one deidentification method");
    }
}
