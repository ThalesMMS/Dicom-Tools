package com.dicomtools.dcm4che;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.nio.file.Path;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.data.VR;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.io.DicomOutputStream;
import org.junit.jupiter.api.Test;

class DicomRoundTripTest {

    @Test
    void roundTripsDatasetWithExplicitLittleEndian() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        String originalInstanceUid = dataset.getString(Tag.SOPInstanceUID);
        int rows = dataset.getInt(Tag.Rows, 0);
        double[] pixelSpacing = dataset.getDoubles(Tag.PixelSpacing);

        dataset.setString(Tag.PatientName, VR.PN, "ROUNDTRIP^TEST");
        Attributes fileMeta = dataset.createFileMetaInformation(UID.ExplicitVRLittleEndian);

        byte[] serialized;
        try (ByteArrayOutputStream bos = new ByteArrayOutputStream();
             DicomOutputStream dos = new DicomOutputStream(bos, UID.ExplicitVRLittleEndian)) {
            dos.writeDataset(fileMeta, dataset);
            serialized = bos.toByteArray();
        }

        assertTrue(serialized.length > 0, "Serialized DICOM should not be empty");

        try (DicomInputStream dis = new DicomInputStream(new ByteArrayInputStream(serialized))) {
            Attributes readFileMeta = dis.readFileMetaInformation();
            Attributes roundTripped = dis.readDataset(-1, -1);

            assertEquals(UID.ExplicitVRLittleEndian, readFileMeta.getString(Tag.TransferSyntaxUID));
            assertEquals(originalInstanceUid, roundTripped.getString(Tag.SOPInstanceUID));
            assertEquals("ROUNDTRIP^TEST", roundTripped.getString(Tag.PatientName));
            assertEquals(rows, roundTripped.getInt(Tag.Rows, 0));
            assertArrayEquals(pixelSpacing, roundTripped.getDoubles(Tag.PixelSpacing), 1e-6);
        }
    }
}
