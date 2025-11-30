using FellowOakDicom;

namespace DicomTools.Tests;

public class RtCheckTests
{
    [Fact]
    public void RtCheck_Returns_Json_With_Plan_Info()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"rt-check-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var planPath = Path.Combine(tempDir, "rtplan.dcm");

        try
        {
            var planUid = DicomUIDGenerator.GenerateDerivedFromUUID();
            var planDataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.RTPlanStorage },
                { DicomTag.SOPInstanceUID, planUid },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.Modality, "RTPLAN" },
                { DicomTag.PatientID, "RT-001" }
            };
            new DicomFile(planDataset).Save(planPath);

            var result = CliRunner.Run("rt-check", "--plan", planPath);
            Assert.Equal(0, result.ExitCode);
            Assert.Contains("ok", result.Stdout);
            Assert.Contains(planUid.UID, result.Stdout);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void RtCheck_With_Dose_File()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"rt-dose-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var planPath = Path.Combine(tempDir, "rtplan.dcm");
        var dosePath = Path.Combine(tempDir, "rtdose.dcm");

        try
        {
            var planUid = DicomUIDGenerator.GenerateDerivedFromUUID();
            var doseUid = DicomUIDGenerator.GenerateDerivedFromUUID();

            var planDataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.RTPlanStorage },
                { DicomTag.SOPInstanceUID, planUid },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.Modality, "RTPLAN" },
                { DicomTag.PatientID, "RT-DOSE" }
            };
            new DicomFile(planDataset).Save(planPath);

            var doseDataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.RTDoseStorage },
                { DicomTag.SOPInstanceUID, doseUid },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.Modality, "RTDOSE" },
                { DicomTag.PatientID, "RT-DOSE" }
            };
            new DicomFile(doseDataset).Save(dosePath);

            var result = CliRunner.Run("rt-check", "--plan", planPath, "--dose", dosePath);
            Assert.Equal(0, result.ExitCode);
            Assert.Contains("hasDose", result.Stdout);
            Assert.Contains("true", result.Stdout);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void RtCheck_With_Structure_Set()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"rt-struct-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var planPath = Path.Combine(tempDir, "rtplan.dcm");
        var structPath = Path.Combine(tempDir, "rtstruct.dcm");

        try
        {
            var planDataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.RTPlanStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.Modality, "RTPLAN" },
                { DicomTag.PatientID, "RT-STRUCT" }
            };
            new DicomFile(planDataset).Save(planPath);

            var structDataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.RTStructureSetStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.Modality, "RTSTRUCT" },
                { DicomTag.PatientID, "RT-STRUCT" }
            };
            new DicomFile(structDataset).Save(structPath);

            var result = CliRunner.Run("rt-check", "--plan", planPath, "--struct", structPath);
            Assert.Equal(0, result.ExitCode);
            Assert.Contains("hasStructureSet", result.Stdout);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void RtCheck_Uses_Positional_Plan_Argument()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"rt-pos-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var planPath = Path.Combine(tempDir, "rtplan.dcm");

        try
        {
            var planDataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.RTPlanStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.Modality, "RTPLAN" },
                { DicomTag.PatientID, "RT-POS" }
            };
            new DicomFile(planDataset).Save(planPath);

            var result = CliRunner.Run("rt-check", planPath);
            Assert.Equal(0, result.ExitCode);
            Assert.Contains("ok", result.Stdout);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }
}
