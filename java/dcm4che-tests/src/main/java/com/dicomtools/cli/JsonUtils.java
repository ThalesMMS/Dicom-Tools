package com.dicomtools.cli;

import jakarta.json.Json;
import jakarta.json.JsonArrayBuilder;
import jakarta.json.JsonObject;
import jakarta.json.JsonObjectBuilder;
import jakarta.json.JsonValue;

import java.nio.file.Path;
import java.util.Map;

/**
 * Lightweight JSON helpers without bringing a larger dependency.
 */
public final class JsonUtils {
    private JsonUtils() {
    }

    public static String toJsonString(Map<String, Object> map, boolean pretty) {
        JsonObject jsonObject = toJsonObject(map);
        if (!pretty) {
            return jsonObject.toString();
        }
        java.io.StringWriter writer = new java.io.StringWriter();
        Json.createWriterFactory(Map.of("jakarta.json.stream.JsonGenerator.prettyPrinting", true))
                .createWriter(writer)
                .write(jsonObject);
        return writer.toString();
    }

    public static JsonObject toJsonObject(Map<String, Object> map) {
        JsonObjectBuilder builder = Json.createObjectBuilder();
        for (Map.Entry<String, Object> entry : map.entrySet()) {
            builder.add(entry.getKey(), toJsonValue(entry.getValue()));
        }
        return builder.build();
    }

    @SuppressWarnings("unchecked")
    public static JsonValue toJsonValue(Object value) {
        if (value == null) {
            return JsonValue.NULL;
        }
        if (value instanceof JsonValue jsonValue) {
            return jsonValue;
        }
        if (value instanceof Boolean b) {
            return b ? JsonValue.TRUE : JsonValue.FALSE;
        }
        if (value instanceof Integer i) {
            return Json.createValue(i);
        }
        if (value instanceof Long l) {
            return Json.createValue(l);
        }
        if (value instanceof Double d) {
            return Json.createValue(d);
        }
        if (value instanceof Path path) {
            return Json.createValue(path.toString());
        }
        if (value instanceof Iterable<?> iterable) {
            JsonArrayBuilder arr = Json.createArrayBuilder();
            for (Object item : iterable) {
                arr.add(toJsonValue(item));
            }
            return arr.build();
        }
        if (value instanceof Map<?, ?> map) {
            JsonObjectBuilder builder = Json.createObjectBuilder();
            for (Map.Entry<?, ?> entry : ((Map<Object, Object>) map).entrySet()) {
                builder.add(String.valueOf(entry.getKey()), toJsonValue(entry.getValue()));
            }
            return builder.build();
        }
        return Json.createValue(String.valueOf(value));
    }
}
