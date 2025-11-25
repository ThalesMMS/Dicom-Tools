package com.dicomtools.dcm4che;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Sequence;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.data.VR;
import org.dcm4che3.imageio.plugins.dcm.DicomImageReadParam;
import org.dcm4che3.imageio.plugins.dcm.DicomImageReader;
import org.dcm4che3.imageio.plugins.dcm.DicomImageReaderSpi;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.io.DicomOutputStream;
import org.dcm4che3.util.UIDUtils;
import org.junit.jupiter.api.Test;

import javax.imageio.stream.ImageInputStream;
import java.awt.image.Raster;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

class EnhancedMultiframeTest {

    @Test
    void readsEnhancedMultiframeDatasetWithFunctionalGroups() throws Exception {
        byte[] dicom = buildEnhancedMultiframe();

        try (ImageInputStream iis = javax.imageio.ImageIO.createImageInputStream(new ByteArrayInputStream(dicom))) {
            DicomImageReader reader = new DicomImageReader(new DicomImageReaderSpi());
            reader.setInput(iis);
            DicomImageReadParam param = (DicomImageReadParam) reader.getDefaultReadParam();
            assertEquals(2, reader.getNumImages(true));

            Raster frame0 = reader.readRaster(0, param);
            Raster frame1 = reader.readRaster(1, param);
            reader.dispose();

            assertEquals(3, frame0.getWidth());
            assertEquals(2, frame0.getHeight());
            assertEquals(0, frame0.getSample(0, 0, 0));
            assertEquals(50, frame1.getSample(0, 0, 0));
        }

        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(new ByteArrayInputStream(dicom))) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        assertEquals(2, dataset.getInt(Tag.NumberOfFrames, -1));
        Sequence shared = dataset.getSequence(Tag.SharedFunctionalGroupsSequence);
        assertNotNull(shared);
        double[] spacing = shared.get(0).getSequence(Tag.PixelMeasuresSequence).get(0).getDoubles(Tag.PixelSpacing);
        assertArrayEquals(new double[]{0.8, 0.8}, spacing, 1e-6);
        double thickness = shared.get(0).getSequence(Tag.PixelMeasuresSequence).get(0).getDouble(Tag.SliceThickness, -1.0);
        assertEquals(1.5, thickness, 1e-6);

        Sequence perFrame = dataset.getSequence(Tag.PerFrameFunctionalGroupsSequence);
        assertNotNull(perFrame);
        double[] frame0Pos = perFrame.get(0).getSequence(Tag.PlanePositionSequence).get(0).getDoubles(Tag.ImagePositionPatient);
        double[] frame1Pos = perFrame.get(1).getSequence(Tag.PlanePositionSequence).get(0).getDoubles(Tag.ImagePositionPatient);
        assertEquals(0.0, frame0Pos[2], 1e-6);
        assertEquals(1.5, frame1Pos[2], 1e-6);
    }

    private byte[] buildEnhancedMultiframe() throws Exception {
        Attributes dataset = new Attributes();
        dataset.setString(Tag.SOPClassUID, VR.UI, UID.EnhancedMRImageStorage);
        dataset.setString(Tag.SOPInstanceUID, VR.UI, UIDUtils.createUID());
        dataset.setString(Tag.StudyInstanceUID, VR.UI, UIDUtils.createUID());
        dataset.setString(Tag.SeriesInstanceUID, VR.UI, UIDUtils.createUID());
        dataset.setString(Tag.Modality, VR.CS, "MR");
        dataset.setInt(Tag.Rows, VR.US, 2);
        dataset.setInt(Tag.Columns, VR.US, 3);
        dataset.setInt(Tag.NumberOfFrames, VR.IS, 2);
        dataset.setInt(Tag.SamplesPerPixel, VR.US, 1);
        dataset.setString(Tag.PhotometricInterpretation, VR.CS, "MONOCHROME2");
        dataset.setInt(Tag.BitsAllocated, VR.US, 16);
        dataset.setInt(Tag.BitsStored, VR.US, 12);
        dataset.setInt(Tag.HighBit, VR.US, 11);
        dataset.setInt(Tag.PixelRepresentation, VR.US, 0);

        Attributes shared = new Attributes();
        Sequence pixelMeasures = shared.newSequence(Tag.PixelMeasuresSequence, 1);
        Attributes measures = new Attributes();
        measures.setString(Tag.PixelSpacing, VR.DS, "0.8\\0.8");
        measures.setDouble(Tag.SliceThickness, VR.DS, 1.5);
        pixelMeasures.add(measures);
        Attributes orientation = new Attributes();
        orientation.setString(Tag.ImageOrientationPatient, VR.DS, "1\\0\\0\\0\\1\\0");
        shared.newSequence(Tag.PlaneOrientationSequence, 1).add(orientation);
        dataset.newSequence(Tag.SharedFunctionalGroupsSequence, 1).add(shared);

        Sequence perFrame = dataset.newSequence(Tag.PerFrameFunctionalGroupsSequence, 2);
        for (int i = 0; i < 2; i++) {
            Attributes frame = new Attributes();
            Attributes frameContent = new Attributes();
            frameContent.setString(Tag.StackID, VR.SH, "1");
            frameContent.setInt(Tag.InStackPositionNumber, VR.IS, i + 1);
            frameContent.setInt(Tag.DimensionIndexValues, VR.UL, i + 1);
            frame.newSequence(Tag.FrameContentSequence, 1).add(frameContent);

            Attributes position = new Attributes();
            position.setString(Tag.ImagePositionPatient, VR.DS, "0\\0\\" + (1.5 * i));
            frame.newSequence(Tag.PlanePositionSequence, 1).add(position);
            perFrame.add(frame);
        }

        short[] pixels = new short[]{
                0, 1, 2,
                3, 4, 5,
                50, 51, 52,
                53, 54, 55
        };
        byte[] pixelBytes = new byte[pixels.length * 2];
        ByteBuffer.wrap(pixelBytes).order(ByteOrder.LITTLE_ENDIAN).asShortBuffer().put(pixels);
        dataset.setBytes(Tag.PixelData, VR.OW, pixelBytes);

        try (ByteArrayOutputStream bos = new ByteArrayOutputStream();
             DicomOutputStream dos = new DicomOutputStream(bos, UID.ExplicitVRLittleEndian)) {
            dos.writeDataset(dataset.createFileMetaInformation(UID.ExplicitVRLittleEndian), dataset);
            return bos.toByteArray();
        }
    }
}
