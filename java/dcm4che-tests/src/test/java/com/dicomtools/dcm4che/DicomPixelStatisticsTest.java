package com.dicomtools.dcm4che;

import static org.junit.jupiter.api.Assertions.assertTrue;

import java.awt.image.BufferedImage;
import java.awt.image.Raster;
import java.nio.file.Path;
import java.util.Iterator;

import javax.imageio.ImageIO;
import javax.imageio.ImageReader;
import javax.imageio.stream.ImageInputStream;

import org.junit.jupiter.api.Test;

class DicomPixelStatisticsTest {

    @Test
    void computesMinMaxPixelValues() throws Exception {
        ImageIO.scanForPlugins();
        Path dicom = TestData.sampleDicom();

        int min = Integer.MAX_VALUE;
        int max = Integer.MIN_VALUE;

        try (ImageInputStream iis = ImageIO.createImageInputStream(dicom.toFile())) {
            Iterator<ImageReader> readers = ImageIO.getImageReadersByFormatName("DICOM");
            ImageReader reader = readers.next();
            reader.setInput(iis);
            BufferedImage image = reader.read(0);
            reader.dispose();

            Raster raster = image.getRaster();
            for (int y = 0; y < raster.getHeight(); y++) {
                for (int x = 0; x < raster.getWidth(); x++) {
                    int sample = raster.getSample(x, y, 0);
                    min = Math.min(min, sample);
                    max = Math.max(max, sample);
                }
            }
        }

        assertTrue(min >= 0, "Min pixel should be non-negative for this CT sample");
        assertTrue(max > min, "Expected dynamic range in pixel values");
    }
}
