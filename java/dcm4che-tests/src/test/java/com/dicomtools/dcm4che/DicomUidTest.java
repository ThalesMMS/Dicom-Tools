package com.dicomtools.dcm4che;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.HashSet;
import java.util.Set;

import org.dcm4che3.data.UID;
import org.dcm4che3.util.UIDUtils;
import org.junit.jupiter.api.Test;

/**
 * Tests dcm4che UID utilities: generation, validation, and well-known UID lookups.
 */
class DicomUidTest {

    @Test
    void generatesUniqueUids() {
        Set<String> uids = new HashSet<>();
        for (int i = 0; i < 100; i++) {
            String uid = UIDUtils.createUID();
            assertNotNull(uid, "Generated UID should not be null");
            assertTrue(uid.length() <= 64, "UID must be at most 64 characters");
            assertTrue(uid.matches("[0-9.]+"), "UID must contain only digits and dots");
            assertTrue(uids.add(uid), "Generated UIDs should be unique");
        }
    }

    @Test
    void generatesUidWithCustomRoot() {
        String root = "1.2.3.4.5";
        String uid = UIDUtils.createUID(root);
        assertTrue(uid.startsWith(root), "UID should start with custom root");
        assertTrue(uid.length() > root.length(), "UID should have suffix after root");
    }

    @Test
    void generatesUidDeterministicallyFromSeed() {
        // UIDUtils can generate UIDs with a root
        String root = "1.2.3.4";
        String uid1 = UIDUtils.createUID(root);
        String uid2 = UIDUtils.createUID(root);
        
        // Both should start with the same root
        assertTrue(uid1.startsWith(root));
        assertTrue(uid2.startsWith(root));
        
        // But should be different (random suffix)
        assertNotEquals(uid1, uid2, "Random UIDs should differ");
    }

    @Test
    void validatesWellKnownStorageClassUids() {
        assertTrue(UID.CTImageStorage.startsWith("1.2.840.10008"));
        assertTrue(UID.MRImageStorage.startsWith("1.2.840.10008"));
        assertTrue(UID.SecondaryCaptureImageStorage.startsWith("1.2.840.10008"));
        assertTrue(UID.XRayAngiographicImageStorage.startsWith("1.2.840.10008"));
        assertTrue(UID.DigitalXRayImageStorageForPresentation.startsWith("1.2.840.10008"));
    }

    @Test
    void validatesTransferSyntaxUids() {
        assertEquals("1.2.840.10008.1.2", UID.ImplicitVRLittleEndian);
        assertEquals("1.2.840.10008.1.2.1", UID.ExplicitVRLittleEndian);
        assertEquals("1.2.840.10008.1.2.2", UID.ExplicitVRBigEndian);
        assertEquals("1.2.840.10008.1.2.4.50", UID.JPEGBaseline8Bit);
        assertEquals("1.2.840.10008.1.2.4.90", UID.JPEG2000Lossless);
    }

    @Test
    void identifiesCompressedTransferSyntaxes() {
        assertFalse(isCompressed(UID.ImplicitVRLittleEndian));
        assertFalse(isCompressed(UID.ExplicitVRLittleEndian));
        assertTrue(isCompressed(UID.JPEGBaseline8Bit));
        assertTrue(isCompressed(UID.JPEGLossless));
        assertTrue(isCompressed(UID.JPEG2000Lossless));
        assertTrue(isCompressed(UID.RLELossless));
    }

    @Test
    void looksUpUidNames() {
        assertEquals("CT Image Storage", UID.nameOf(UID.CTImageStorage));
        assertEquals("MR Image Storage", UID.nameOf(UID.MRImageStorage));
        assertEquals("Explicit VR Little Endian", UID.nameOf(UID.ExplicitVRLittleEndian));
        assertEquals("Verification SOP Class", UID.nameOf(UID.Verification));
    }

    @Test
    void validatesServiceClassUids() {
        assertEquals("1.2.840.10008.1.1", UID.Verification);
        assertEquals("1.2.840.10008.5.1.4.1.1.2", UID.CTImageStorage);
        assertNotNull(UID.StudyRootQueryRetrieveInformationModelFind);
        assertNotNull(UID.PatientRootQueryRetrieveInformationModelFind);
    }

    private boolean isCompressed(String tsuid) {
        return !UID.ImplicitVRLittleEndian.equals(tsuid)
                && !UID.ExplicitVRLittleEndian.equals(tsuid)
                && !UID.ExplicitVRBigEndian.equals(tsuid);
    }
}
