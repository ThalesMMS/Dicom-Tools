using FellowOakDicom;
using FellowOakDicom.IO;
using FellowOakDicom.IO.Writer;

namespace DicomTools.Tests;

public class ValidateCommandTests
{
    [Fact]
    public void Validate_Succeeds_With_All_Required_Tags()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"validate-ok-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var dicomPath = Path.Combine(tempDir, "valid.dcm");

        try
        {
            var dataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.PatientID, "VALID-001" },
                { DicomTag.Modality, "OT" }
            };
            new DicomFile(dataset).Save(dicomPath);

            var result = CliRunner.Run("validate", dicomPath);
            Assert.Equal(0, result.ExitCode);
            Assert.Contains("validation ok", result.Stdout, StringComparison.OrdinalIgnoreCase);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void Validate_Fails_Missing_SOPInstanceUID()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"validate-sop-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var dicomPath = Path.Combine(tempDir, "missing-sop.dcm");

        try
        {
            var dataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.PatientID, "MISSING-SOP" }
            };
            SaveDataset(dicomPath, dataset);

            var result = CliRunner.Run("validate", dicomPath);
            Assert.NotEqual(0, result.ExitCode);
            Assert.Contains("SOPInstanceUID", result.Stderr, StringComparison.OrdinalIgnoreCase);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void Validate_Fails_Missing_StudyInstanceUID()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"validate-study-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var dicomPath = Path.Combine(tempDir, "missing-study.dcm");

        try
        {
            var dataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.PatientID, "MISSING-STUDY" }
            };
            SaveDataset(dicomPath, dataset);

            var result = CliRunner.Run("validate", dicomPath);
            Assert.NotEqual(0, result.ExitCode);
            Assert.Contains("StudyInstanceUID", result.Stderr, StringComparison.OrdinalIgnoreCase);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void Validate_Reports_All_Missing_Tags()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"validate-all-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var dicomPath = Path.Combine(tempDir, "missing-all.dcm");

        try
        {
            var dataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage },
                { DicomTag.PatientID, "MISSING-ALL" }
            };
            SaveDataset(dicomPath, dataset);

            var result = CliRunner.Run("validate", dicomPath);
            Assert.NotEqual(0, result.ExitCode);
            Assert.Contains("SOPInstanceUID", result.Stderr, StringComparison.OrdinalIgnoreCase);
            Assert.Contains("StudyInstanceUID", result.Stderr, StringComparison.OrdinalIgnoreCase);
            Assert.Contains("SeriesInstanceUID", result.Stderr, StringComparison.OrdinalIgnoreCase);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void Validate_Works_With_Sample_Series()
    {
        var input = SampleSeriesHelper.GetFirstFilePath();
        var result = CliRunner.Run("validate", input);
        Assert.Equal(0, result.ExitCode);
        Assert.Contains("validation ok", result.Stdout, StringComparison.OrdinalIgnoreCase);
    }

    private static void SaveDataset(string path, DicomDataset dataset)
    {
        var meta = new DicomFileMetaInformation
        {
            MediaStorageSOPClassUID = dataset.GetSingleValueOrDefault(DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage),
            MediaStorageSOPInstanceUID = dataset.GetSingleValueOrDefault(DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID()),
            TransferSyntax = DicomTransferSyntax.ExplicitVRLittleEndian,
            ImplementationClassUID = DicomImplementation.ClassUID,
            ImplementationVersionName = DicomImplementation.Version
        };

        using var target = new FileByteTarget(new FileReference(path));
        var writer = new DicomFileWriter(DicomWriteOptions.Default);
        writer.Write(target, meta, dataset);
    }
}
