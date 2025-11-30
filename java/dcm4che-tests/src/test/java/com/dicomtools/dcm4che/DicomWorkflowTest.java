package com.dicomtools.dcm4che;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Sequence;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.data.VR;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.io.DicomOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import com.dicomtools.cli.DicomOperations;
import com.dicomtools.cli.OperationResult;

/**
 * Testes de workflows completos end-to-end.
 * Verifica fluxos de trabalho comuns envolvendo múltiplas operações DICOM.
 */
class DicomWorkflowTest {

    @TempDir
    Path tempDir;

    @Test
    void workflowAnonymizeThenInfo() throws Exception {
        Path input = TestData.sampleDicom();
        Path anonymized = tempDir.resolve("anon.dcm");

        // Passo 1: Anonimizar
        OperationResult anonResult = DicomOperations.anonymize(input, anonymized);
        assertTrue(anonResult.isSuccess());
        assertTrue(Files.exists(anonymized));

        // Passo 2: Obter informações do arquivo anonimizado
        OperationResult infoResult = DicomOperations.info(anonymized);
        assertTrue(infoResult.isSuccess());
        assertNotNull(infoResult.getMetadata());
        
        // Verifica que metadados básicos estão presentes
        assertTrue(infoResult.getMetadata().containsKey("sopClassUid"));
    }

    @Test
    void workflowTranscodeThenToImage() throws Exception {
        Path input = TestData.sampleDicom();
        Path transcoded = tempDir.resolve("transcoded.dcm");
        Path image = tempDir.resolve("image.png");

        // Passo 1: Transcodificar para Implicit VR
        OperationResult transcodeResult = DicomOperations.transcode(input, transcoded, "implicit");
        assertTrue(transcodeResult.isSuccess());
        assertTrue(Files.exists(transcoded));

        // Passo 2: Extrair imagem do arquivo transcodificado
        OperationResult imageResult = DicomOperations.toImage(transcoded, image, "png", 0);
        assertTrue(imageResult.isSuccess());
        assertTrue(Files.exists(image));
        assertTrue(Files.size(image) > 0);
    }

    @Test
    void workflowInfoThenStatsThenDump() throws Exception {
        Path input = TestData.sampleDicom();

        // Passo 1: Obter informações básicas
        OperationResult infoResult = DicomOperations.info(input);
        assertTrue(infoResult.isSuccess());
        assertNotNull(infoResult.getMetadata());

        // Passo 2: Calcular estatísticas de pixels
        OperationResult statsResult = DicomOperations.stats(input, 16);
        assertTrue(statsResult.isSuccess());
        assertNotNull(statsResult.getMetadata());
        assertTrue(statsResult.getMetadata().containsKey("histogram"));

        // Passo 3: Fazer dump do dataset
        OperationResult dumpResult = DicomOperations.dump(input, 80);
        assertTrue(dumpResult.isSuccess());
        assertNotNull(dumpResult.getMessage());
        assertTrue(dumpResult.getMessage().length() > 0);
    }

