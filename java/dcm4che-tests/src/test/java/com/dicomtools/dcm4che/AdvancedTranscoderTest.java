package com.dicomtools.dcm4che;

import com.dicomtools.cli.DicomOperations;
import com.dicomtools.cli.OperationResult;
import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.imageio.plugins.dcm.DicomImageReader;
import org.dcm4che3.imageio.plugins.dcm.DicomImageReaderSpi;
import org.dcm4che3.io.DicomInputStream;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.api.Assumptions;

import javax.imageio.ImageIO;
import javax.imageio.stream.ImageInputStream;
import java.awt.image.Raster;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class AdvancedTranscoderTest {

    @TempDir
    Path tempDir;

    @BeforeAll
    static void registerPlugins() {
        ImageIO.scanForPlugins();
    }

    @Test
    void transcodesWithLosslessCodecs() throws Exception {
        Path input = TestData.sampleDicom();
        int baselineSample = samplePixel(input);
        int width = readAttribute(input, Tag.Columns);
        int height = readAttribute(input, Tag.Rows);

        Map<String, String> cases = new LinkedHashMap<>();
        cases.put("jpeg2000", UID.JPEG2000Lossless);
        cases.put("rle", UID.RLELossless);
        cases.put("deflated", UID.DeflatedExplicitVRLittleEndian);

        for (Map.Entry<String, String> entry : cases.entrySet()) {
            Path output = tempDir.resolve("transcoded-" + entry.getKey() + ".dcm");
            try {
                OperationResult result = DicomOperations.transcode(input, output, entry.getKey());
                assertTrue(result.isSuccess(), "Transcode should succeed for " + entry.getKey());
                try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
                    Attributes fmi = dis.readFileMetaInformation();
                    Attributes dataset = dis.readDataset(-1, -1);
                    assertEquals(entry.getValue(), fmi.getString(Tag.TransferSyntaxUID));
                    assertEquals(width, dataset.getInt(Tag.Columns, -1));
                    assertEquals(height, dataset.getInt(Tag.Rows, -1));
                }
                assertEquals(baselineSample, samplePixel(output), "Pixel sample should survive " + entry.getKey());
            } catch (RuntimeException ex) {
                Assumptions.assumeFalse(isMissingCodec(ex), "Skipping " + entry.getKey() + " codec: " + ex.getMessage());
            }
        }
    }

    private int samplePixel(Path dicom) throws Exception {
        try (ImageInputStream iis = ImageIO.createImageInputStream(dicom.toFile())) {
            DicomImageReader reader = new DicomImageReader(new DicomImageReaderSpi());
            reader.setInput(iis);
            Raster raster = reader.readRaster(0, null);
            int sample = raster.getSample(0, 0, 0);
            reader.dispose();
            return sample;
        }
    }

    private int readAttribute(Path dicom, int tag) throws Exception {
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            return dis.readDataset(-1, -1).getInt(tag, -1);
        }
    }

    private boolean isMissingCodec(RuntimeException ex) {
        String msg = ex.getMessage();
        return msg != null && msg.toLowerCase().contains("no writer for format");
    }
}
