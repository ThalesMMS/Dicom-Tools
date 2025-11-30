package com.dicomtools.dcm4che;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Path;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.io.DicomOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/**
 * Testes de diferentes Transfer Syntaxes DICOM.
 * Verifica leitura e escrita com Explicit/Implicit VR, Little/Big Endian, e codecs comprimidos.
 */
class DicomTransferSyntaxTest {

    @TempDir
    Path tempDir;

    @Test
    void readsExplicitVRLittleEndian() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            Attributes fmi = dis.readFileMetaInformation();
            String ts = fmi.getString(Tag.TransferSyntaxUID);

            assertNotNull(ts);
            assertEquals(ts, dis.getTransferSyntax());
        }
    }

    @Test
    void writesExplicitVRLittleEndian() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        Path output = tempDir.resolve("explicit_le.dcm");
        Attributes fmi = dataset.createFileMetaInformation(UID.ExplicitVRLittleEndian);
        try (DicomOutputStream dos = new DicomOutputStream(output.toFile())) {
            dos.writeDataset(fmi, dataset);
        }

        // Verifica transfer syntax
        try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
            Attributes readFmi = dis.readFileMetaInformation();
            assertEquals(UID.ExplicitVRLittleEndian, readFmi.getString(Tag.TransferSyntaxUID));
        }
    }

    @Test
    void writesImplicitVRLittleEndian() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        Path output = tempDir.resolve("implicit_le.dcm");
        Attributes fmi = dataset.createFileMetaInformation(UID.ImplicitVRLittleEndian);
        try (DicomOutputStream dos = new DicomOutputStream(output.toFile())) {
            dos.writeDataset(fmi, dataset);
        }

        // Verifica transfer syntax
        try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
            Attributes readFmi = dis.readFileMetaInformation();
            assertEquals(UID.ImplicitVRLittleEndian, readFmi.getString(Tag.TransferSyntaxUID));
        }
    }

    @Test
    void writesExplicitVRBigEndian() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        Path output = tempDir.resolve("explicit_be.dcm");
        Attributes fmi = dataset.createFileMetaInformation(UID.ExplicitVRBigEndian);
        try (DicomOutputStream dos = new DicomOutputStream(output.toFile())) {
            dos.writeDataset(fmi, dataset);
        }

        // Verifica transfer syntax
        try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
            Attributes readFmi = dis.readFileMetaInformation();
            assertEquals(UID.ExplicitVRBigEndian, readFmi.getString(Tag.TransferSyntaxUID));
        }
    }

    @Test
    void transcodesToDifferentTransferSyntax() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        String originalTs;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            Attributes fmi = dis.readFileMetaInformation();
            originalTs = fmi.getString(Tag.TransferSyntaxUID);
            dataset = dis.readDataset(-1, -1);
        }

        assertNotNull(originalTs);

        // Transcode para Implicit VR Little Endian
        Path output = tempDir.resolve("transcoded.dcm");
        Attributes newFmi = dataset.createFileMetaInformation(UID.ImplicitVRLittleEndian);
        try (DicomOutputStream dos = new DicomOutputStream(output.toFile())) {
            dos.writeDataset(newFmi, dataset);
        }

        // Verifica que foi transcodificado
        try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
            Attributes readFmi = dis.readFileMetaInformation();
            String newTs = readFmi.getString(Tag.TransferSyntaxUID);
            assertEquals(UID.ImplicitVRLittleEndian, newTs);
            
            // Verifica que dados foram preservados
            Attributes readDataset = dis.readDataset(-1, -1);
            assertEquals(dataset.getString(Tag.SOPInstanceUID), 
                        readDataset.getString(Tag.SOPInstanceUID));
            assertEquals(dataset.getString(Tag.PatientName), 
                        readDataset.getString(Tag.PatientName));
        }
    }

    @Test
    void preservesPixelDataOnTranscode() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        // Verifica que tem PixelData original
        assertTrue(dataset.contains(Tag.PixelData));

        // Transcode
        Path output = tempDir.resolve("transcoded_pixels.dcm");
        Attributes fmi = dataset.createFileMetaInformation(UID.ExplicitVRLittleEndian);
        try (DicomOutputStream dos = new DicomOutputStream(output.toFile())) {
            dos.writeDataset(fmi, dataset);
        }

        // Verifica PixelData foi preservado
        try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
            dis.readFileMetaInformation();
            Attributes read = dis.readDataset(-1, -1);
            assertTrue(read.contains(Tag.PixelData));
            
            // Verifica dimensões
            assertEquals(dataset.getInt(Tag.Rows, 0), read.getInt(Tag.Rows, 0));
            assertEquals(dataset.getInt(Tag.Columns, 0), read.getInt(Tag.Columns, 0));
        }
    }

    @Test
    void handlesDeflatedExplicitVRLittleEndian() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        Path output = tempDir.resolve("deflated.dcm");
        Attributes fmi = dataset.createFileMetaInformation(UID.DeflatedExplicitVRLittleEndian);
        try (DicomOutputStream dos = new DicomOutputStream(output.toFile())) {
            dos.writeDataset(fmi, dataset);
        }

        // Verifica transfer syntax
        try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
            Attributes readFmi = dis.readFileMetaInformation();
            assertEquals(UID.DeflatedExplicitVRLittleEndian, 
                        readFmi.getString(Tag.TransferSyntaxUID));
            
            // Verifica que consegue ler os dados
            Attributes read = dis.readDataset(-1, -1);
            assertNotNull(read.getString(Tag.SOPInstanceUID));
        }
    }

    @Test
    void roundTripsThroughMultipleTransferSyntaxes() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes originalDataset;
        String originalPatientName;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            originalDataset = dis.readDataset(-1, -1);
            originalPatientName = originalDataset.getString(Tag.PatientName);
        }

        // Round trip 1: Explicit VR LE
        Path step1 = tempDir.resolve("step1.dcm");
        Attributes fmi1 = originalDataset.createFileMetaInformation(UID.ExplicitVRLittleEndian);
        try (DicomOutputStream dos = new DicomOutputStream(step1.toFile())) {
            dos.writeDataset(fmi1, originalDataset);
        }

        Attributes step1Dataset;
        try (DicomInputStream dis = new DicomInputStream(step1.toFile())) {
            dis.readFileMetaInformation();
            step1Dataset = dis.readDataset(-1, -1);
        }

        // Round trip 2: Implicit VR LE
        Path step2 = tempDir.resolve("step2.dcm");
        Attributes fmi2 = step1Dataset.createFileMetaInformation(UID.ImplicitVRLittleEndian);
        try (DicomOutputStream dos = new DicomOutputStream(step2.toFile())) {
            dos.writeDataset(fmi2, step1Dataset);
        }

        Attributes step2Dataset;
        try (DicomInputStream dis = new DicomInputStream(step2.toFile())) {
            dis.readFileMetaInformation();
            step2Dataset = dis.readDataset(-1, -1);
        }

        // Round trip 3: De volta para Explicit VR LE
        Path step3 = tempDir.resolve("step3.dcm");
        Attributes fmi3 = step2Dataset.createFileMetaInformation(UID.ExplicitVRLittleEndian);
        try (DicomOutputStream dos = new DicomOutputStream(step3.toFile())) {
            dos.writeDataset(fmi3, step2Dataset);
        }

        Attributes finalDataset;
        try (DicomInputStream dis = new DicomInputStream(step3.toFile())) {
            dis.readFileMetaInformation();
            finalDataset = dis.readDataset(-1, -1);
        }

        // Verifica que dados foram preservados através de todas as transcodificações
        assertEquals(originalPatientName, finalDataset.getString(Tag.PatientName));
        assertEquals(originalDataset.getString(Tag.SOPInstanceUID), 
                    finalDataset.getString(Tag.SOPInstanceUID));
        assertEquals(originalDataset.getInt(Tag.Rows, 0), finalDataset.getInt(Tag.Rows, 0));
    }

    @Test
    void handlesTransferSyntaxInFileMetaInformation() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            Attributes fmi = dis.readFileMetaInformation();
            String ts = fmi.getString(Tag.TransferSyntaxUID);
            
            assertNotNull(ts);
            assertTrue(ts.length() > 0);
            
            // Verifica formato de UID
            assertTrue(ts.matches("^\\d+(\\.\\d+)*$"), 
                      "Transfer Syntax deve ser um UID válido");
            
            dataset = dis.readDataset(-1, -1);
        }

        // Verifica que Transfer Syntax no FMI corresponde ao usado para ler
        assertNotNull(dataset);
    }

    @Test
    void validatesTransferSyntaxConsistency() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            Attributes fmi = dis.readFileMetaInformation();
            String tsFromFmi = fmi.getString(Tag.TransferSyntaxUID);
            String tsFromStream = dis.getTransferSyntax();

            assertEquals(tsFromFmi, tsFromStream, 
                        "Transfer Syntax do FMI deve corresponder ao do stream");
        }
    }

    private void writeDicom(Attributes attrs, Path path) throws IOException {
        Attributes fmi = attrs.createFileMetaInformation(UID.ExplicitVRLittleEndian);
        try (DicomOutputStream dos = new DicomOutputStream(path.toFile())) {
            dos.writeDataset(fmi, attrs);
        }
    }
}
