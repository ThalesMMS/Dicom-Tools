package com.dicomtools.dcm4che;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Tag;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.json.JSONWriter;
import org.junit.jupiter.api.Test;

import jakarta.json.Json;
import jakarta.json.JsonObject;
import jakarta.json.JsonReader;
import jakarta.json.stream.JsonGenerator;

class DicomJsonTest {

    @Test
    void exportsDatasetToDicomJson() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        try (JsonGenerator gen = Json.createGenerator(bos)) {
            JSONWriter writer = new JSONWriter(gen);
            writer.write(dataset);
        }

        byte[] jsonBytes = bos.toByteArray();
        assertTrue(jsonBytes.length > 0, "JSON output should not be empty");

        try (JsonReader reader = Json.createReader(new ByteArrayInputStream(jsonBytes))) {
            JsonObject root = reader.readObject();

            JsonObject modality = root.getJsonObject("00080060");
            assertNotNull(modality, "Modality tag should be present in JSON");
            assertEquals("CT", modality.getJsonArray("Value").getString(0));

            JsonObject patientName = root.getJsonObject("00100010");
            assertNotNull(patientName);
            JsonObject patientNameValue = patientName.getJsonArray("Value").getJsonObject(0);
            assertEquals("CEREBRIX", patientNameValue.getString("Alphabetic"));

            JsonObject rows = root.getJsonObject(org.dcm4che3.util.TagUtils.toHexString(Tag.Rows));
            JsonObject cols = root.getJsonObject(org.dcm4che3.util.TagUtils.toHexString(Tag.Columns));
            assertEquals(512, rows.getJsonArray("Value").getJsonNumber(0).intValue());
            assertEquals(512, cols.getJsonArray("Value").getJsonNumber(0).intValue());
        }
    }
}
