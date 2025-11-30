package com.dicomtools.dcm4che;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.SpecificCharacterSet;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.data.VR;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.io.DicomOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/**
 * Tests dcm4che character set handling: encoding, decoding, and multi-byte support.
 */
class DicomCharsetTest {

    @TempDir
    Path tempDir;

    @Test
    void defaultCharsetIsIsoLatin1() {
        SpecificCharacterSet cs = SpecificCharacterSet.getDefaultCharacterSet();
        assertNotNull(cs);

        // Default should handle basic ASCII
        String test = "Test^Patient";
        byte[] encoded = cs.encode(test, null);
        String decoded = cs.decode(encoded, null);
        assertEquals(test, decoded);
    }

    @Test
    void handlesUtf8Encoding() {
        SpecificCharacterSet utf8 = SpecificCharacterSet.valueOf("ISO_IR 192");
        assertNotNull(utf8);

        // UTF-8 can encode any Unicode character
        String japanese = "山田^太郎";
        byte[] encoded = utf8.encode(japanese, null);
        String decoded = utf8.decode(encoded, null);
        assertEquals(japanese, decoded);

        String chinese = "张^三";
        encoded = utf8.encode(chinese, null);
        decoded = utf8.decode(encoded, null);
        assertEquals(chinese, decoded);

        String korean = "김^철수";
        encoded = utf8.encode(korean, null);
        decoded = utf8.decode(encoded, null);
        assertEquals(korean, decoded);
    }

    @Test
    void handlesMultipleCharacterSets() {
        // ISO 2022 IR 100 (Latin-1) with extension
        SpecificCharacterSet cs = SpecificCharacterSet.valueOf("ISO 2022 IR 100");
        assertNotNull(cs);

        String europeanChars = "Müller^François";
        byte[] encoded = cs.encode(europeanChars, null);
        String decoded = cs.decode(encoded, null);
        assertEquals(europeanChars, decoded);
    }

    @Test
    void writesAndReadsUtf8DicomFile() throws Exception {
        Attributes dataset = new Attributes();

        // Set UTF-8 character set
        dataset.setString(Tag.SpecificCharacterSet, VR.CS, "ISO_IR 192");

        // Set patient name with non-ASCII characters
        String patientName = "Müller^François";
        dataset.setString(Tag.PatientName, VR.PN, patientName);
        dataset.setString(Tag.PatientID, VR.LO, "UTF8TEST001");
        dataset.setString(Tag.Modality, VR.CS, "OT");
        dataset.setString(Tag.SOPClassUID, VR.UI, UID.SecondaryCaptureImageStorage);
        dataset.setString(Tag.SOPInstanceUID, VR.UI, "1.2.3.4.5.6.7.8.9");

        Attributes fmi = dataset.createFileMetaInformation(UID.ExplicitVRLittleEndian);
        Path output = tempDir.resolve("utf8_test.dcm");
        try (DicomOutputStream dos = new DicomOutputStream(output.toFile())) {
            dos.writeDataset(fmi, dataset);
        }

        // Read back and verify
        try (DicomInputStream dis = new DicomInputStream(output.toFile())) {
            dis.readFileMetaInformation();
            Attributes reread = dis.readDataset(-1, -1);

            assertEquals("ISO_IR 192", reread.getString(Tag.SpecificCharacterSet));
            assertEquals(patientName, reread.getString(Tag.PatientName));
        }
    }

    @Test
    void supportsIsoIr6DefaultRepertoire() {
        // ISO IR 6 is the default 7-bit ASCII repertoire
        SpecificCharacterSet ascii = SpecificCharacterSet.valueOf("ISO_IR 6");
        assertNotNull(ascii);

        String asciiText = "SMITH^JOHN";
        byte[] encoded = ascii.encode(asciiText, null);
        String decoded = ascii.decode(encoded, null);
        assertEquals(asciiText, decoded);
    }

