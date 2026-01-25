using System.IO;
using System.Text.Json;
using FellowOakDicom;

namespace DicomTools.Cli;

internal static class RtCheckCommand
{
    internal static int Execute(OptionParser parser, JsonSerializerOptions jsonOptions)
    {
        var planPath = parser.GetOption("plan") ?? parser.RequirePositional("plan");
        var dosePath = parser.GetOption("dose");
        var structPath = parser.GetOption("struct");

        var planFile = DicomFile.Open(planPath);
        var planUid = planFile.Dataset.GetSingleValueOrDefault(DicomTag.SOPInstanceUID, string.Empty);

        var doseUid = string.Empty;
        if (!string.IsNullOrWhiteSpace(dosePath) && File.Exists(dosePath))
        {
            var doseFile = DicomFile.Open(dosePath);
            doseUid = doseFile.Dataset.GetSingleValueOrDefault(DicomTag.SOPInstanceUID, string.Empty);
        }

        var structUid = string.Empty;
        if (!string.IsNullOrWhiteSpace(structPath) && File.Exists(structPath))
        {
            var structFile = DicomFile.Open(structPath);
            structUid = structFile.Dataset.GetSingleValueOrDefault(DicomTag.SOPInstanceUID, string.Empty);
        }

        var meta = new
        {
            plan = planUid,
            dose = doseUid,
            structureSet = structUid,
            hasDose = !string.IsNullOrEmpty(doseUid),
            hasStructureSet = !string.IsNullOrEmpty(structUid)
        };

        var payload = new
        {
            ok = true,
            returncode = 0,
            stdout = "RT check completed",
            stderr = string.Empty,
            output_files = Array.Empty<string>(),
            metadata = meta
        };
        Console.WriteLine(JsonSerializer.Serialize(payload, jsonOptions));
        return 0;
    }
}
