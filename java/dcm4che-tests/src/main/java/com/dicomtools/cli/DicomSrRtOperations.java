package com.dicomtools.cli;

import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Sequence;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

final class DicomSrRtOperations {
    private DicomSrRtOperations() {
    }

    static OperationResult structuredReport(Path input) throws IOException {
        DicomIOUtils.DicomData data = DicomIOUtils.readDicom(input);
        Attributes attrs = data.dataset();
        List<Map<String, Object>> entries = new ArrayList<>();

        Sequence content = attrs.getSequence(Tag.ContentSequence);
        if (content != null) {
            for (Attributes item : content) {
                collectSrNodes(item, 0, entries);
            }
        }

        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put("sopClassUid", attrs.getString(Tag.SOPClassUID, ""));
        meta.put("sopClassName", UID.nameOf(attrs.getString(Tag.SOPClassUID, "")));
        meta.put("entryCount", entries.size());
        meta.put("entries", entries);

        String message = entries.isEmpty()
                ? "Structured Report parsed but ContentSequence is empty"
                : "Structured Report parsed with " + entries.size() + " content items";
        return OperationResult.success(message, meta, java.util.Collections.emptyList());
    }

    static OperationResult rtConsistency(Path planPath, Path dosePath, Path structPath) throws IOException {
        Attributes plan = planPath != null ? DicomIOUtils.readDicom(planPath).dataset() : null;
        Attributes dose = dosePath != null ? DicomIOUtils.readDicom(dosePath).dataset() : null;
        Attributes struct = structPath != null ? DicomIOUtils.readDicom(structPath).dataset() : null;

        String planUid = plan != null ? plan.getString(Tag.SOPInstanceUID, "") : "";
        String planStudy = plan != null ? plan.getString(Tag.StudyInstanceUID, "") : "";
        String planFor = plan != null ? plan.getString(Tag.FrameOfReferenceUID, "") : "";

        List<String> issues = new ArrayList<>();
        Map<String, Object> meta = new LinkedHashMap<>();

        if (plan != null) meta.put("plan", summarizeRt(planPath, plan));
        if (dose != null) meta.put("dose", summarizeRt(dosePath, dose));
        if (struct != null) meta.put("struct", summarizeRt(structPath, struct));

        if (plan != null && dose != null) {
            if (!referencesPlan(dose, planUid)) {
                issues.add("RTDOSE does not reference supplied RTPLAN " + planUid);
            }
            String doseStudy = dose.getString(Tag.StudyInstanceUID, "");
            if (!planStudy.isBlank() && !doseStudy.isBlank() && !planStudy.equals(doseStudy)) {
                issues.add("StudyInstanceUID mismatch between RTPLAN and RTDOSE");
            }
        }

        if (plan != null && struct != null) {
            String structStudy = struct.getString(Tag.StudyInstanceUID, "");
            if (!planStudy.isBlank() && !structStudy.isBlank() && !planStudy.equals(structStudy)) {
                issues.add("StudyInstanceUID mismatch between RTPLAN and RTSTRUCT");
            }
            String structFor = struct.getString(Tag.FrameOfReferenceUID, "");
            if (!planFor.isBlank() && !structFor.isBlank() && !planFor.equals(structFor)) {
                issues.add("FrameOfReferenceUID mismatch between RTPLAN and RTSTRUCT");
            }
            Sequence refPlanSeq = struct.getSequence(Tag.ReferencedRTPlanSequence);
            if (refPlanSeq != null && !refPlanSeq.isEmpty() && !referencesPlan(struct, planUid)) {
                issues.add("RTSTRUCT references a different RTPLAN than supplied");
            }
        }

        if (!issues.isEmpty()) {
            meta.put("issues", issues);
            return OperationResult.failure("RT consistency check failed: " + String.join("; ", issues), meta);
        }

        meta.put("issues", java.util.Collections.emptyList());
        return OperationResult.success("RT references are consistent", meta, java.util.Collections.emptyList());
    }

    private static void collectSrNodes(Attributes item, int level, List<Map<String, Object>> entries) {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("level", level);
        row.put("relationship", item.getString(Tag.RelationshipType, ""));
        row.put("valueType", item.getString(Tag.ValueType, ""));
        row.put("conceptName", codeDisplay(item.getSequence(Tag.ConceptNameCodeSequence)));
        row.put("codeMeaning", codeMeaning(item.getSequence(Tag.ConceptNameCodeSequence)));
        row.put("codeValue", codeValue(item.getSequence(Tag.ConceptNameCodeSequence)));
        row.put("textValue", item.getString(Tag.TextValue, ""));
        row.put("numericValue", item.getString(Tag.NumericValue, ""));
        entries.add(row);

        Sequence nested = item.getSequence(Tag.ContentSequence);
        if (nested != null) {
            for (Attributes child : nested) {
                collectSrNodes(child, level + 1, entries);
            }
        }
    }

    private static Map<String, Object> summarizeRt(Path path, Attributes attrs) {
        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("path", path != null ? path.toAbsolutePath().toString() : "");
        summary.put("sopClassUid", attrs.getString(Tag.SOPClassUID, ""));
        summary.put("sopClassName", UID.nameOf(attrs.getString(Tag.SOPClassUID, "")));
        summary.put("sopInstanceUid", attrs.getString(Tag.SOPInstanceUID, ""));
        summary.put("studyInstanceUid", attrs.getString(Tag.StudyInstanceUID, ""));
        summary.put("seriesInstanceUid", attrs.getString(Tag.SeriesInstanceUID, ""));
        summary.put("frameOfReferenceUid", attrs.getString(Tag.FrameOfReferenceUID, ""));
        summary.put("referencedPlanUids", findReferencedPlanUids(attrs));
        return summary;
    }

    private static List<String> findReferencedPlanUids(Attributes attrs) {
        Sequence seq = attrs.getSequence(Tag.ReferencedRTPlanSequence);
        if (seq == null || seq.isEmpty()) {
            return java.util.Collections.emptyList();
        }
        return seq.stream()
                .map(a -> a.getString(Tag.ReferencedSOPInstanceUID, ""))
                .filter(s -> s != null && !s.isBlank())
                .collect(Collectors.toList());
    }

    private static boolean referencesPlan(Attributes attrs, String planUid) {
        if (planUid == null || planUid.isBlank()) return false;
        return findReferencedPlanUids(attrs).stream().anyMatch(planUid::equals);
    }

    private static String codeMeaning(Sequence seq) {
        if (seq == null || seq.isEmpty()) return "";
        return seq.get(0).getString(Tag.CodeMeaning, "");
    }

    private static String codeValue(Sequence seq) {
        if (seq == null || seq.isEmpty()) return "";
        return seq.get(0).getString(Tag.CodeValue, "");
    }

    private static String codeDisplay(Sequence seq) {
        if (seq == null || seq.isEmpty()) return "";
        Attributes code = seq.get(0);
        String meaning = code.getString(Tag.CodeMeaning, "");
        String value = code.getString(Tag.CodeValue, "");
        String scheme = code.getString(Tag.CodingSchemeDesignator, "");
        if (!meaning.isBlank() && !value.isBlank() && !scheme.isBlank()) {
            return meaning + " [" + scheme + ":" + value + "]";
        }
        if (!meaning.isBlank() && !value.isBlank()) {
            return meaning + " [" + value + "]";
        }
        return meaning.isBlank() ? value : meaning;
    }
}
