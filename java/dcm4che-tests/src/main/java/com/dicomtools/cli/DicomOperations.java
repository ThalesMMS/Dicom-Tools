package com.dicomtools.cli;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

public final class DicomOperations {
    private DicomOperations() {
    }

    public static OperationResult info(Path input) throws IOException {
        return DicomFileOperations.info(input);
    }

    public static OperationResult anonymize(Path input, Path output) throws IOException {
        return DicomFileOperations.anonymize(input, output);
    }

    public static OperationResult toImage(Path input, Path output, String format, int frame) throws IOException {
        return DicomFileOperations.toImage(input, output, format, frame);
    }

    public static OperationResult transcode(Path input, Path output, String syntax) throws IOException {
        return DicomFileOperations.transcode(input, output, syntax);
    }

    public static OperationResult validate(Path input) {
        return DicomFileOperations.validate(input);
    }

    public static OperationResult dump(Path input, int maxWidth) throws IOException {
        return DicomFileOperations.dump(input, maxWidth);
    }

    public static OperationResult stats(Path input, int bins) throws IOException {
        return DicomFileOperations.stats(input, bins);
    }

    public static OperationResult echo(String host, int port, int timeoutMs, String callingAet, String calledAet) {
        return DicomDimseOperations.echo(host, port, timeoutMs, callingAet, calledAet);
    }

    public static OperationResult structuredReport(Path input) throws IOException {
        return DicomSrRtOperations.structuredReport(input);
    }

    public static OperationResult rtConsistency(Path planPath, Path dosePath, Path structPath) throws IOException {
        return DicomSrRtOperations.rtConsistency(planPath, dosePath, structPath);
    }

    public static OperationResult store(Path input, String host, int port, int timeoutMs, String callingAet, String calledAet) {
        return DicomDimseOperations.store(input, host, port, timeoutMs, callingAet, calledAet);
    }

    public static OperationResult storeSCP(int port, String aet, Path outputDir, int durationSeconds) {
        return DicomDimseOperations.storeSCP(port, aet, outputDir, durationSeconds);
    }

    public static OperationResult cfind(String host, int port, String callingAet, String calledAet, String level, Map<Integer, String> filters, int timeoutMs) {
        return DicomQueryRetrieveOperations.cfind(host, port, callingAet, calledAet, level, filters, timeoutMs);
    }

    public static OperationResult cmove(String host, int port, String callingAet, String calledAet,
                                        String moveDestination, Map<Integer, String> filters, int timeoutMs) {
        return DicomQueryRetrieveOperations.cmove(host, port, callingAet, calledAet, moveDestination, filters, timeoutMs);
    }

    public static OperationResult cget(String host, int port, String callingAet, String calledAet,
                                       Map<Integer, String> filters, Path outputDir, int timeoutMs) {
        return DicomQueryRetrieveOperations.cget(host, port, callingAet, calledAet, filters, outputDir, timeoutMs);
    }

    public static OperationResult storageCommit(String host, int port, String callingAet, String calledAet,
                                                List<Path> instances, int timeoutMs) {
        return DicomQueryRetrieveOperations.storageCommit(host, port, callingAet, calledAet, instances, timeoutMs);
    }
}
