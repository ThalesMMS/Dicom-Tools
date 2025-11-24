package com.dicomtools.dcm4che;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

final class TestData {
    private static final Path SAMPLE = Paths.get("..", "..", "sample_series", "IM-0001-0001.dcm");
    private static final Path SAMPLE_SERIES_DIR = Paths.get("..", "..", "sample_series");

    private TestData() {
    }

    static Path sampleDicom() {
        Path absolute = SAMPLE.toAbsolutePath().normalize();
        if (!Files.exists(absolute)) {
            throw new IllegalStateException("Sample DICOM not found at " + absolute);
        }
        return absolute;
    }

    static Path sampleSeriesDir() {
        Path dir = SAMPLE_SERIES_DIR.toAbsolutePath().normalize();
        if (!Files.isDirectory(dir)) {
            throw new IllegalStateException("Sample DICOM series directory not found at " + dir);
        }
        return dir;
    }
}
