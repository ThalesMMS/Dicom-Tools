package com.dicomtools.cli;

import jakarta.json.Json;
import jakarta.json.JsonArray;
import jakarta.json.JsonObject;
import jakarta.json.JsonReader;
import org.dcm4che3.ws.rs.MediaTypes;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.StringReader;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Minimal DICOMweb helpers for QIDO/WADO/STOW interactions using Java HttpClient.
 */
public final class DicomWebOperations {
    private static final HttpClient CLIENT = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(2))
            .build();

    private DicomWebOperations() {
    }

    public static OperationResult stow(Path dicom, String url) throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder(URI.create(url))
                .timeout(Duration.ofSeconds(5))
                .header("Content-Type", MediaTypes.APPLICATION_DICOM)
                .POST(HttpRequest.BodyPublishers.ofFile(dicom))
                .build();
        HttpResponse<String> response = CLIENT.send(request, HttpResponse.BodyHandlers.ofString());
        Map<String, Object> meta = Map.of(
                "status", response.statusCode(),
                "body", response.body());
        if (response.statusCode() / 100 == 2) {
            return OperationResult.success("STOW-RS stored instance", meta, List.of(dicom));
        }
        return OperationResult.failure("STOW-RS failed with status " + response.statusCode(), meta);
    }

    public static OperationResult qido(String url) throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder(URI.create(url))
                .timeout(Duration.ofSeconds(5))
                .header("Accept", MediaTypes.APPLICATION_DICOM_JSON)
                .GET()
                .build();
        HttpResponse<String> response = CLIENT.send(request, HttpResponse.BodyHandlers.ofString());
        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put("status", response.statusCode());
        if (response.statusCode() / 100 != 2) {
            return OperationResult.failure("QIDO-RS failed with status " + response.statusCode(), meta);
        }
        List<Map<String, Object>> rows = parseQidoJson(response.body());
        meta.put("results", rows);
        meta.put("count", rows.size());
        return OperationResult.success("QIDO-RS returned " + rows.size() + " results", meta, List.of());
    }

    public static OperationResult wado(String url, Path output) throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder(URI.create(url))
                .timeout(Duration.ofSeconds(5))
                .header("Accept", MediaTypes.APPLICATION_DICOM)
                .GET()
                .build();
        HttpResponse<byte[]> response = CLIENT.send(request, HttpResponse.BodyHandlers.ofByteArray());
        Map<String, Object> meta = Map.of("status", response.statusCode(), "output", output.toAbsolutePath().toString());
        if (response.statusCode() / 100 != 2) {
            return OperationResult.failure("WADO-RS failed with status " + response.statusCode(), meta);
        }
        Files.createDirectories(output.toAbsolutePath().getParent());
        Files.write(output, response.body());
        return OperationResult.success("WADO-RS saved object to " + output, meta, output);
    }

    private static List<Map<String, Object>> parseQidoJson(String body) {
        List<Map<String, Object>> rows = new ArrayList<>();
        if (body == null || body.isBlank()) {
            return rows;
        }
        try (JsonReader reader = Json.createReader(new StringReader(body))) {
            var value = reader.readValue();
            if (value instanceof JsonArray array) {
                for (var element : array) {
                    if (element instanceof JsonObject obj) {
                        rows.add(jsonToFlatMap(obj));
                    }
                }
            } else if (value instanceof JsonObject obj) {
                rows.add(jsonToFlatMap(obj));
            }
        }
        return rows;
    }

    private static Map<String, Object> jsonToFlatMap(JsonObject obj) {
        Map<String, Object> map = new LinkedHashMap<>();
        for (String key : obj.keySet()) {
            map.put(key, obj.get(key).toString());
        }
        return map;
    }
}
