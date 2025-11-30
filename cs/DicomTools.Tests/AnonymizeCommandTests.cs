using FellowOakDicom;
using DicomTools.Cli;

namespace DicomTools.Tests;

public class AnonymizeCommandTests
{
    [Fact]
    public void Anonymize_Removes_Patient_Name()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"anon-name-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var inputPath = Path.Combine(tempDir, "input.dcm");
        var outputPath = Path.Combine(tempDir, "output.dcm");

        try
        {
            var dataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.PatientID, "ORIGINAL-ID-123" },
                { DicomTag.PatientName, "Doe^John" },
                { DicomTag.PatientBirthDate, "19800101" },
                { DicomTag.Modality, "OT" }
            };
            new DicomFile(dataset).Save(inputPath);

            var result = CliRunner.Run("anonymize", inputPath, "--output", outputPath);
            Assert.Equal(0, result.ExitCode);
            Assert.True(File.Exists(outputPath));

            var anonymized = DicomFile.Open(outputPath);
            var anonPatientName = anonymized.Dataset.GetSingleValueOrDefault(DicomTag.PatientName, string.Empty);
            Assert.NotEqual("Doe^John", anonPatientName);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void Anonymize_Generates_New_UIDs()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"anon-uid-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var inputPath = Path.Combine(tempDir, "input.dcm");
        var outputPath = Path.Combine(tempDir, "output.dcm");

        try
        {
            var originalSopUid = DicomUIDGenerator.GenerateDerivedFromUUID();
            var originalStudyUid = DicomUIDGenerator.GenerateDerivedFromUUID();
            var originalSeriesUid = DicomUIDGenerator.GenerateDerivedFromUUID();

            var dataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage },
                { DicomTag.SOPInstanceUID, originalSopUid },
                { DicomTag.StudyInstanceUID, originalStudyUid },
                { DicomTag.SeriesInstanceUID, originalSeriesUid },
                { DicomTag.PatientID, "TEST-UID" },
                { DicomTag.Modality, "OT" }
            };
            new DicomFile(dataset).Save(inputPath);

            var result = CliRunner.Run("anonymize", inputPath, "--output", outputPath);
            Assert.Equal(0, result.ExitCode);

            var anonymized = DicomFile.Open(outputPath);
            var anonSopUid = anonymized.Dataset.GetSingleValueOrDefault(DicomTag.SOPInstanceUID, string.Empty);
            var anonStudyUid = anonymized.Dataset.GetSingleValueOrDefault(DicomTag.StudyInstanceUID, string.Empty);
            var anonSeriesUid = anonymized.Dataset.GetSingleValueOrDefault(DicomTag.SeriesInstanceUID, string.Empty);

            Assert.NotEqual(originalSopUid.UID, anonSopUid);
            Assert.NotEqual(originalStudyUid.UID, anonStudyUid);
            Assert.NotEqual(originalSeriesUid.UID, anonSeriesUid);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void Anonymize_Uses_Default_Output_When_Not_Specified()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"anon-default-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var inputPath = Path.Combine(tempDir, "myfile.dcm");
        var expectedOutput = Path.Combine(tempDir, "myfile_anon.dcm");

        try
        {
            var dataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.PatientID, "DEFAULT-OUTPUT" },
                { DicomTag.Modality, "OT" }
            };
            new DicomFile(dataset).Save(inputPath);

            var result = CliRunner.Run("anonymize", inputPath);
            Assert.Equal(0, result.ExitCode);
            Assert.True(File.Exists(expectedOutput));
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void Anonymize_Preserves_Modality()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"anon-modality-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var inputPath = Path.Combine(tempDir, "input.dcm");
        var outputPath = Path.Combine(tempDir, "output.dcm");

        try
        {
            var dataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.CTImageStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.PatientID, "CT-PATIENT" },
                { DicomTag.Modality, "CT" }
            };
            new DicomFile(dataset).Save(inputPath);

            var result = CliRunner.Run("anonymize", inputPath, "--output", outputPath);
            Assert.Equal(0, result.ExitCode);

            var anonymized = DicomFile.Open(outputPath);
            var modality = anonymized.Dataset.GetSingleValueOrDefault(DicomTag.Modality, string.Empty);
            Assert.Equal("CT", modality);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void Anonymize_Works_With_Sample_Series()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"anon-sample-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var input = SampleSeriesHelper.GetFirstFilePath();
        var outputPath = Path.Combine(tempDir, "anonymized.dcm");

        try
        {
            var result = CliRunner.Run("anonymize", input, "--output", outputPath);
            Assert.Equal(0, result.ExitCode);
            Assert.True(File.Exists(outputPath));
            Assert.Contains("Saved anonymized file", result.Stdout);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }
}
