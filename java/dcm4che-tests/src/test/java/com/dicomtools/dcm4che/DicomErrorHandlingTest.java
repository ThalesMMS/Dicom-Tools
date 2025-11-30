package com.dicomtools.dcm4che;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.NoSuchFileException;
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
 * Testes de tratamento de erros e casos extremos.
 * Verifica comportamento do sistema frente a arquivos inválidos, ausentes, corrompidos, etc.
 */
class DicomErrorHandlingTest {

    @TempDir
    Path tempDir;

    @Test
    void handlesNonExistentFile() {
        Path nonExistent = Paths.get("nonexistent_file.dcm");
        assertThrows(FileNotFoundException.class, () -> {
            try (DicomInputStream dis = new DicomInputStream(nonExistent.toFile())) {
                dis.readFileMetaInformation();
            }
        });
    }

    @Test
    void handlesEmptyFile() throws Exception {
        Path emptyFile = tempDir.resolve("empty.dcm");
        Files.createFile(emptyFile);

        assertThrows(Exception.class, () -> {
            try (DicomInputStream dis = new DicomInputStream(emptyFile.toFile())) {
                dis.readFileMetaInformation();
            }
        });
    }

    @Test
    void handlesInvalidDicomFormat() throws Exception {
        Path invalidFile = tempDir.resolve("invalid.dcm");
        Files.writeString(invalidFile, "This is not a DICOM file");

        assertThrows(Exception.class, () -> {
            try (DicomInputStream dis = new DicomInputStream(invalidFile.toFile())) {
                dis.readFileMetaInformation();
                dis.readDataset(-1, -1);
            }
        });
    }

    @Test
    void handlesCorruptedPixelData() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        // Remove PixelData mas mantém outras tags de pixel
        dataset.remove(Tag.PixelData);

        Path output = tempDir.resolve("no_pixel_data.dcm");
        writeDicom(dataset, output);

