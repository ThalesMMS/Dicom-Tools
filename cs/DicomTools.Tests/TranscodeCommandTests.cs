using FellowOakDicom;

namespace DicomTools.Tests;

public class TranscodeCommandTests
{
    [Fact]
    public void Transcode_To_ExplicitVR_LittleEndian()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"tx-evr-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var input = SampleSeriesHelper.GetFirstFilePath();
        var output = Path.Combine(tempDir, "explicit.dcm");

        try
        {
            var result = CliRunner.Run("transcode", input, "--output", output, "--transfer-syntax", "explicit");
            if (result.ExitCode != 0)
            {
                Assert.Contains("not supported", result.Stderr + result.Stdout, StringComparison.OrdinalIgnoreCase);
                return;
            }

            var transcoded = DicomFile.Open(output);
            Assert.Equal("1.2.840.10008.1.2.1", transcoded.FileMetaInfo.TransferSyntax.UID.UID);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void Transcode_To_ImplicitVR_LittleEndian()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"tx-ivr-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var input = SampleSeriesHelper.GetFirstFilePath();
        var output = Path.Combine(tempDir, "implicit.dcm");

        try
        {
            var result = CliRunner.Run("transcode", input, "--output", output, "--transfer-syntax", "implicit");
            if (result.ExitCode != 0)
            {
                Assert.Contains("not supported", result.Stderr + result.Stdout, StringComparison.OrdinalIgnoreCase);
                return;
            }

            var transcoded = DicomFile.Open(output);
            Assert.Equal("1.2.840.10008.1.2", transcoded.FileMetaInfo.TransferSyntax.UID.UID);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void Transcode_Uses_Default_Output_Filename()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"tx-default-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var inputPath = Path.Combine(tempDir, "source.dcm");
        var expectedOutput = Path.Combine(tempDir, "source_transcoded.dcm");

        try
        {
            var dataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.PatientID, "TX-DEFAULT" },
                { DicomTag.Modality, "OT" }
            };
            new DicomFile(dataset).Save(inputPath);

            var result = CliRunner.Run("transcode", inputPath);
            Assert.Equal(0, result.ExitCode);
            Assert.True(File.Exists(expectedOutput));
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void Transcode_Preserves_Patient_Data()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"tx-preserve-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var inputPath = Path.Combine(tempDir, "patient.dcm");
        var outputPath = Path.Combine(tempDir, "patient_tx.dcm");

        try
        {
            var dataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.PatientID, "PRESERVE-123" },
                { DicomTag.PatientName, "Test^Patient" },
                { DicomTag.Modality, "CT" }
            };
            new DicomFile(dataset).Save(inputPath);

            var result = CliRunner.Run("transcode", inputPath, "--output", outputPath);
            Assert.Equal(0, result.ExitCode);

            var transcoded = DicomFile.Open(outputPath);
            Assert.Equal("PRESERVE-123", transcoded.Dataset.GetSingleValueOrDefault(DicomTag.PatientID, ""));
            Assert.Equal("Test^Patient", transcoded.Dataset.GetSingleValueOrDefault(DicomTag.PatientName, ""));
            Assert.Equal("CT", transcoded.Dataset.GetSingleValueOrDefault(DicomTag.Modality, ""));
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }
}
