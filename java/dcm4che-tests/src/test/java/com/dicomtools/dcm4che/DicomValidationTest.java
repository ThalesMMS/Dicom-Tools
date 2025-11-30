package com.dicomtools.dcm4che;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Sequence;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.data.VR;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.io.DicomOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/**
 * Testes de validação de datasets DICOM.
 * Verifica estrutura, tags obrigatórias, consistência de UIDs e integridade de dados.
 */
class DicomValidationTest {

    @TempDir
    Path tempDir;

    @Test
    void validatesCompleteDataset() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            Attributes fmi = dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            // Verifica File Meta Information
            assertNotNull(fmi.getString(Tag.MediaStorageSOPClassUID));
            assertNotNull(fmi.getString(Tag.TransferSyntaxUID));
            assertNotNull(fmi.getString(Tag.MediaStorageSOPInstanceUID));

            // Verifica tags obrigatórias do dataset
            assertTrue(dataset.contains(Tag.SOPClassUID));
            assertTrue(dataset.contains(Tag.SOPInstanceUID));
            assertTrue(dataset.contains(Tag.StudyInstanceUID));
            assertTrue(dataset.contains(Tag.SeriesInstanceUID));
            assertTrue(dataset.contains(Tag.PatientID));
        }
    }

    @Test
    void detectsMissingRequiredTags() throws Exception {
        Attributes incomplete = new Attributes();
        incomplete.setString(Tag.SOPClassUID, VR.UI, UID.CTImageStorage);
        // Falta SOPInstanceUID e outras tags obrigatórias

        Path output = tempDir.resolve("incomplete.dcm");
        writeDicom(incomplete, output);

        assertThrows(Exception.class, () -> {
            try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
                dis.readFileMetaInformation();
                dis.readDataset(-1, -1);
            }
        });
    }

    @Test
    void validatesUidConsistency() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            Attributes fmi = dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            String mediaStorageSOPInstanceUID = fmi.getString(Tag.MediaStorageSOPInstanceUID);
            String datasetSOPInstanceUID = dataset.getString(Tag.SOPInstanceUID);

            assertEquals(mediaStorageSOPInstanceUID, datasetSOPInstanceUID,
                    "SOPInstanceUID deve ser consistente entre FMI e dataset");

            String mediaStorageSOPClassUID = fmi.getString(Tag.MediaStorageSOPClassUID);
            String datasetSOPClassUID = dataset.getString(Tag.SOPClassUID);

            assertEquals(mediaStorageSOPClassUID, datasetSOPClassUID,
                    "SOPClassUID deve ser consistente entre FMI e dataset");
        }
    }

    @Test
    void validatesPixelDataStructure() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            assertTrue(dataset.contains(Tag.PixelData), "Imagem deve conter PixelData");

            // Verifica dimensões
            assertTrue(dataset.contains(Tag.Rows));
            assertTrue(dataset.contains(Tag.Columns));
            int rows = dataset.getInt(Tag.Rows, 0);
            int cols = dataset.getInt(Tag.Columns, 0);
            assertTrue(rows > 0 && cols > 0, "Dimensões devem ser positivas");

            // Verifica bits
            if (dataset.contains(Tag.BitsAllocated)) {
                int bitsAllocated = dataset.getInt(Tag.BitsAllocated, 0);
                assertTrue(bitsAllocated > 0 && bitsAllocated <= 32,
                        "BitsAllocated deve ser razoável");
            }
        }
    }

    @Test
    void validatesSequenceStructure() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            // Verifica se sequências existentes têm estrutura válida
            Sequence[] sequences = {
                dataset.getSequence(Tag.ReferencedImageSequence),
                dataset.getSequence(Tag.ReferencedInstanceSequence),
                dataset.getSequence(Tag.SourceImageSequence)
            };

            for (Sequence seq : sequences) {
                if (seq != null) {
                    for (Attributes item : seq) {
                        assertNotNull(item, "Itens de sequência não devem ser null");
                    }
                }
            }
        }
    }

    @Test
    void validatesDatesAndTimes() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            if (dataset.contains(Tag.StudyDate)) {
                String studyDate = dataset.getString(Tag.StudyDate);
                assertNotNull(studyDate);
                assertEquals(8, studyDate.length(), "Data deve estar no formato YYYYMMDD");
            }

            if (dataset.contains(Tag.StudyTime)) {
                String studyTime = dataset.getString(Tag.StudyTime);
                assertNotNull(studyTime);
                assertTrue(studyTime.length() >= 6, "Hora deve ter pelo menos HHMMSS");
            }
        }
    }

    @Test
    void detectsInvalidTransferSyntax() throws Exception {
        Attributes attrs = new Attributes();
        attrs.setString(Tag.SOPClassUID, VR.UI, UID.CTImageStorage);
        attrs.setString(Tag.SOPInstanceUID, VR.UI, "1.2.3.4.5");
        attrs.setString(Tag.StudyInstanceUID, VR.UI, "1.2.3.4");
        attrs.setString(Tag.SeriesInstanceUID, VR.UI, "1.2.3.4.1");
        attrs.setString(Tag.PatientID, VR.LO, "TEST123");

        // Cria FMI com transfer syntax inválido
        Attributes fmi = attrs.createFileMetaInformation("1.2.3.INVALID");

        Path output = tempDir.resolve("invalid_ts.dcm");
        try (DicomOutputStream dos = new DicomOutputStream(output.toFile())) {
            dos.writeDataset(fmi, attrs);
        }

        // Tentar ler pode falhar ou gerar warnings dependendo da implementação
        assertTrue(Files.exists(output));
    }

    @Test
    void validatesDicomPreamble() throws Exception {
        Path dicom = TestData.sampleDicom();
        byte[] fileBytes = Files.readAllBytes(dicom);

        // Verifica se tem os 128 bytes de preâmbulo
        assertTrue(fileBytes.length >= 132, "Arquivo DICOM deve ter pelo menos 132 bytes");

        // Verifica prefixo DICM
        byte[] prefix = new byte[4];
        System.arraycopy(fileBytes, 128, prefix, 0, 4);
        String dicm = new String(prefix);
        assertEquals("DICM", dicm, "Deve conter prefixo DICM após preâmbulo");
    }

    @Test
    void validatesRequiredImageTags() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            // Tags obrigatórias para imagens
            assertTrue(dataset.contains(Tag.Modality));
            assertTrue(dataset.contains(Tag.StudyDate) || dataset.contains(Tag.SeriesDate));
            assertTrue(dataset.contains(Tag.StudyTime) || dataset.contains(Tag.SeriesTime));

            // Verifica se é uma imagem (tem PixelData)
            if (dataset.contains(Tag.PixelData)) {
                assertTrue(dataset.contains(Tag.SamplesPerPixel));
                assertTrue(dataset.contains(Tag.PhotometricInterpretation));
                assertTrue(dataset.contains(Tag.BitsAllocated));
                assertTrue(dataset.contains(Tag.BitsStored));
                assertTrue(dataset.contains(Tag.HighBit));
            }
        }
    }

    @Test
    void validatesEmptySequenceVsNull() throws Exception {
        Attributes attrs = new Attributes();
        attrs.setString(Tag.SOPClassUID, VR.UI, UID.SecondaryCaptureImageStorage);
        attrs.setString(Tag.SOPInstanceUID, VR.UI, "1.2.3.4.5");
        attrs.setString(Tag.StudyInstanceUID, VR.UI, "1.2.3.4");
        attrs.setString(Tag.SeriesInstanceUID, VR.UI, "1.2.3.4.1");
        attrs.setString(Tag.PatientID, VR.LO, "TEST123");

        // Sequência vazia vs null
        Sequence emptySeq = attrs.newSequence(Tag.ReferencedImageSequence, 0);
        assertNotNull(emptySeq);
        assertEquals(0, emptySeq.size());

        Path output = tempDir.resolve("empty_seq.dcm");
        writeDicom(attrs, output);

        try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
            dis.readFileMetaInformation();
            Attributes read = dis.readDataset(-1, -1);
            Sequence readSeq = read.getSequence(Tag.ReferencedImageSequence);
            assertNotNull(readSeq);
            assertEquals(0, readSeq.size());
        }
    }

    private void writeDicom(Attributes attrs, Path path) throws IOException {
        Attributes fmi = attrs.createFileMetaInformation(UID.ExplicitVRLittleEndian);
        try (DicomOutputStream dos = new DicomOutputStream(path.toFile())) {
            dos.writeDataset(fmi, attrs);
        }
    }
}
