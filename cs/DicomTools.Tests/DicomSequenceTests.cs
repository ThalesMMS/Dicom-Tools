using System.IO;
using FellowOakDicom;

namespace DicomTools.Tests;

public class DicomSequenceTests
{
    [Fact]
    public void DicomSequence_AddItem_CreatesNestedStructure()
    {
        var dataset = new DicomDataset();
        var sequence = new DicomSequence(DicomTag.ReferencedStudySequence);

        var item1 = new DicomDataset
        {
            { DicomTag.ReferencedSOPClassUID, DicomUID.Verification },
            { DicomTag.ReferencedSOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() }
        };

        var item2 = new DicomDataset
        {
            { DicomTag.ReferencedSOPClassUID, DicomUID.CTImageStorage },
            { DicomTag.ReferencedSOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() }
        };

        sequence.Items.Add(item1);
        sequence.Items.Add(item2);
        dataset.Add(sequence);

        Assert.True(dataset.Contains(DicomTag.ReferencedStudySequence));
        Assert.Equal(2, dataset.GetSequence(DicomTag.ReferencedStudySequence).Items.Count);
    }

    [Fact]
    public void DicomSequence_GetSequence_ReturnsItems()
    {
        var dataset = new DicomDataset();
        var sequence = new DicomSequence(DicomTag.ProcedureCodeSequence,
            new DicomDataset
            {
                { DicomTag.CodeValue, "CODE1" },
                { DicomTag.CodingSchemeDesignator, "DCM" },
                { DicomTag.CodeMeaning, "Test Procedure" }
            });

        dataset.Add(sequence);

        var retrieved = dataset.GetSequence(DicomTag.ProcedureCodeSequence);
        var firstItem = retrieved.Items.First();

        Assert.Equal("CODE1", firstItem.GetSingleValue<string>(DicomTag.CodeValue));
        Assert.Equal("DCM", firstItem.GetSingleValue<string>(DicomTag.CodingSchemeDesignator));
        Assert.Equal("Test Procedure", firstItem.GetSingleValue<string>(DicomTag.CodeMeaning));
    }

    [Fact]
    public void DicomSequence_NestedSequences_WorkCorrectly()
    {
        var innerSequence = new DicomSequence(DicomTag.ConceptNameCodeSequence,
            new DicomDataset
            {
                { DicomTag.CodeValue, "INNER" },
                { DicomTag.CodingSchemeDesignator, "99TEST" }
            });

        var middleDataset = new DicomDataset
        {
            { DicomTag.ValueType, "CODE" },
            innerSequence
        };

        var outerSequence = new DicomSequence(DicomTag.ContentSequence, middleDataset);

        var dataset = new DicomDataset();
        dataset.Add(outerSequence);

        var outer = dataset.GetSequence(DicomTag.ContentSequence).Items.First();
        Assert.Equal("CODE", outer.GetSingleValue<string>(DicomTag.ValueType));

        var inner = outer.GetSequence(DicomTag.ConceptNameCodeSequence).Items.First();
        Assert.Equal("INNER", inner.GetSingleValue<string>(DicomTag.CodeValue));
    }

    [Fact]
    public void DicomSequence_EmptySequence_IsValid()
    {
        var dataset = new DicomDataset();
        var emptySequence = new DicomSequence(DicomTag.PerformedProtocolCodeSequence);
        dataset.Add(emptySequence);

        Assert.True(dataset.Contains(DicomTag.PerformedProtocolCodeSequence));
        Assert.Empty(dataset.GetSequence(DicomTag.PerformedProtocolCodeSequence).Items);
    }

