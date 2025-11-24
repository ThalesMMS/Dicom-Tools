package com.dicomtools.dcm4che;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.DoubleSummaryStatistics;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Tag;
import org.dcm4che3.io.DicomInputStream;
import org.junit.jupiter.api.Test;

class DicomSeriesTest {

    @Test
    void seriesIsConsistentAcrossAllFiles() throws Exception {
        List<Path> dicoms = seriesFiles();
        Attributes first = readDataset(dicoms.get(0));

        String studyUid = first.getString(Tag.StudyInstanceUID);
        String seriesUid = first.getString(Tag.SeriesInstanceUID);
        double[] spacing = first.getDoubles(Tag.PixelSpacing);
        int rows = first.getInt(Tag.Rows, 0);
        int cols = first.getInt(Tag.Columns, 0);

        List<Integer> instanceNumbers = new ArrayList<>();
        for (Path file : dicoms) {
            Attributes ds = readDataset(file);
            assertEquals(studyUid, ds.getString(Tag.StudyInstanceUID), "StudyInstanceUID mismatch in " + file.getFileName());
            assertEquals(seriesUid, ds.getString(Tag.SeriesInstanceUID), "SeriesInstanceUID mismatch in " + file.getFileName());
            assertTrue(ds.contains(Tag.PixelData), "Pixel data missing in " + file.getFileName());
            assertEquals(rows, ds.getInt(Tag.Rows, 0));
            assertEquals(cols, ds.getInt(Tag.Columns, 0));
            assertEquals(spacing[0], ds.getDouble(Tag.PixelSpacing, 0), 1e-6);
            assertEquals(spacing[1], ds.getDoubles(Tag.PixelSpacing)[1], 1e-6);
            instanceNumbers.add(ds.getInt(Tag.InstanceNumber, -1));
        }

        List<Integer> sortedInstances = instanceNumbers.stream().sorted().collect(Collectors.toList());
        assertEquals(instanceNumbers.size(), Set.copyOf(instanceNumbers).size(), "InstanceNumbers should be unique");
        assertEquals(sortedInstances, instanceNumbers, "Files should be ordered by InstanceNumber");
        assertEquals(1, sortedInstances.get(0), "Instance numbers should start at 1");
        assertEquals(instanceNumbers.size(), sortedInstances.get(sortedInstances.size() - 1), "Instance numbers should be contiguous");
    }

    @Test
    void slicePositionsAreMonotonic() throws Exception {
        List<Path> dicoms = seriesFiles();
        List<Slice> slices = new ArrayList<>();
        for (Path file : dicoms) {
            Attributes ds = readDataset(file);
            double[] ipp = ds.getDoubles(Tag.ImagePositionPatient);
            double posZ = ipp != null && ipp.length >= 3 ? ipp[2] : Double.NaN;
            int inst = ds.getInt(Tag.InstanceNumber, -1);
            slices.add(new Slice(inst, posZ));
        }

        slices.sort(Comparator.comparingInt(s -> s.instance));
        List<Double> positions = slices.stream().map(s -> s.z).collect(Collectors.toList());

        DoubleSummaryStatistics stats = positions.stream().mapToDouble(Double::doubleValue).summaryStatistics();
        assertFalse(Double.isNaN(stats.getMin()), "ImagePositionPatient should be present for all slices");

        double direction = Math.signum(positions.get(positions.size() - 1) - positions.get(0));
        double tolerance = 1e-3;
        for (int i = 1; i < positions.size(); i++) {
            double delta = positions.get(i) - positions.get(i - 1);
            assertTrue(Math.abs(delta) > tolerance, "Slice spacing too small at index " + i);
            assertTrue(Math.signum(delta) == direction, "Slice order changed direction at index " + i);
        }
    }

    private static List<Path> seriesFiles() throws IOException {
        Path dir = TestData.sampleSeriesDir();
        try (var stream = Files.list(dir)) {
            List<Path> files = stream
                    .filter(p -> p.getFileName().toString().toLowerCase().endsWith(".dcm"))
                    .sorted()
                    .collect(Collectors.toList());
            if (files.isEmpty()) {
                throw new IllegalStateException("No DICOM files found in " + dir);
            }
            return files;
        }
    }

    private static Attributes readDataset(Path file) throws IOException {
        try (DicomInputStream dis = new DicomInputStream(file.toFile())) {
            dis.readFileMetaInformation();
            return dis.readDataset(-1, -1);
        }
    }

    private record Slice(int instance, double z) {}
}