    @Test
    void handlesLatin1Characters() {
        // ISO IR 100 is Latin-1 (ISO-8859-1)
        SpecificCharacterSet latin1 = SpecificCharacterSet.valueOf("ISO_IR 100");
        assertNotNull(latin1);

        String withAccents = "Hôpital^Général";
        byte[] encoded = latin1.encode(withAccents, null);
        String decoded = latin1.decode(encoded, null);
        assertEquals(withAccents, decoded);
    }

    @Test
    void parsesCharacterSetFromSampleFile() throws Exception {
        Path dicom = TestData.sampleDicom();
        Attributes dataset;
        try (DicomInputStream dis = new DicomInputStream(dicom.toFile())) {
            dis.readFileMetaInformation();
            dataset = dis.readDataset(-1, -1);
        }

        // Sample file may or may not have SpecificCharacterSet
        String cs = dataset.getString(Tag.SpecificCharacterSet);
        // If absent, default repertoire is used

        // Patient name should decode correctly regardless
        String patientName = dataset.getString(Tag.PatientName);
        assertNotNull(patientName);
    }

    @Test
    void handlesEmptyCharacterSet() {
        Attributes dataset = new Attributes();

        // Empty or absent SpecificCharacterSet means default repertoire
        String patientName = "SMITH^JOHN";
        dataset.setString(Tag.PatientName, VR.PN, patientName);

        // Should work without explicit character set
        assertEquals(patientName, dataset.getString(Tag.PatientName));
    }

    @Test
    void convertsJavaCharsetsToSpecificCharacterSet() {
        // Verify mapping between Java charsets and DICOM specific character sets
        SpecificCharacterSet utf8 = SpecificCharacterSet.valueOf("ISO_IR 192");
        assertTrue(utf8.containsASCII());

        SpecificCharacterSet latin1 = SpecificCharacterSet.valueOf("ISO_IR 100");
        assertTrue(latin1.containsASCII());
    }

    @Test
    void handlesPersonNameComponents() {
        Attributes dataset = new Attributes();
        dataset.setString(Tag.SpecificCharacterSet, VR.CS, "ISO_IR 192");

        // Person Name with all 5 components: Family^Given^Middle^Prefix^Suffix
        String fullName = "Smith^John^Michael^Dr.^Jr.";
        dataset.setString(Tag.PatientName, VR.PN, fullName);

        assertEquals(fullName, dataset.getString(Tag.PatientName));

        // Person Name can have 3 groups for different representations
        // Alphabetic=Ideographic=Phonetic separated by '='
        String multiGroup = "Smith^John=山田^太郎=やまだ^たろう";
        dataset.setString(Tag.PatientName, VR.PN, multiGroup);
        assertEquals(multiGroup, dataset.getString(Tag.PatientName));
    }

    @Test
    void handlesGreekCharacterSet() {
        // ISO IR 126 is Greek
        SpecificCharacterSet greek = SpecificCharacterSet.valueOf("ISO_IR 126");
        assertNotNull(greek);

        // Greek characters
        String greekText = "ΝΙΚΟΛΑΟΣ";
        byte[] encoded = greek.encode(greekText, null);
        String decoded = greek.decode(encoded, null);
        assertEquals(greekText, decoded);
    }

    @Test
    void handlesRussianCyrillicCharacterSet() {
        // ISO IR 144 is Cyrillic
        SpecificCharacterSet cyrillic = SpecificCharacterSet.valueOf("ISO_IR 144");
        assertNotNull(cyrillic);

        String russianText = "ИВАНОВ";
        byte[] encoded = cyrillic.encode(russianText, null);
        String decoded = cyrillic.decode(encoded, null);
        assertEquals(russianText, decoded);
    }

    @Test
    void handlesArabicCharacterSet() {
        // ISO IR 127 is Arabic
        SpecificCharacterSet arabic = SpecificCharacterSet.valueOf("ISO_IR 127");
        assertNotNull(arabic);

        String arabicText = "محمد";
        byte[] encoded = arabic.encode(arabicText, null);
        String decoded = arabic.decode(encoded, null);
        assertEquals(arabicText, decoded);
    }
}
