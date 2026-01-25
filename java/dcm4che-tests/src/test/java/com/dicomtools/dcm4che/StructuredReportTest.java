package com.dicomtools.dcm4che;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Sequence;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.data.VR;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.io.DicomOutputStream;
import org.dcm4che3.util.UIDUtils;
import org.junit.jupiter.api.Test;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.time.Instant;
import java.util.Date;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

class StructuredReportTest {

    @Test
    void createsAndReadsSimpleStructuredReport() throws Exception {
        Attributes sr = buildSimpleStructuredReport();

        byte[] bytes;
        try (ByteArrayOutputStream bos = new ByteArrayOutputStream();
             DicomOutputStream dos = new DicomOutputStream(bos, UID.ExplicitVRLittleEndian)) {
            dos.writeDataset(sr.createFileMetaInformation(UID.ExplicitVRLittleEndian), sr);
            bytes = bos.toByteArray();
        }

        Attributes reread;
        try (DicomInputStream dis = new DicomInputStream(new ByteArrayInputStream(bytes))) {
            dis.readFileMetaInformation();
            reread = dis.readDataset(-1, -1);
        }

        assertEquals(UID.BasicTextSRStorage, reread.getString(Tag.SOPClassUID));
        assertEquals("SR", reread.getString(Tag.Modality));

        Sequence rootSeq = reread.getSequence(Tag.ContentSequence);
        assertNotNull(rootSeq);
        assertEquals(1, rootSeq.size(), "SR root should have one CONTAINER item");
        Attributes root = rootSeq.get(0);
        assertEquals("CONTAINER", root.getString(Tag.ValueType));
        assertEquals("SEPARATE", root.getString(Tag.ContinuityOfContent));

        Sequence title = root.getSequence(Tag.ConceptNameCodeSequence);
        assertNotNull(title);
        assertEquals("121070", title.get(0).getString(Tag.CodeValue));
        assertEquals("DCM", title.get(0).getString(Tag.CodingSchemeDesignator));

        Sequence children = root.getSequence(Tag.ContentSequence);
        assertNotNull(children);
        assertEquals(2, children.size());

        Attributes textItem = children.get(0);
        assertEquals("CONTAINS", textItem.getString(Tag.RelationshipType));
        assertEquals("TEXT", textItem.getString(Tag.ValueType));
        assertEquals("No acute findings.", textItem.getString(Tag.TextValue));
        assertEquals("121071", textItem.getSequence(Tag.ConceptNameCodeSequence).get(0).getString(Tag.CodeValue));

        Attributes codeItem = children.get(1);
        assertEquals("CONTAINS", codeItem.getString(Tag.RelationshipType));
        assertEquals("CODE", codeItem.getString(Tag.ValueType));
        Attributes conceptCode = codeItem.getSequence(Tag.ConceptCodeSequence).get(0);
        assertEquals("G-A185", conceptCode.getString(Tag.CodeValue));
        assertEquals("SRT", conceptCode.getString(Tag.CodingSchemeDesignator));
        assertEquals("Lung", conceptCode.getString(Tag.CodeMeaning));

        assertTrue(bytes.length > 0, "SR should be serializable");
    }

    private Attributes buildSimpleStructuredReport() {
        Attributes sr = new Attributes();
        sr.setString(Tag.SpecificCharacterSet, VR.CS, "ISO_IR 100");
        sr.setString(Tag.SOPClassUID, VR.UI, UID.BasicTextSRStorage);
        sr.setString(Tag.SOPInstanceUID, VR.UI, UIDUtils.createUID());
        sr.setString(Tag.StudyInstanceUID, VR.UI, UIDUtils.createUID());
        sr.setString(Tag.SeriesInstanceUID, VR.UI, UIDUtils.createUID());
        sr.setString(Tag.Modality, VR.CS, "SR");
        sr.setString(Tag.ContentLabel, VR.CS, "AUTO-SR");
        sr.setString(Tag.ContentDescription, VR.LO, "Synthetic structured report");
        sr.setString(Tag.ContentCreatorName, VR.PN, "REPORTER^TEST");
        Date now = Date.from(Instant.now());
        sr.setDate(Tag.ContentDate, VR.DA, now);
        sr.setDate(Tag.ContentTime, VR.TM, now);
        sr.setInt(Tag.InstanceNumber, VR.IS, 1);

        Attributes root = new Attributes();
        root.setString(Tag.ValueType, VR.CS, "CONTAINER");
        root.setString(Tag.ContinuityOfContent, VR.CS, "SEPARATE");
        root.newSequence(Tag.ConceptNameCodeSequence, 1).add(code("121070", "DCM", "Findings"));

        Attributes text = new Attributes();
        text.setString(Tag.RelationshipType, VR.CS, "CONTAINS");
        text.setString(Tag.ValueType, VR.CS, "TEXT");
        text.newSequence(Tag.ConceptNameCodeSequence, 1).add(code("121071", "DCM", "Finding"));
        text.setString(Tag.TextValue, VR.UT, "No acute findings.");

        Attributes code = new Attributes();
        code.setString(Tag.RelationshipType, VR.CS, "CONTAINS");
        code.setString(Tag.ValueType, VR.CS, "CODE");
        code.newSequence(Tag.ConceptNameCodeSequence, 1).add(code("121401", "DCM", "Imaged Organ"));
        code.newSequence(Tag.ConceptCodeSequence, 1).add(code("G-A185", "SRT", "Lung"));

        Sequence childSeq = root.newSequence(Tag.ContentSequence, 2);
        childSeq.add(text);
        childSeq.add(code);

        Sequence container = sr.newSequence(Tag.ContentSequence, 1);
        container.add(root);
        return sr;
    }

    private Attributes code(String value, String scheme, String meaning) {
        Attributes code = new Attributes();
        code.setString(Tag.CodeValue, VR.SH, value);
        code.setString(Tag.CodingSchemeDesignator, VR.SH, scheme);
        code.setString(Tag.CodeMeaning, VR.LO, meaning);
        return code;
    }
}
