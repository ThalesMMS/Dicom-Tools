package com.dicomtools.dcm4che;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Path;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.Date;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.DatePrecision;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.VR;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.util.DateUtils;
import org.junit.jupiter.api.Test;

/**
 * Tests dcm4che date/time handling: DA, TM, DT value representations.
 */
class DicomDateTimeTest {

    @Test
    void parsesDateFromDicomFile() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        String birthDateStr = dataset.getString(Tag.PatientBirthDate);
        assertNotNull(birthDateStr, "PatientBirthDate should be present");
        assertEquals(8, birthDateStr.length(), "DA format should be YYYYMMDD");

        Date birthDate = dataset.getDate(Tag.PatientBirthDate);
        assertNotNull(birthDate);
    }

    @Test
    void formatsDateValuesCorrectly() {
        Attributes dataset = new Attributes();

        // Set date using string
        dataset.setString(Tag.StudyDate, VR.DA, "20231215");
        assertEquals("20231215", dataset.getString(Tag.StudyDate));

        // Set date using Date object
        LocalDate localDate = LocalDate.of(2023, 6, 15);
        Date javaDate = java.sql.Date.valueOf(localDate);
        dataset.setDate(Tag.PatientBirthDate, VR.DA, javaDate);

        String retrieved = dataset.getString(Tag.PatientBirthDate);
        assertTrue(retrieved.contains("2023"));
    }

    @Test
    void parsesTimeValues() {
        Attributes dataset = new Attributes();

        // Full precision: HHMMSS.FFFFFF
        dataset.setString(Tag.StudyTime, VR.TM, "143025.123456");
        String timeStr = dataset.getString(Tag.StudyTime);
        assertTrue(timeStr.startsWith("143025"), "Time should start with HHMMSS");

        // Partial precision
        dataset.setString(Tag.SeriesTime, VR.TM, "1430");
        assertEquals("1430", dataset.getString(Tag.SeriesTime));
    }

    @Test
    void handlesDateTimeVr() {
        Attributes dataset = new Attributes();

        // DateTime format: YYYYMMDDHHMMSS.FFFFFF&ZZXX
        String dt = "20231215143025.000000";
        dataset.setString(Tag.AcquisitionDateTime, VR.DT, dt);

        String retrieved = dataset.getString(Tag.AcquisitionDateTime);
        assertNotNull(retrieved);
        assertTrue(retrieved.startsWith("20231215"));
    }

    @Test
    void convertsDateUtilsFormats() {
        // DateUtils provides static helpers for format conversion
        Date now = new Date();

        String daStr = DateUtils.formatDA(null, now);
        assertNotNull(daStr);
        assertEquals(8, daStr.length(), "DA format is YYYYMMDD");

        String tmStr = DateUtils.formatTM(null, now);
        assertNotNull(tmStr);
        assertTrue(tmStr.length() >= 6, "TM format is at least HHMMSS");

        String dtStr = DateUtils.formatDT(null, now);
        assertNotNull(dtStr);
        assertTrue(dtStr.length() >= 14, "DT format is at least YYYYMMDDHHMMSS");
    }

    @Test
    void parsesDateRange() {
        Attributes dataset = new Attributes();

        // Date range format: startDate-endDate
        dataset.setString(Tag.StudyDate, VR.DA, "20230101-20231231");

        String dateRange = dataset.getString(Tag.StudyDate);
        assertTrue(dateRange.contains("-"), "Date range should contain hyphen");

        // Parse range components
        String[] parts = dateRange.split("-");
        assertEquals(2, parts.length);
        assertEquals("20230101", parts[0]);
        assertEquals("20231231", parts[1]);
    }

    @Test
    void handlesTimezoneOffset() {
        Attributes dataset = new Attributes();

        // Timezone offset format in DT: +HHMM or -HHMM
        String dtWithTz = "20231215143025.000000-0500";
        dataset.setString(Tag.AcquisitionDateTime, VR.DT, dtWithTz);

        String retrieved = dataset.getString(Tag.AcquisitionDateTime);
        assertNotNull(retrieved);
        assertTrue(retrieved.contains("-0500") || retrieved.contains("2023"), 
                "Should preserve timezone or date info");
    }

    @Test
    void setsAndRetrievesDatePrecision() {
        Attributes dataset = new Attributes();

        // Full date
        dataset.setString(Tag.StudyDate, VR.DA, "20231215");
        Date fullDate = dataset.getDate(Tag.StudyDate);
        assertNotNull(fullDate);

        // Retrieve with precision indicator
        DatePrecision precision = new DatePrecision();
        Date dateWithPrecision = dataset.getDate(Tag.StudyDate, precision);
        assertNotNull(dateWithPrecision);
    }

    @Test
    void handlesAgeStringVr() {
        Attributes dataset = new Attributes();

        // Age String format: nnnD, nnnW, nnnM, nnnY
        dataset.setString(Tag.PatientAge, VR.AS, "045Y");
        assertEquals("045Y", dataset.getString(Tag.PatientAge));

        dataset.setString(Tag.PatientAge, VR.AS, "006M");
        assertEquals("006M", dataset.getString(Tag.PatientAge));

        dataset.setString(Tag.PatientAge, VR.AS, "012W");
        assertEquals("012W", dataset.getString(Tag.PatientAge));

        dataset.setString(Tag.PatientAge, VR.AS, "003D");
        assertEquals("003D", dataset.getString(Tag.PatientAge));
    }

    @Test
    void combinesDateAndTimeIntoDateTime() {
        Attributes dataset = new Attributes();

        dataset.setString(Tag.StudyDate, VR.DA, "20231215");
        dataset.setString(Tag.StudyTime, VR.TM, "143025");

        Date studyDate = dataset.getDate(Tag.StudyDate);
        Date studyTime = dataset.getDate(Tag.StudyTime);

        assertNotNull(studyDate);
        assertNotNull(studyTime);

        // Combined date/time can be retrieved as a combined value
        String combinedStr = dataset.getString(Tag.StudyDate) + dataset.getString(Tag.StudyTime);
        assertNotNull(combinedStr);
        assertEquals(14, combinedStr.length(), "Combined YYYYMMDDHHMMSS should be 14 chars");
    }

    @Test
    void readsDateFromSampleFile() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        // Study/Series date/time from real file
        String studyDate = dataset.getString(Tag.StudyDate);
        String seriesDate = dataset.getString(Tag.SeriesDate);
        String studyTime = dataset.getString(Tag.StudyTime);
        String seriesTime = dataset.getString(Tag.SeriesTime);

        // At least one should be present in a typical DICOM
        boolean hasDateInfo = studyDate != null || seriesDate != null;
        assertTrue(hasDateInfo || dataset.contains(Tag.ContentDate), 
                "Sample DICOM should have some date information");
    }
}