    [Fact]
    public void DicomSequence_SaveAndReload_PreservesStructure()
    {
        var dataset = new DicomDataset(DicomTransferSyntax.ExplicitVRLittleEndian)
        {
            { DicomTag.PatientName, "Sequence^Test" },
            { DicomTag.PatientID, "SEQ-001" },
            { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage }
        };

        var sequence = new DicomSequence(DicomTag.OtherPatientIDsSequence,
            new DicomDataset
            {
                { DicomTag.PatientID, "ALT-001" },
                { DicomTag.IssuerOfPatientID, "Hospital A" }
            },
            new DicomDataset
            {
                { DicomTag.PatientID, "ALT-002" },
                { DicomTag.IssuerOfPatientID, "Hospital B" }
            });

        dataset.Add(sequence);

        using var memory = new MemoryStream();
        new DicomFile(dataset).Save(memory);
        memory.Position = 0;

        var reloaded = DicomFile.Open(memory);
        var reloadedSequence = reloaded.Dataset.GetSequence(DicomTag.OtherPatientIDsSequence);

        Assert.Equal(2, reloadedSequence.Items.Count);
        Assert.Equal("ALT-001", reloadedSequence.Items[0].GetSingleValue<string>(DicomTag.PatientID));
        Assert.Equal("Hospital A", reloadedSequence.Items[0].GetSingleValue<string>(DicomTag.IssuerOfPatientID));
        Assert.Equal("ALT-002", reloadedSequence.Items[1].GetSingleValue<string>(DicomTag.PatientID));
        Assert.Equal("Hospital B", reloadedSequence.Items[1].GetSingleValue<string>(DicomTag.IssuerOfPatientID));
    }

    [Fact]
    public void DicomSequence_ModifyItem_UpdatesCorrectly()
    {
        var dataset = new DicomDataset();
        var sequence = new DicomSequence(DicomTag.RequestAttributesSequence,
            new DicomDataset
            {
                { DicomTag.RequestedProcedureID, "ORIGINAL" }
            });

        dataset.Add(sequence);

        var item = dataset.GetSequence(DicomTag.RequestAttributesSequence).Items.First();
        item.AddOrUpdate(DicomTag.RequestedProcedureID, "MODIFIED");

        var retrieved = dataset.GetSequence(DicomTag.RequestAttributesSequence).Items.First();
        Assert.Equal("MODIFIED", retrieved.GetSingleValue<string>(DicomTag.RequestedProcedureID));
    }

    [Fact]
    public void DicomSequence_RemoveItem_UpdatesCount()
    {
        var dataset = new DicomDataset();
        var sequence = new DicomSequence(DicomTag.ReferencedSeriesSequence,
            new DicomDataset { { DicomTag.SeriesInstanceUID, "1.2.3" } },
            new DicomDataset { { DicomTag.SeriesInstanceUID, "1.2.4" } },
            new DicomDataset { { DicomTag.SeriesInstanceUID, "1.2.5" } });

        dataset.Add(sequence);

        var seq = dataset.GetSequence(DicomTag.ReferencedSeriesSequence);
        Assert.Equal(3, seq.Items.Count);

        seq.Items.RemoveAt(1);
        Assert.Equal(2, seq.Items.Count);
        Assert.Equal("1.2.3", seq.Items[0].GetSingleValue<string>(DicomTag.SeriesInstanceUID));
        Assert.Equal("1.2.5", seq.Items[1].GetSingleValue<string>(DicomTag.SeriesInstanceUID));
    }

    [Fact]
    public void DicomDataset_TryGetSequence_ReturnsFalseWhenMissing()
    {
        var dataset = new DicomDataset();

        var found = dataset.TryGetSequence(DicomTag.ReferencedStudySequence, out var sequence);

        Assert.False(found);
        Assert.Null(sequence);
    }

    [Fact]
    public void DicomDataset_TryGetSequence_ReturnsTrueWhenExists()
    {
        var dataset = new DicomDataset();
        dataset.Add(new DicomSequence(DicomTag.ReferencedStudySequence,
            new DicomDataset { { DicomTag.ReferencedSOPInstanceUID, "1.2.3" } }));

        var found = dataset.TryGetSequence(DicomTag.ReferencedStudySequence, out var sequence);

        Assert.True(found);
        Assert.NotNull(sequence);
        Assert.Single(sequence.Items);
    }
}