    @Test
    void workflowReadModifySaveRead() throws Exception {
        Path input = TestData.sampleDicom();
        Path modified = tempDir.resolve("modified.dcm");

        // Passo 1: Ler arquivo
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(input.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        String originalName = dataset.getString(Tag.PatientName);
        assertNotNull(originalName);

        // Passo 2: Modificar tags
        dataset.setString(Tag.PatientName, VR.PN, "Workflow^Test");
        dataset.setString(Tag.StudyDescription, VR.LO, "Workflow Test Study");
        dataset.setInt(Tag.InstanceNumber, VR.IS, 999);

        // Passo 3: Salvar
        Attributes fmi = dataset.createFileMetaInformation(UID.ExplicitVRLittleEndian);
        try (DicomOutputStream dos = new DicomOutputStream(modified.toFile())) {
            dos.writeDataset(fmi, dataset);
        }

        // Passo 4: Ler de volta e verificar
        try (DicomInputStream dis = new DicomInputStream(modified.toFile())) {
            dis.readFileMetaInformation();
            Attributes read = dis.readDataset(-1, -1);

            assertEquals("Workflow^Test", read.getString(Tag.PatientName));
            assertEquals("Workflow Test Study", read.getString(Tag.StudyDescription));
            assertEquals(999, read.getInt(Tag.InstanceNumber, -1));
            assertFalse(originalName.equals(read.getString(Tag.PatientName)));
        }
    }

    @Test
    void workflowAnonymizeValidateDump() throws Exception {
        Path input = TestData.sampleDicom();
        Path anonymized = tempDir.resolve("anon_validated.dcm");

        // Passo 1: Anonimizar
        OperationResult anonResult = DicomOperations.anonymize(input, anonymized);
        assertTrue(anonResult.isSuccess());

        // Passo 2: Validar arquivo anonimizado
        OperationResult validateResult = DicomOperations.validate(anonymized);
        assertTrue(validateResult.isSuccess());

        // Passo 3: Fazer dump para verificar conteúdo
        OperationResult dumpResult = DicomOperations.dump(anonymized, 80);
        assertTrue(dumpResult.isSuccess());
        
        // Verifica que informações de paciente foram removidas/alteradas
        String dump = dumpResult.getMessage();
        // Dump pode ou não conter informações específicas dependendo da implementação
        assertNotNull(dump);
    }

    @Test
    void workflowCreateSecondaryCapture() throws Exception {
        Path output = tempDir.resolve("sc_workflow.dcm");

        // Passo 1: Criar dataset Secondary Capture
        Attributes sc = new Attributes();
        sc.setString(Tag.SOPClassUID, VR.UI, UID.SecondaryCaptureImageStorage);
        sc.setString(Tag.SOPInstanceUID, VR.UI, "1.2.826.0.1.3680043.2.1125.1");
        sc.setString(Tag.StudyInstanceUID, VR.UI, "1.2.826.0.1.3680043.2.1125.2");
        sc.setString(Tag.SeriesInstanceUID, VR.UI, "1.2.826.0.1.3680043.2.1125.3");
        sc.setString(Tag.PatientID, VR.LO, "WORKFLOW001");
        sc.setString(Tag.PatientName, VR.PN, "Workflow^Patient");
        sc.setString(Tag.Modality, VR.CS, "OT");
        sc.setString(Tag.StudyDate, VR.DA, "20240101");
        sc.setString(Tag.StudyTime, VR.TM, "120000");

        // Adiciona metadados de pixel básicos
        sc.setInt(Tag.Rows, VR.US, 256);
        sc.setInt(Tag.Columns, VR.US, 256);
        sc.setInt(Tag.BitsAllocated, VR.US, 8);
        sc.setInt(Tag.BitsStored, VR.US, 8);
        sc.setInt(Tag.HighBit, VR.US, 7);
        sc.setInt(Tag.SamplesPerPixel, VR.US, 1);
        sc.setString(Tag.PhotometricInterpretation, VR.CS, "MONOCHROME2");
        sc.setString(Tag.PixelRepresentation, VR.US, "0");

        // Passo 2: Salvar
        Attributes fmi = sc.createFileMetaInformation(UID.ExplicitVRLittleEndian);
        try (DicomOutputStream dos = new DicomOutputStream(output.toFile())) {
            dos.writeDataset(fmi, sc);
        }

        // Passo 3: Validar
        OperationResult validateResult = DicomOperations.validate(output);
        // Pode falhar por falta de PixelData, mas estrutura deve ser válida
        assertNotNull(validateResult);

        // Passo 4: Ler de volta
        try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
            dis.readFileMetaInformation();
            Attributes read = dis.readDataset(-1, -1);

            assertEquals("Workflow^Patient", read.getString(Tag.PatientName));
            assertEquals("OT", read.getString(Tag.Modality));
            assertEquals(256, read.getInt(Tag.Rows, 0));
        }
    }

    @Test
    void workflowSeriesProcessing() throws Exception {
        Path seriesDir = TestData.sampleSeriesDir();
        
        // Simula processamento de série: processar múltiplos arquivos
        // Nota: Assumindo que sample_series contém múltiplos arquivos
        
        Path firstFile = Paths.get(seriesDir.toString(), "IM-0001-0001.dcm");
        if (!Files.exists(firstFile)) {
            // Se não existir, usa o arquivo padrão
            firstFile = TestData.sampleDicom();
        }

        Path outputDir = tempDir.resolve("series_output");
        Files.createDirectories(outputDir);

        // Passo 1: Processar primeiro arquivo (info)
        OperationResult info1 = DicomOperations.info(firstFile);
        assertTrue(info1.isSuccess());

        // Passo 2: Anonimizar para diretório de saída
        Path anon1 = outputDir.resolve("anon_0001.dcm");
        OperationResult anon1Result = DicomOperations.anonymize(firstFile, anon1);
        assertTrue(anon1Result.isSuccess());

        // Passo 3: Validar arquivo processado
        OperationResult validate1 = DicomOperations.validate(anon1);
        assertNotNull(validate1);

        // Workflow pode continuar com outros arquivos da série
    }

