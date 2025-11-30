using FellowOakDicom;

namespace DicomTools.Tests;

public class StructuredReportTests
{
    [Fact]
    public void SrSummary_Returns_Json_With_Metadata()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"sr-summary-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var dicomPath = Path.Combine(tempDir, "sr.dcm");

        try
        {
            var contentItem = new DicomDataset
            {
                { DicomTag.ValueType, "TEXT" },
                { DicomTag.TextValue, "Test content" }
            };
            var contentSeq = new DicomSequence(DicomTag.ContentSequence, contentItem);

            var dataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.BasicTextSRStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.Modality, "SR" },
                { DicomTag.DocumentTitle, "Test Report" },
                { DicomTag.PatientID, "SR-001" }
            };
            dataset.Add(contentSeq);
            new DicomFile(dataset).Save(dicomPath);

            var result = CliRunner.Run("sr-summary", dicomPath);
            Assert.Equal(0, result.ExitCode);
            Assert.Contains("ok", result.Stdout);
            Assert.Contains("SR", result.Stdout);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void SrSummary_Returns_Zero_ContentItems_When_Empty()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"sr-empty-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var dicomPath = Path.Combine(tempDir, "sr-empty.dcm");

        try
        {
            var dataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.BasicTextSRStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.Modality, "SR" },
                { DicomTag.PatientID, "SR-EMPTY" }
            };
            new DicomFile(dataset).Save(dicomPath);

            var result = CliRunner.Run("sr-summary", dicomPath);
            Assert.Equal(0, result.ExitCode);
            Assert.Contains("contentItems", result.Stdout);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void SrSummary_Multiple_ContentItems()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"sr-multi-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var dicomPath = Path.Combine(tempDir, "sr-multi.dcm");

        try
        {
            var item1 = new DicomDataset { { DicomTag.ValueType, "TEXT" } };
            var item2 = new DicomDataset { { DicomTag.ValueType, "CODE" } };
            var item3 = new DicomDataset { { DicomTag.ValueType, "NUM" } };
            var contentSeq = new DicomSequence(DicomTag.ContentSequence, item1, item2, item3);

            var dataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.BasicTextSRStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.Modality, "SR" },
                { DicomTag.PatientID, "SR-MULTI" }
            };
            dataset.Add(contentSeq);
            new DicomFile(dataset).Save(dicomPath);

            var result = CliRunner.Run("sr-summary", dicomPath);
            Assert.Equal(0, result.ExitCode);
            Assert.Contains("3", result.Stdout);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }
}
