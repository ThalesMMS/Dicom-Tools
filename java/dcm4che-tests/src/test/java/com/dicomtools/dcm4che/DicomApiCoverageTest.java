package com.dicomtools.dcm4che;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.data.VR;
import org.dcm4che3.imageio.plugins.dcm.DicomImageReadParam;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.io.DicomOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import javax.imageio.ImageIO;
import javax.imageio.ImageReader;
import javax.imageio.stream.ImageInputStream;
import java.awt.image.Raster;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Iterator;

import static org.junit.jupiter.api.Assertions.*;

class DicomApiCoverageTest {

    @TempDir
    Path tempDir;

    @Test
    void dicomInputStreamReadsDatasetAndMeta() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            Attributes fmi = dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            assertNotNull(fmi, "File meta should be present");
            assertEquals(UID.CTImageStorage, fmi.getString(Tag.MediaStorageSOPClassUID));
            assertEquals(fmi.getString(Tag.TransferSyntaxUID), dis.getTransferSyntax());

            assertNotNull(dataset.getString(Tag.PatientName));
            assertTrue(dataset.contains(Tag.PixelData), "Pixel Data must be present");
        }
    }

    @Test
    void attributesCanBeEditedAndSaved() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        dataset.setString(Tag.PatientName, VR.PN, "TEST^EDITED");
        dataset.setInt(Tag.InstanceNumber, VR.IS, 42);
        dataset.remove(Tag.OtherPatientIDs);
        Attributes fmi = dataset.createFileMetaInformation(UID.ExplicitVRLittleEndian);

        Path out = tempDir.resolve("edited.dcm");
        try (DicomOutputStream dos = new DicomOutputStream(out.toFile())) {
            dos.writeDataset(fmi, dataset);
        }

        try (DicomInputStream dis = new DicomInputStream(out.toFile())) {
            dis.readFileMetaInformation();
            Attributes reread = dis.readDataset(-1, -1);
            assertEquals("TEST^EDITED", reread.getString(Tag.PatientName));
            assertEquals(42, reread.getInt(Tag.InstanceNumber, -1));
            assertFalse(reread.contains(Tag.OtherPatientIDs));
        }
    }

    @Test
    void rawRasterCanBeReadViaImageIoPlugin() throws Exception {
        ImageIO.scanForPlugins();
        Path dicom = TestData.sampleDicom();
        try (ImageInputStream iis = ImageIO.createImageInputStream(dicom.toFile())) {
            Iterator<ImageReader> readers = ImageIO.getImageReadersByFormatName("DICOM");
            assertTrue(readers.hasNext(), "Expected DICOM ImageIO reader");
            ImageReader reader = readers.next();
            reader.setInput(iis);
            DicomImageReadParam param = (DicomImageReadParam) reader.getDefaultReadParam();
            Raster raster = reader.readRaster(0, param);
            reader.dispose();

            assertNotNull(raster);
            assertEquals(512, raster.getWidth());
            assertEquals(512, raster.getHeight());

            int[] probeXs = {0, raster.getWidth() / 2, raster.getWidth() - 1};
            int[] probeYs = {0, raster.getHeight() / 2, raster.getHeight() - 1};
            boolean foundNonZero = false;
            for (int x : probeXs) {
                for (int y : probeYs) {
                    if (raster.getSample(x, y, 0) != 0) {
                        foundNonZero = true;
                        break;
                    }
                }
                if (foundNonZero) break;
            }
            assertTrue(foundNonZero, "Expected at least one non-zero sample in raster probes");
        }
    }
}