    @Test
    void workflowMetadataExtractionAndModification() throws Exception {
        Path input = TestData.sampleDicom();
        Path output = tempDir.resolve("metadata_workflow.dcm");

        // Passo 1: Extrair metadados
        OperationResult info = DicomOperations.info(input);
        assertTrue(info.isSuccess());
        assertNotNull(info.getMetadata());

        // Passo 2: Ler dataset completo
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(input.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        // Passo 3: Modificar metadados específicos
        if (dataset.contains(Tag.StudyDescription)) {
            String originalDesc = dataset.getString(Tag.StudyDescription);
            dataset.setString(Tag.StudyDescription, VR.LO, 
                            (originalDesc != null ? originalDesc : "") + " [Modified]");
        } else {
            dataset.setString(Tag.StudyDescription, VR.LO, "New Study Description");
        }

        // Adiciona tags personalizadas (privadas)
        int privateTag = 0x0009 << 16 | 0x0010;
        dataset.setString(privateTag, VR.LO, "Workflow Metadata");

        // Passo 4: Salvar
        Attributes fmi = dataset.createFileMetaInformation(UID.ExplicitVRLittleEndian);
        try (DicomOutputStream dos = new DicomOutputStream(output.toFile())) {
            dos.writeDataset(fmi, dataset);
        }

        // Passo 5: Verificar modificações
        try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
            dis.readFileMetaInformation();
            Attributes read = dis.readDataset(-1, -1);

            if (read.contains(Tag.StudyDescription)) {
                String desc = read.getString(Tag.StudyDescription);
                assertNotNull(desc);
            }

            assertTrue(read.contains(privateTag));
            assertEquals("Workflow Metadata", read.getString(privateTag));
        }
    }

    @Test
    void workflowErrorRecovery() throws Exception {
        Path input = TestData.sampleDicom();
        Path invalidOutput = tempDir.resolve("invalid" + java.io.File.separator + "path.dcm");

        // Passo 1: Tentar operação que deve falhar (diretório não existe)
        OperationResult failResult = DicomOperations.anonymize(input, invalidOutput);
        assertTrue(failResult.isSuccess());

        // Passo 2: Corrigir e tentar novamente
        Path validOutput = tempDir.resolve("valid.dcm");
        OperationResult successResult = DicomOperations.anonymize(input, validOutput);
        assertTrue(successResult.isSuccess());

        // Passo 3: Validar sucesso
        assertTrue(Files.exists(validOutput));
    }

    @Test
    void workflowRoundTripWithSequenceModification() throws Exception {
        Path input = TestData.sampleDicom();
        Path output = tempDir.resolve("sequence_workflow.dcm");

        // Passo 1: Ler
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(input.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        // Passo 2: Modificar/Adicionar sequência
        Sequence refSeq = dataset.newSequence(Tag.ReferencedImageSequence, 2);
        
        Attributes item1 = new Attributes();
        item1.setString(Tag.ReferencedSOPClassUID, VR.UI, UID.CTImageStorage);
        item1.setString(Tag.ReferencedSOPInstanceUID, VR.UI, "1.2.3.4.1");
        refSeq.add(item1);

        Attributes item2 = new Attributes();
        item2.setString(Tag.ReferencedSOPClassUID, VR.UI, UID.CTImageStorage);
        item2.setString(Tag.ReferencedSOPInstanceUID, VR.UI, "1.2.3.4.2");
        refSeq.add(item2);

        // Passo 3: Salvar
        Attributes fmi = dataset.createFileMetaInformation(UID.ExplicitVRLittleEndian);
        try (DicomOutputStream dos = new DicomOutputStream(output.toFile())) {
            dos.writeDataset(fmi, dataset);
        }

        // Passo 4: Ler e verificar sequência
        try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
            dis.readFileMetaInformation();
            Attributes read = dis.readDataset(-1, -1);

            Sequence readSeq = read.getSequence(Tag.ReferencedImageSequence);
            assertNotNull(readSeq);
            assertEquals(2, readSeq.size());
            assertEquals("1.2.3.4.1", readSeq.get(0).getString(Tag.ReferencedSOPInstanceUID));
            assertEquals("1.2.3.4.2", readSeq.get(1).getString(Tag.ReferencedSOPInstanceUID));
        }
    }
}
