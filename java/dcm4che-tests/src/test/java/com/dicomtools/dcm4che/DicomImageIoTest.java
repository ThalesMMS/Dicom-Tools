package com.dicomtools.dcm4che;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.awt.image.BufferedImage;
import java.awt.image.Raster;
import java.nio.file.Path;
import java.util.Iterator;

import javax.imageio.ImageIO;
import javax.imageio.ImageReader;
import javax.imageio.stream.ImageInputStream;

import org.junit.jupiter.api.Test;

class DicomImageIoTest {

    @Test
    void decodesPixelDataWithImageIoPlugin() throws Exception {
        ImageIO.scanForPlugins();
        Path dicom = TestData.sampleDicom();

        try (ImageInputStream iis = ImageIO.createImageInputStream(dicom.toFile())) {
            Iterator<ImageReader> readers = ImageIO.getImageReadersByFormatName("DICOM");
            assertTrue(readers.hasNext(), "DICOM ImageIO plugin not registered");

            ImageReader reader = readers.next();
            reader.setInput(iis);
            BufferedImage image = reader.read(0);
            reader.dispose();

            assertNotNull(image);
            assertEquals(512, image.getWidth());
            assertEquals(512, image.getHeight());

            Raster raster = image.getRaster();
            int[] xs = {0, image.getWidth() / 2, image.getWidth() - 1};
            int[] ys = {0, image.getHeight() / 2, image.getHeight() - 1};
            boolean foundNonZero = false;
            for (int x : xs) {
                for (int y : ys) {
                    if (raster.getSample(x, y, 0) != 0) {
                        foundNonZero = true;
                        break;
                    }
                }
                if (foundNonZero) {
                    break;
                }
            }
            assertTrue(foundNonZero, "Expected at least one non-zero sample among inspected pixels");
        }
    }
}