        // Tentar ler pode funcionar mas pode falhar ao tentar decodificar imagem
        assertDoesNotThrow(() -> {
            try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
                dis.readFileMetaInformation();
                dis.readDataset(-1, -1);
            }
        });
    }

    @Test
    void handlesInvalidUidFormat() throws Exception {
        Attributes attrs = new Attributes();
        attrs.setString(Tag.SOPClassUID, VR.UI, "INVALID.UID.FORMAT");
        attrs.setString(Tag.SOPInstanceUID, VR.UI, "1.2.3.4.5");
        attrs.setString(Tag.StudyInstanceUID, VR.UI, "1.2.3.4");
        attrs.setString(Tag.SeriesInstanceUID, VR.UI, "1.2.3.4.1");
        attrs.setString(Tag.PatientID, VR.LO, "TEST123");

        Path output = tempDir.resolve("invalid_uid.dcm");
        writeDicom(attrs, output);

        // UIDs inválidos podem ser escritos mas não são conformes
        assertTrue(Files.exists(output));
        try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
            dis.readFileMetaInformation();
            Attributes read = dis.readDataset(-1, -1);
            String uid = read.getString(Tag.SOPClassUID);
            assertNotNull(uid);
            assertTrue(uid.contains("INVALID"));
        }
    }

    @Test
    void handlesMissingOutputDirectory() throws Exception {
        Path output = tempDir.resolve("nonexistent/directory/output.dcm");
        Path input = TestData.sampleDicom();

        OperationResult result = DicomOperations.anonymize(input, output);
        assertTrue(result.isSuccess());
        assertTrue(Files.exists(output));
    }

    @Test
    void handlesVeryLongTagValue() throws Exception {
        Attributes attrs = new Attributes();
        attrs.setString(Tag.SOPClassUID, VR.UI, UID.CTImageStorage);
        attrs.setString(Tag.SOPInstanceUID, VR.UI, "1.2.3.4.5");
        attrs.setString(Tag.StudyInstanceUID, VR.UI, "1.2.3.4");
        attrs.setString(Tag.SeriesInstanceUID, VR.UI, "1.2.3.4.1");
        attrs.setString(Tag.PatientID, VR.LO, "TEST123");

        // Cria string muito longa
        StringBuilder longString = new StringBuilder();
        for (int i = 0; i < 10000; i++) {
            longString.append("A");
        }
        attrs.setString(Tag.StudyDescription, VR.LO, longString.toString());

        Path output = tempDir.resolve("long_tag.dcm");
        writeDicom(attrs, output);

        // Deve conseguir escrever e ler de volta
        try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
            dis.readFileMetaInformation();
            Attributes read = dis.readDataset(-1, -1);
            String desc = read.getString(Tag.StudyDescription);
            assertNotNull(desc);
            assertTrue(desc.length() > 1000);
        }
    }

    @Test
    void handlesNullValuesGracefully() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            // Tenta acessar tags que podem não existir
            String missingTag = dataset.getString(Tag.StudyDescription, null);
            // Não deve lançar exceção mesmo se tag não existe

            // Verifica tags obrigatórias não devem ser null
            String sopInstance = dataset.getString(Tag.SOPInstanceUID, null);
            assertNotNull(sopInstance, "Tag obrigatória não deve ser null");
        }
    }

    @Test
    void handlesInvalidNumericTags() throws Exception {
        Attributes attrs = new Attributes();
        attrs.setString(Tag.SOPClassUID, VR.UI, UID.CTImageStorage);
        attrs.setString(Tag.SOPInstanceUID, VR.UI, "1.2.3.4.5");
        attrs.setString(Tag.StudyInstanceUID, VR.UI, "1.2.3.4");
        attrs.setString(Tag.SeriesInstanceUID, VR.UI, "1.2.3.4.1");
        attrs.setString(Tag.PatientID, VR.LO, "TEST123");

        // Tenta definir valor inválido para tag numérica (mas como string)
        attrs.setString(Tag.InstanceNumber, VR.IS, "NOT_A_NUMBER");

        Path output = tempDir.resolve("invalid_numeric.dcm");
        writeDicom(attrs, output);

        // Pode ser escrito mas pode causar problemas ao tentar ler como número
        try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
            dis.readFileMetaInformation();
            Attributes read = dis.readDataset(-1, -1);
            // Tentar ler como int pode retornar valor padrão ou lançar exceção
            int instanceNum = read.getInt(Tag.InstanceNumber, -1);
            assertEquals(-1, instanceNum, "Valor inválido deve retornar default");
        }
    }

    @Test
    void handlesTruncatedFile() throws Exception {
        Path dicom = TestData.sampleDicom();
        byte[] fullContent = Files.readAllBytes(dicom);

        // Cria arquivo truncado (primeiros 100 bytes)
        Path truncated = tempDir.resolve("truncated.dcm");
        byte[] truncatedContent = new byte[Math.min(100, fullContent.length)];
        System.arraycopy(fullContent, 0, truncatedContent, 0, truncatedContent.length);
        Files.write(truncated, truncatedContent);

        assertThrows(Exception.class, () -> {
            try (DicomInputStream dis = new DicomInputStream(truncated.toFile())) {
                dis.readFileMetaInformation();
                dis.readDataset(-1, -1);
            }
        });
    }

    @Test
    void handlesOperationsOnInvalidPaths() throws Exception {
        Path invalidInput = Paths.get("/invalid/path.dcm");

        assertThrows(FileNotFoundException.class, () -> DicomOperations.info(invalidInput));
    }

    @Test
    void handlesMemoryConstraints() throws Exception {
        // Testa se operações lidam bem com datasets grandes
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        // Adiciona muitas sequências pequenas
        Sequence seq = dataset.newSequence(Tag.ReferencedImageSequence, 1000);
        for (int i = 0; i < 100; i++) {
            Attributes item = new Attributes();
            item.setString(Tag.ReferencedSOPInstanceUID, VR.UI, "1.2.3.4." + i);
            seq.add(item);
        }

        Path output = tempDir.resolve("large_dataset.dcm");
        writeDicom(dataset, output);

        // Deve conseguir processar sem estourar memória (dependendo do tamanho)
        assertDoesNotThrow(() -> {
            try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
                dis.readFileMetaInformation();
                dis.readDataset(-1, -1);
            }
        });
    }

    @Test
    void handlesConcurrentAccess() throws Exception {
        Path dicom = TestData.sampleDicom();

        // Tenta ler o mesmo arquivo de múltiplas threads
        Runnable reader = () -> {
            assertDoesNotThrow(() -> {
                try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
                    dis.readFileMetaInformation();
                    dis.readDataset(-1, -1);
                }
            });
        };

        Thread t1 = new Thread(reader);
        Thread t2 = new Thread(reader);
        Thread t3 = new Thread(reader);

        t1.start();
        t2.start();
        t3.start();

        t1.join();
        t2.join();
        t3.join();
    }

    private void writeDicom(Attributes attrs, Path path) throws IOException {
        Attributes fmi = attrs.createFileMetaInformation(UID.ExplicitVRLittleEndian);
        try (DicomOutputStream dos = new DicomOutputStream(path.toFile())) {
            dos.writeDataset(fmi, attrs);
        }
    }
}
