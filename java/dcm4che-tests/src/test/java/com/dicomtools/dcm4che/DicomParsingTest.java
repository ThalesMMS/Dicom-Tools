package com.dicomtools.dcm4che;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Path;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.io.DicomInputStream;
import org.junit.jupiter.api.Test;

class DicomParsingTest {

    @Test
    void readsCoreMetadataFromDisk() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes fileMeta;
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            fileMeta = dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        assertEquals(UID.CTImageStorage, fileMeta.getString(Tag.MediaStorageSOPClassUID));
        assertEquals("CT", dataset.getString(Tag.Modality));
        assertEquals("CEREBRIX", dataset.getString(Tag.PatientName));
        assertEquals("XsxuId", dataset.getString(Tag.PatientID));
        assertEquals("19350401", dataset.getString(Tag.PatientBirthDate));
        assertEquals("0000", dataset.getString(Tag.PatientSex));
        assertEquals("000Y", dataset.getString(Tag.PatientAge));
        assertEquals(512, dataset.getInt(Tag.Rows, 0));
        assertEquals(512, dataset.getInt(Tag.Columns, 0));
    }

    @Test
    void exposesSpatialInformationAndPixelData() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        double[] spacing = dataset.getDoubles(Tag.PixelSpacing);
        assertArrayEquals(new double[] {0.48828125, 0.48828125}, spacing, 1e-6);

        double[] orientation = dataset.getDoubles(Tag.ImageOrientationPatient);
        assertNotNull(orientation);
        assertEquals(6, orientation.length);
        assertEquals(1.0, orientation[0], 1e-6);
        assertEquals(1.0, orientation[4], 1e-6);

        assertTrue(dataset.contains(Tag.PixelData), "Pixel data is present");
    }
}
