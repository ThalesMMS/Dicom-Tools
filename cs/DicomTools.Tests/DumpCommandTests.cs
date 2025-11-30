using FellowOakDicom;

namespace DicomTools.Tests;

public class DumpCommandTests
{
    [Fact]
    public void Dump_Shows_Basic_Tags()
    {
        var input = SampleSeriesHelper.GetFirstFilePath();
        var result = CliRunner.Run("dump", input);

        Assert.Equal(0, result.ExitCode);
        Assert.Contains("Patient ID", result.Stdout);
    }

    [Fact]
    public void Dump_Shows_Modality()
    {
        var input = SampleSeriesHelper.GetFirstFilePath();
        var result = CliRunner.Run("dump", input);

        Assert.Equal(0, result.ExitCode);
        Assert.Contains("Modality", result.Stdout);
    }

    [Fact]
    public void Dump_Respects_MaxValueLength()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"dump-len-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var dicomPath = Path.Combine(tempDir, "longval.dcm");

        try
        {
            var longValue = new string('X', 200);
            var dataset = new DicomDataset { AutoValidate = false };
            dataset.Add(DicomTag.SpecificCharacterSet, "ISO_IR 192");
            dataset.Add(DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage);
            dataset.Add(DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID());
            dataset.Add(DicomTag.PatientID, longValue);
            dataset.Add(DicomTag.Modality, "OT");
            new DicomFile(dataset).Save(dicomPath);

            var result = CliRunner.Run("dump", dicomPath, "--max-value-length", "20");
            Assert.Equal(0, result.ExitCode);
            Assert.DoesNotContain(longValue, result.Stdout);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void Dump_Shows_VR_Types()
    {
        var input = SampleSeriesHelper.GetFirstFilePath();
        var result = CliRunner.Run("dump", input);

        Assert.Equal(0, result.ExitCode);
        Assert.Contains("LO", result.Stdout); // PatientID is LO
        Assert.Contains("UI", result.Stdout); // UIDs are UI
    }

    [Fact]
    public void Dump_Handles_Sequence_Tags()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"dump-seq-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var dicomPath = Path.Combine(tempDir, "sequence.dcm");

        try
        {
            var seqItem = new DicomDataset
            {
                { DicomTag.PatientName, "SEQ^NESTED" }
            };
            var dataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.PatientID, "SEQ-TEST" }
            };
            dataset.Add(new DicomSequence(DicomTag.PerFrameFunctionalGroupsSequence, seqItem));
            new DicomFile(dataset).Save(dicomPath);

            var result = CliRunner.Run("dump", dicomPath);
            Assert.Equal(0, result.ExitCode);
            Assert.Contains("SQ", result.Stdout);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void Dump_Json_Output()
    {
        var input = SampleSeriesHelper.GetFirstFilePath();
        var result = CliRunner.Run("dump", input, "--json");

        Assert.Equal(0, result.ExitCode);
        Assert.Contains("Patient ID", result.Stdout);
        Assert.DoesNotContain("\"ok\"", result.Stdout);
    }
}
