package com.dicomtools.cli;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

public class OperationResult {
    private final boolean success;
    private final String message;
    private final Map<String, Object> metadata;
    private final List<Path> outputFiles;

    private OperationResult(boolean success, String message, Map<String, Object> metadata, List<Path> outputFiles) {
        this.success = success;
        this.message = message;
        this.metadata = metadata == null ? Collections.emptyMap() : metadata;
        this.outputFiles = outputFiles == null ? Collections.emptyList() : List.copyOf(outputFiles);
    }

    public static OperationResult success(String message) {
        return new OperationResult(true, message, Collections.emptyMap(), Collections.emptyList());
    }

    public static OperationResult success(String message, Map<String, Object> metadata, Path outputFile) {
        List<Path> outputs = outputFile != null ? List.of(outputFile) : Collections.emptyList();
        return new OperationResult(true, message, metadata, outputs);
    }

    public static OperationResult success(String message, Map<String, Object> metadata, List<Path> outputFiles) {
        return new OperationResult(true, message, metadata, outputFiles);
    }

    public static OperationResult failure(String message) {
        return new OperationResult(false, message, Collections.emptyMap(), Collections.emptyList());
    }

    public boolean isSuccess() {
        return success;
    }

    public String getMessage() {
        return message;
    }

    public Map<String, Object> getMetadata() {
        return metadata;
    }

    public List<Path> getOutputFiles() {
        return outputFiles;
    }
}
