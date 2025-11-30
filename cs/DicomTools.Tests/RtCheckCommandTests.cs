using System.Text.Json;
using FellowOakDicom;

namespace DicomTools.Tests;

public class RtCheckCommandTests
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
            using var json = JsonDocument.Parse(result.Stdout);
            var root = json.RootElement;
            var metadata = root.GetProperty("metadata");
            Assert.True(root.GetProperty("ok").GetBoolean());
            Assert.Equal(planUid.UID, metadata.GetProperty("plan").GetString());
            Assert.False(metadata.GetProperty("hasDose").GetBoolean());
            Assert.False(metadata.GetProperty("hasStructureSet").GetBoolean());
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
            using var json = JsonDocument.Parse(result.Stdout);
            var metadata = json.RootElement.GetProperty("metadata");
            Assert.True(metadata.GetProperty("hasDose").GetBoolean());
            Assert.Equal(doseUid.UID, metadata.GetProperty("dose").GetString());
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
            var planUid = DicomUIDGenerator.GenerateDerivedFromUUID();
            var structUid = DicomUIDGenerator.GenerateDerivedFromUUID();

            var planDataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.RTPlanStorage },
                { DicomTag.SOPInstanceUID, planUid },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.Modality, "RTPLAN" },
                { DicomTag.PatientID, "RT-STRUCT" }
            };
            new DicomFile(planDataset).Save(planPath);

            var structDataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.RTStructureSetStorage },
                { DicomTag.SOPInstanceUID, structUid },
                { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.Modality, "RTSTRUCT" },
                { DicomTag.PatientID, "RT-STRUCT" }
            };
            new DicomFile(structDataset).Save(structPath);

            var result = CliRunner.Run("rt-check", "--plan", planPath, "--struct", structPath);
            Assert.Equal(0, result.ExitCode);
            using var json = JsonDocument.Parse(result.Stdout);
            var metadata = json.RootElement.GetProperty("metadata");
            Assert.True(metadata.GetProperty("hasStructureSet").GetBoolean());
            Assert.Equal(structUid.UID, metadata.GetProperty("structureSet").GetString());
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void RtCheck_With_All_Files()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"rt-all-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var planPath = Path.Combine(tempDir, "rtplan.dcm");
        var dosePath = Path.Combine(tempDir, "rtdose.dcm");
        var structPath = Path.Combine(tempDir, "rtstruct.dcm");

        try
        {
            var studyUid = DicomUIDGenerator.GenerateDerivedFromUUID();

            var planDataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.RTPlanStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.StudyInstanceUID, studyUid },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.Modality, "RTPLAN" },
                { DicomTag.PatientID, "RT-ALL" }
            };
            new DicomFile(planDataset).Save(planPath);

            var doseDataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.RTDoseStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.StudyInstanceUID, studyUid },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.Modality, "RTDOSE" },
                { DicomTag.PatientID, "RT-ALL" }
            };
            new DicomFile(doseDataset).Save(dosePath);

            var structDataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.RTStructureSetStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.StudyInstanceUID, studyUid },
                { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.Modality, "RTSTRUCT" },
                { DicomTag.PatientID, "RT-ALL" }
            };
            new DicomFile(structDataset).Save(structPath);

            var result = CliRunner.Run("rt-check", "--plan", planPath, "--dose", dosePath, "--struct", structPath);
            Assert.Equal(0, result.ExitCode);
            using var json = JsonDocument.Parse(result.Stdout);
            var metadata = json.RootElement.GetProperty("metadata");
            Assert.True(metadata.GetProperty("hasDose").GetBoolean());
            Assert.True(metadata.GetProperty("hasStructureSet").GetBoolean());
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
            using var json = JsonDocument.Parse(result.Stdout);
            Assert.True(json.RootElement.GetProperty("ok").GetBoolean());
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void RtCheck_Missing_Dose_File_Handled_Gracefully()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"rt-missing-{Guid.NewGuid():N}");
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
                { DicomTag.PatientID, "RT-MISSING" }
            };
            new DicomFile(planDataset).Save(planPath);

            var result = CliRunner.Run("rt-check", "--plan", planPath, "--dose", "/nonexistent/dose.dcm");
            Assert.Equal(0, result.ExitCode);
            using var json = JsonDocument.Parse(result.Stdout);
            var metadata = json.RootElement.GetProperty("metadata");
            Assert.False(metadata.GetProperty("hasDose").GetBoolean());
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }
}
