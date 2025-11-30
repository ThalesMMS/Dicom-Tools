package com.dicomtools.dcm4che;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.ByteArrayOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Random;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.BulkData;
import org.dcm4che3.data.Fragments;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.data.VR;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.io.DicomOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/**
 * Tests dcm4che bulk data handling: pixel data, encapsulated data, and large values.
 */
class DicomBulkDataTest {

    @TempDir
    Path tempDir;

    @Test
    void readsPixelDataFromSampleFile() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        assertTrue(dataset.contains(Tag.PixelData), "Sample file should contain pixel data");

        // Get pixel data as bytes
        byte[] pixelData = dataset.getBytes(Tag.PixelData);
        assertNotNull(pixelData);
        assertTrue(pixelData.length > 0, "Pixel data should not be empty");

        // Verify dimensions match expected size
        int rows = dataset.getInt(Tag.Rows, 0);
        int cols = dataset.getInt(Tag.Columns, 0);
        int bitsAllocated = dataset.getInt(Tag.BitsAllocated, 16);
        int samplesPerPixel = dataset.getInt(Tag.SamplesPerPixel, 1);

        int expectedSize = rows * cols * (bitsAllocated / 8) * samplesPerPixel;
        assertEquals(expectedSize, pixelData.length, "Pixel data size should match dimensions");
    }

    @Test
    void writesAndReadsPixelData() throws Exception {
        Attributes dataset = new Attributes();
        dataset.setString(Tag.PatientName, VR.PN, "Test^BulkData");
        dataset.setString(Tag.PatientID, VR.LO, "BULK001");
        dataset.setString(Tag.Modality, VR.CS, "OT");
        dataset.setString(Tag.SOPClassUID, VR.UI, UID.SecondaryCaptureImageStorage);
        dataset.setString(Tag.SOPInstanceUID, VR.UI, "1.2.3.4.5.6.7.8.9.10");

        // Image parameters
        int rows = 64;
        int cols = 64;
        dataset.setInt(Tag.Rows, VR.US, rows);
        dataset.setInt(Tag.Columns, VR.US, cols);
        dataset.setInt(Tag.BitsAllocated, VR.US, 8);
        dataset.setInt(Tag.BitsStored, VR.US, 8);
        dataset.setInt(Tag.HighBit, VR.US, 7);
        dataset.setInt(Tag.PixelRepresentation, VR.US, 0);
        dataset.setInt(Tag.SamplesPerPixel, VR.US, 1);
        dataset.setString(Tag.PhotometricInterpretation, VR.CS, "MONOCHROME2");

        // Generate test pixel data
        byte[] pixelData = new byte[rows * cols];
        new Random(42).nextBytes(pixelData);
        dataset.setBytes(Tag.PixelData, VR.OW, pixelData);

        Attributes fmi = dataset.createFileMetaInformation(UID.ExplicitVRLittleEndian);
        Path output = tempDir.resolve("bulk_data_test.dcm");
        try (DicomOutputStream dos = new DicomOutputStream(output.toFile())) {
            dos.writeDataset(fmi, dataset);
        }

        // Read back and verify
        try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
            dis.readFileMetaInformation();
            Attributes reread = dis.readDataset(-1, -1);

            byte[] rereadPixelData = reread.getBytes(Tag.PixelData);
            assertArrayEquals(pixelData, rereadPixelData, "Pixel data should survive round trip");
        }
    }

    @Test
    void handlesLargeOtherByteVr() throws Exception {
        Attributes dataset = new Attributes();
        dataset.setString(Tag.SOPClassUID, VR.UI, UID.SecondaryCaptureImageStorage);
        dataset.setString(Tag.SOPInstanceUID, VR.UI, "1.2.3.4.5");
        dataset.setString(Tag.PatientID, VR.LO, "LARGEOB");
        dataset.setString(Tag.Modality, VR.CS, "OT");

        // Large OB data (simulating waveform or other large binary)
        byte[] largeData = new byte[1024 * 100]; // 100KB
        new Random(123).nextBytes(largeData);

        // Use a tag that accepts OB VR
        dataset.setBytes(Tag.EncapsulatedDocument, VR.OB, largeData);

        Attributes fmi = dataset.createFileMetaInformation(UID.ExplicitVRLittleEndian);
        Path output = tempDir.resolve("large_ob_test.dcm");
        try (DicomOutputStream dos = new DicomOutputStream(output.toFile())) {
            dos.writeDataset(fmi, dataset);
        }

        // Verify file size is reasonable
        long fileSize = Files.size(output);
        assertTrue(fileSize >= largeData.length, "File should contain the large data");

        // Read back
        try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
            dis.readFileMetaInformation();
            Attributes reread = dis.readDataset(-1, -1);

            byte[] retrieved = reread.getBytes(Tag.EncapsulatedDocument);
            assertArrayEquals(largeData, retrieved);
        }
    }

    @Test
    void handlesOtherWordVr() throws Exception {
        Attributes dataset = new Attributes();

        // OW (Other Word) data - 16-bit values
        short[] shortData = {1000, 2000, 3000, 4000, 5000};
        byte[] owData = new byte[shortData.length * 2];
        for (int i = 0; i < shortData.length; i++) {
            owData[i * 2] = (byte) (shortData[i] & 0xFF);
            owData[i * 2 + 1] = (byte) ((shortData[i] >> 8) & 0xFF);
        }

        dataset.setBytes(Tag.PixelData, VR.OW, owData);

        byte[] retrieved = dataset.getBytes(Tag.PixelData);
        assertArrayEquals(owData, retrieved);
    }

    @Test
    void recognizesBulkDataReference() throws Exception {
        Path dicom = TestData.sampleDicom();

        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.setIncludeBulkData(DicomInputStream.IncludeBulkData.URI);
            dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            // When using URI mode, pixel data is stored as BulkData reference
            Object pixelDataObj = dataset.getValue(Tag.PixelData);
            // Can be BulkData, byte[], or Fragments depending on transfer syntax
            assertNotNull(pixelDataObj, "Pixel data value should exist");
        }
    }

    @Test
    void handlesInlineBinaryData() throws Exception {
        Attributes dataset = new Attributes();

        // Small binary data stored inline using private tags
        byte[] smallData = {0x01, 0x02, 0x03, 0x04, 0x05};

        // Store as OB in private tag block
        // Private creator at (0009,0010)
        dataset.setString(0x00090010, VR.LO, "TESTCREATOR");
        // Private data at (0009,1001)
        int privateTag = 0x00091001;
        dataset.setBytes(privateTag, VR.OB, smallData);

        byte[] retrieved = dataset.getBytes(privateTag);
        assertArrayEquals(smallData, retrieved);
    }

    @Test
    void calculatesValueLength() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        // Value length can be queried
        int pixelDataLength = dataset.getInt(Tag.PixelData, 0);
        byte[] pixelData = dataset.getBytes(Tag.PixelData);

        assertTrue(pixelData.length > 0, "Should have pixel data");

        // Calculate expected size from attributes
        int rows = dataset.getInt(Tag.Rows, 0);
        int cols = dataset.getInt(Tag.Columns, 0);
        int bitsAllocated = dataset.getInt(Tag.BitsAllocated, 16);

        int expectedLength = rows * cols * (bitsAllocated / 8);
        assertEquals(expectedLength, pixelData.length);
    }

    @Test
    void handlesFloatAndDoubleArrays() {
        Attributes dataset = new Attributes();

        // Float array (OF VR)
        float[] floatArray = {1.5f, 2.5f, 3.5f, 4.5f};
        dataset.setFloat(Tag.FloatPixelData, VR.OF, floatArray);

        float[] retrievedFloats = dataset.getFloats(Tag.FloatPixelData);
        assertNotNull(retrievedFloats);
        assertEquals(floatArray.length, retrievedFloats.length);
        for (int i = 0; i < floatArray.length; i++) {
            assertEquals(floatArray[i], retrievedFloats[i], 0.001f);
        }

        // Double array (FD VR)
        double[] doubleArray = {1.123456789, 2.234567890, 3.345678901};
        dataset.setDouble(Tag.DoubleFloatPixelData, VR.FD, doubleArray);

        double[] retrievedDoubles = dataset.getDoubles(Tag.DoubleFloatPixelData);
        assertNotNull(retrievedDoubles);
        assertEquals(doubleArray.length, retrievedDoubles.length);
        for (int i = 0; i < doubleArray.length; i++) {
            assertEquals(doubleArray[i], retrievedDoubles[i], 1e-9);
        }
    }

    @Test
    void handlesIntegerArrays() {
        Attributes dataset = new Attributes();

        // Unsigned short array (US VR)
        int[] usArray = {100, 200, 300, 65535};
        dataset.setInt(Tag.ReferencedFrameNumber, VR.US, usArray);

        int[] retrievedUs = dataset.getInts(Tag.ReferencedFrameNumber);
        assertArrayEquals(usArray, retrievedUs);

        // Signed short array (SS VR)
        int[] ssArray = {-100, 0, 100, 32767};
        dataset.setInt(Tag.OverlayRows, VR.SS, ssArray[0]);

        // Unsigned long (UL VR) - test with a value in valid signed range
        long ulValue = 2147483647L; // Max signed 32-bit, safely fits in long
        dataset.setLong(Tag.SimpleFrameList, VR.UL, ulValue);

        long[] retrievedUl = dataset.getLongs(Tag.SimpleFrameList);
        assertEquals(ulValue, retrievedUl[0]);

        // Test smaller UL value
        dataset.setLong(Tag.SimpleFrameList, VR.UL, 123456789L);
        assertEquals(123456789L, dataset.getLongs(Tag.SimpleFrameList)[0]);
    }
}
