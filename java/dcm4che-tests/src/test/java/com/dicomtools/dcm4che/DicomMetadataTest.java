package com.dicomtools.dcm4che;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Path;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Sequence;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.VR;
import org.dcm4che3.io.DicomInputStream;
import org.junit.jupiter.api.Test;

/**
 * Testes profundos de extração e manipulação de metadados DICOM.
 * Verifica leitura, interpretação e transformação de diferentes tipos de metadados.
 */
class DicomMetadataTest {

    @Test
    void extractsPatientMetadata() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            // Metadados do paciente
            assertNotNull(dataset.getString(Tag.PatientName));
            assertNotNull(dataset.getString(Tag.PatientID));
            
            if (dataset.contains(Tag.PatientBirthDate)) {
                String birthDate = dataset.getString(Tag.PatientBirthDate);
                assertNotNull(birthDate);
            }
            
            if (dataset.contains(Tag.PatientSex)) {
                String sex = dataset.getString(Tag.PatientSex);
                assertNotNull(sex);
            }
        }
    }

    @Test
    void extractsStudyMetadata() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            // Metadados do estudo
            assertNotNull(dataset.getString(Tag.StudyInstanceUID));
            
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
            
            if (dataset.contains(Tag.StudyDescription)) {
                String desc = dataset.getString(Tag.StudyDescription);
                assertNotNull(desc);
            }
        }
    }

    @Test
    void extractsSeriesMetadata() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            // Metadados da série
            assertNotNull(dataset.getString(Tag.SeriesInstanceUID));
            
            if (dataset.contains(Tag.SeriesNumber)) {
                int seriesNum = dataset.getInt(Tag.SeriesNumber, -1);
                assertTrue(seriesNum >= 0 || seriesNum == -1, 
                          "SeriesNumber deve ser não-negativo ou ausente");
            }
            
            if (dataset.contains(Tag.Modality)) {
                String modality = dataset.getString(Tag.Modality);
                assertNotNull(modality);
                assertFalse(modality.isEmpty());
            }
            
            if (dataset.contains(Tag.SeriesDescription)) {
                String desc = dataset.getString(Tag.SeriesDescription);
                assertNotNull(desc);
            }
        }
    }

    @Test
    void extractsImageMetadata() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            // Metadados da imagem
            if (dataset.contains(Tag.InstanceNumber)) {
                int instanceNum = dataset.getInt(Tag.InstanceNumber, -1);
                assertTrue(instanceNum >= 0 || instanceNum == -1);
            }

            if (dataset.contains(Tag.SliceLocation)) {
                double sliceLoc = dataset.getDouble(Tag.SliceLocation, Double.NaN);
                assertFalse(Double.isNaN(sliceLoc), 
                           "Se presente, SliceLocation deve ser um número válido");
            }

            if (dataset.contains(Tag.ImagePositionPatient)) {
                double[] pos = dataset.getDoubles(Tag.ImagePositionPatient);
                assertNotNull(pos);
                assertEquals(3, pos.length, "ImagePositionPatient deve ter 3 valores");
            }

            if (dataset.contains(Tag.ImageOrientationPatient)) {
                double[] orient = dataset.getDoubles(Tag.ImageOrientationPatient);
                assertNotNull(orient);
                assertEquals(6, orient.length, "ImageOrientationPatient deve ter 6 valores");
            }
        }
    }

    @Test
    void extractsPixelMetadata() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            if (dataset.contains(Tag.PixelData)) {
                // Dimensões
                assertTrue(dataset.contains(Tag.Rows));
                assertTrue(dataset.contains(Tag.Columns));
                int rows = dataset.getInt(Tag.Rows, 0);
                int cols = dataset.getInt(Tag.Columns, 0);
                assertTrue(rows > 0 && cols > 0);

                // Bits
                if (dataset.contains(Tag.BitsAllocated)) {
                    int bitsAllocated = dataset.getInt(Tag.BitsAllocated, 0);
                    assertTrue(bitsAllocated > 0 && bitsAllocated <= 32);
                }

                if (dataset.contains(Tag.BitsStored)) {
                    int bitsStored = dataset.getInt(Tag.BitsStored, 0);
                    assertTrue(bitsStored > 0);
                }

                if (dataset.contains(Tag.HighBit)) {
                    int highBit = dataset.getInt(Tag.HighBit, -1);
                    assertTrue(highBit >= 0);
                }

                // Espaçamento
                if (dataset.contains(Tag.PixelSpacing)) {
                    double[] spacing = dataset.getDoubles(Tag.PixelSpacing);
                    assertNotNull(spacing);
                    assertEquals(2, spacing.length);
                    assertTrue(spacing[0] > 0 && spacing[1] > 0);
                }

                // Window/Level
                if (dataset.contains(Tag.WindowCenter)) {
                    double[] center = dataset.getDoubles(Tag.WindowCenter);
                    assertNotNull(center);
                    assertTrue(center.length > 0);
                }

                if (dataset.contains(Tag.WindowWidth)) {
                    double[] width = dataset.getDoubles(Tag.WindowWidth);
                    assertNotNull(width);
                    assertTrue(width.length > 0);
                }
            }
        }
    }

    @Test
    void extractsSOPClassMetadata() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            Attributes fmi = dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            // SOP Class
            String sopClassUID = dataset.getString(Tag.SOPClassUID);
            assertNotNull(sopClassUID);
            assertFalse(sopClassUID.isEmpty());

            String mediaStorageSOPClassUID = fmi.getString(Tag.MediaStorageSOPClassUID);
            assertEquals(sopClassUID, mediaStorageSOPClassUID,
                        "SOPClassUID deve ser consistente entre FMI e dataset");

            // SOP Instance
            String sopInstanceUID = dataset.getString(Tag.SOPInstanceUID);
            assertNotNull(sopInstanceUID);
            assertFalse(sopInstanceUID.isEmpty());

            String mediaStorageSOPInstanceUID = fmi.getString(Tag.MediaStorageSOPInstanceUID);
            assertEquals(sopInstanceUID, mediaStorageSOPInstanceUID,
                        "SOPInstanceUID deve ser consistente entre FMI e dataset");
        }
    }

    @Test
    void extractsReferencedMetadata() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            // Verifica sequências de referência
            Sequence refImageSeq = dataset.getSequence(Tag.ReferencedImageSequence);
            if (refImageSeq != null) {
                for (Attributes item : refImageSeq) {
                    if (item.contains(Tag.ReferencedSOPClassUID)) {
                        String refSOPClass = item.getString(Tag.ReferencedSOPClassUID);
                        assertNotNull(refSOPClass);
                    }
                    if (item.contains(Tag.ReferencedSOPInstanceUID)) {
                        String refSOPInstance = item.getString(Tag.ReferencedSOPInstanceUID);
                        assertNotNull(refSOPInstance);
                    }
                }
            }

            Sequence refInstanceSeq = dataset.getSequence(Tag.ReferencedInstanceSequence);
            if (refInstanceSeq != null) {
                for (Attributes item : refInstanceSeq) {
                    if (item.contains(Tag.ReferencedSOPClassUID)) {
                        assertNotNull(item.getString(Tag.ReferencedSOPClassUID));
                    }
                    if (item.contains(Tag.ReferencedSOPInstanceUID)) {
                        assertNotNull(item.getString(Tag.ReferencedSOPInstanceUID));
                    }
                }
            }
        }
    }

    @Test
    void extractsAcquisitionMetadata() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            // Metadados de aquisição
            if (dataset.contains(Tag.AcquisitionDate)) {
                String acqDate = dataset.getString(Tag.AcquisitionDate);
                assertNotNull(acqDate);
            }

            if (dataset.contains(Tag.AcquisitionTime)) {
                String acqTime = dataset.getString(Tag.AcquisitionTime);
                assertNotNull(acqTime);
            }

            if (dataset.contains(Tag.AcquisitionNumber)) {
                int acqNum = dataset.getInt(Tag.AcquisitionNumber, -1);
                assertTrue(acqNum >= 0 || acqNum == -1);
            }

            if (dataset.contains(Tag.KVP)) {
                double kvp = dataset.getDouble(Tag.KVP, Double.NaN);
                assertFalse(Double.isNaN(kvp));
            }

            if (dataset.contains(Tag.ExposureTime)) {
                int exposure = dataset.getInt(Tag.ExposureTime, -1);
                assertTrue(exposure >= 0 || exposure == -1);
            }
        }
    }

    @Test
    void extractsEquipmentMetadata() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            // Metadados do equipamento
            if (dataset.contains(Tag.Manufacturer)) {
                String manufacturer = dataset.getString(Tag.Manufacturer);
                assertNotNull(manufacturer);
            }

            if (dataset.contains(Tag.ManufacturerModelName)) {
                String model = dataset.getString(Tag.ManufacturerModelName);
                assertNotNull(model);
            }

            if (dataset.contains(Tag.DeviceSerialNumber)) {
                String serial = dataset.getString(Tag.DeviceSerialNumber);
                assertNotNull(serial);
            }

            if (dataset.contains(Tag.SoftwareVersions)) {
                String software = dataset.getString(Tag.SoftwareVersions);
                assertNotNull(software);
            }
        }
    }

    @Test
    void extractsAllAvailableMetadata() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            // Conta número total de tags
            int tagCount = dataset.size();
            assertTrue(tagCount > 0, "Dataset deve conter pelo menos algumas tags");

            // Verifica que tags obrigatórias estão presentes
            assertTrue(dataset.contains(Tag.SOPClassUID));
            assertTrue(dataset.contains(Tag.SOPInstanceUID));
            assertTrue(dataset.contains(Tag.StudyInstanceUID));
            assertTrue(dataset.contains(Tag.SeriesInstanceUID));

            // Itera sobre todas as tags
            int iteratedCount = 0;
            for (int tag : dataset.tags()) {
                iteratedCount++;
                assertTrue(tag > 0, "Tag deve ser um número positivo");
                
                // Verifica que consegue ler o valor (sem importar o tipo)
                Object value = dataset.getValue(tag);
                // Valor pode ser null para alguns casos, mas tag existe
            }

            assertEquals(tagCount, iteratedCount, 
                        "Número de tags iteradas deve corresponder ao tamanho do dataset");
        }
    }

    @Test
    void handlesMissingOptionalMetadata() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            // Tags opcionais podem não existir
            String missingTag = dataset.getString(Tag.PatientAge, null);
            // Não deve lançar exceção se tag não existe

            int missingInt = dataset.getInt(Tag.SliceThickness, -1);
            // Retorna valor padrão se tag não existe

            double[] missingArray = dataset.getDoubles(Tag.PatientWeight);
            // Pode ser null se tag não existe
        }
    }

    @Test
    void extractsSequenceMetadata() throws Exception {
        Path dicom = TestData.sampleDicom();
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            Attributes dataset = dis.readDataset(-1, -1);

            // Itera sobre sequências presentes
            int[] sequenceTags = {
                Tag.ReferencedImageSequence,
                Tag.ReferencedInstanceSequence,
                Tag.SourceImageSequence,
                Tag.ReferencedStudySequence,
                Tag.ReferencedSeriesSequence
            };

            for (int seqTag : sequenceTags) {
                Sequence seq = dataset.getSequence(seqTag);
                if (seq != null) {
                    assertTrue(seq.size() >= 0, 
                              "Tamanho da sequência deve ser não-negativo");
                    
                    for (Attributes item : seq) {
                        assertNotNull(item, "Itens de sequência não devem ser null");
                        assertTrue(item.size() >= 0, 
                                  "Itens devem ter pelo menos 0 tags");
                    }
                }
            }
        }
    }
}
