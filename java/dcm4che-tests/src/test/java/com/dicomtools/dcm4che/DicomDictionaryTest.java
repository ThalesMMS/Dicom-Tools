package com.dicomtools.dcm4che;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.dcm4che3.data.ElementDictionary;
import org.dcm4che3.data.Keyword;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.VR;
import org.dcm4che3.util.TagUtils;
import org.junit.jupiter.api.Test;

/**
 * Tests dcm4che data dictionary: tag lookups, VR resolution, and keyword mapping.
 */
class DicomDictionaryTest {

    @Test
    void looksUpStandardTagConstants() {
        assertEquals(0x00100010, Tag.PatientName);
        assertEquals(0x00100020, Tag.PatientID);
        assertEquals(0x00080060, Tag.Modality);
        assertEquals(0x7FE00010, Tag.PixelData);
        assertEquals(0x00080018, Tag.SOPInstanceUID);
        assertEquals(0x0020000D, Tag.StudyInstanceUID);
        assertEquals(0x0020000E, Tag.SeriesInstanceUID);
    }

    @Test
    void resolvesKeywordsFromTags() {
        assertEquals("PatientName", Keyword.valueOf(Tag.PatientName));
        assertEquals("PatientID", Keyword.valueOf(Tag.PatientID));
        assertEquals("Modality", Keyword.valueOf(Tag.Modality));
        assertEquals("PixelData", Keyword.valueOf(Tag.PixelData));
        assertEquals("Rows", Keyword.valueOf(Tag.Rows));
        assertEquals("Columns", Keyword.valueOf(Tag.Columns));
    }

    @Test
    void resolvesTagsFromKeywords() {
        // Use ElementDictionary to look up tags by keyword
        ElementDictionary dict = ElementDictionary.getStandardElementDictionary();
        assertEquals(Tag.PatientName, dict.tagForKeyword("PatientName"));
        assertEquals(Tag.PatientID, dict.tagForKeyword("PatientID"));
        assertEquals(Tag.Modality, dict.tagForKeyword("Modality"));
        assertEquals(Tag.PixelData, dict.tagForKeyword("PixelData"));
    }

    @Test
    void retrievesVrFromDictionary() {
        ElementDictionary dict = ElementDictionary.getStandardElementDictionary();

        assertEquals(VR.PN, dict.vrOf(Tag.PatientName));
        assertEquals(VR.LO, dict.vrOf(Tag.PatientID));
        assertEquals(VR.CS, dict.vrOf(Tag.Modality));
        assertEquals(VR.US, dict.vrOf(Tag.Rows));
        assertEquals(VR.US, dict.vrOf(Tag.Columns));
        assertEquals(VR.DA, dict.vrOf(Tag.PatientBirthDate));
        assertEquals(VR.TM, dict.vrOf(Tag.StudyTime));
        assertEquals(VR.UI, dict.vrOf(Tag.SOPInstanceUID));
    }

    @Test
    void formatsTagsAsHexStrings() {
        assertEquals("00100010", TagUtils.toHexString(Tag.PatientName));
        assertEquals("00100020", TagUtils.toHexString(Tag.PatientID));
        assertEquals("7FE00010", TagUtils.toHexString(Tag.PixelData));
        assertEquals("00080060", TagUtils.toHexString(Tag.Modality));
    }

    @Test
    void parsesTagsFromHexStrings() {
        assertEquals(Tag.PatientName, TagUtils.intFromHexString("00100010"));
        assertEquals(Tag.PatientID, TagUtils.intFromHexString("00100020"));
        assertEquals(Tag.PixelData, TagUtils.intFromHexString("7FE00010"));
    }

    @Test
    void identifiesGroupAndElement() {
        assertEquals(0x0010, TagUtils.groupNumber(Tag.PatientName));
        assertEquals(0x0010, TagUtils.elementNumber(Tag.PatientName));

        assertEquals(0x0008, TagUtils.groupNumber(Tag.Modality));
        assertEquals(0x0060, TagUtils.elementNumber(Tag.Modality));

        assertEquals(0x7FE0, TagUtils.groupNumber(Tag.PixelData));
        assertEquals(0x0010, TagUtils.elementNumber(Tag.PixelData));
    }

    @Test
    void retrievesPrivateCreatorTags() {
        // Private tags follow pattern: (gggg,0010-00FF) for creator, (gggg,1000-10FF) for data
        int privateCreatorTag = 0x00110010;
        int privateDataTag = 0x00111001;

        assertTrue(TagUtils.isPrivateCreator(privateCreatorTag));
        assertTrue(TagUtils.isPrivateTag(privateDataTag));
        assertEquals(0x0011, TagUtils.groupNumber(privateDataTag));
    }

    @Test
    void recognizesSequenceTags() {
        ElementDictionary dict = ElementDictionary.getStandardElementDictionary();

        assertEquals(VR.SQ, dict.vrOf(Tag.ReferencedStudySequence));
        assertEquals(VR.SQ, dict.vrOf(Tag.ReferencedSeriesSequence));
        assertEquals(VR.SQ, dict.vrOf(Tag.OtherPatientIDsSequence));
        assertEquals(VR.SQ, dict.vrOf(Tag.ProcedureCodeSequence));
    }

    @Test
    void looksUpKeywordByTag() {
        String keyword = ElementDictionary.keywordOf(Tag.PatientName, null);
        assertEquals("PatientName", keyword);

        String modalityKeyword = ElementDictionary.keywordOf(Tag.Modality, null);
        assertEquals("Modality", modalityKeyword);
    }

    @Test
    void vrEnumProvidesUsefulMetadata() {
        assertEquals(2, VR.US.numEndianBytes());
        assertEquals(4, VR.UL.numEndianBytes());
        assertEquals(8, VR.FD.numEndianBytes());
        assertEquals(4, VR.FL.numEndianBytes());
        assertEquals(2, VR.SS.numEndianBytes());
        assertEquals(4, VR.SL.numEndianBytes());

        assertTrue(VR.PN.isStringType());
        assertTrue(VR.LO.isStringType());
        assertTrue(VR.CS.isStringType());
        assertTrue(VR.DA.isStringType());
    }
}
