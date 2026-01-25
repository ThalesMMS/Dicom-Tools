using FellowOakDicom;

namespace DicomTools.Tests;

public class InfoCommandTests
{
    [Fact]
    public void Info_Shows_Patient_Info()
    {
        var input = SampleSeriesHelper.GetFirstFilePath();
        var result = CliRunner.Run("info", input);

        Assert.Equal(0, result.ExitCode);
        Assert.NotEmpty(result.Stdout);
    }

    [Fact]
    public void Info_Shows_Study_Info()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"info-study-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var dicomPath = Path.Combine(tempDir, "study.dcm");

        try
        {
            var dataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.PatientID, "INFO-001" },
                { DicomTag.PatientName, "Info^Test" },
                { DicomTag.StudyDescription, "Test Study Description" },
                { DicomTag.Modality, "OT" }
            };
            new DicomFile(dataset).Save(dicomPath);

            var result = CliRunner.Run("info", dicomPath);
            Assert.Equal(0, result.ExitCode);
            Assert.Contains("INFO-001", result.Stdout);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void Info_Json_Output()
    {
        var input = SampleSeriesHelper.GetFirstFilePath();
        var result = CliRunner.Run("info", input, "--json");

        Assert.Equal(0, result.ExitCode);
        Assert.Contains("{", result.Stdout);
        Assert.Contains("}", result.Stdout);
    }

    [Fact]
    public void Info_Shows_Modality()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"info-mod-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var dicomPath = Path.Combine(tempDir, "modality.dcm");

        try
        {
            var dataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.CTImageStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.PatientID, "MOD-CT" },
                { DicomTag.Modality, "CT" }
            };
            new DicomFile(dataset).Save(dicomPath);

            var result = CliRunner.Run("info", dicomPath);
            Assert.Equal(0, result.ExitCode);
            Assert.Contains("CT", result.Stdout);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void Info_Handles_MR_Modality()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"info-mr-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var dicomPath = Path.Combine(tempDir, "mr.dcm");

        try
        {
            var dataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.MRImageStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.PatientID, "MOD-MR" },
                { DicomTag.Modality, "MR" }
            };
            new DicomFile(dataset).Save(dicomPath);

            var result = CliRunner.Run("info", dicomPath);
            Assert.Equal(0, result.ExitCode);
            Assert.Contains("MR", result.Stdout);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }
}
