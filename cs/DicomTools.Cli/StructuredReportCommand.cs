using System.Text.Json;
using FellowOakDicom;

namespace DicomTools.Cli;

internal static class StructuredReportCommand
{
    internal static int Execute(OptionParser parser, JsonSerializerOptions jsonOptions)
    {
        var input = parser.RequirePositional("input");
        var file = DicomFile.Open(input);
        var ds = file.Dataset;
        var contentSeq = ds.GetSequence(DicomTag.ContentSequence);

        var meta = new
        {
            modality = ds.GetSingleValueOrDefault(DicomTag.Modality, string.Empty),
            title = ds.GetSingleValueOrDefault(DicomTag.DocumentTitle, string.Empty),
            contentItems = contentSeq?.Items.Count ?? 0,
            sopInstanceUid = ds.GetSingleValueOrDefault(DicomTag.SOPInstanceUID, string.Empty)
        };

        var payload = new
        {
            ok = true,
            returncode = 0,
            stdout = $"SR summary for {input}",
            stderr = string.Empty,
            output_files = Array.Empty<string>(),
            metadata = meta
        };
        Console.WriteLine(JsonSerializer.Serialize(payload, jsonOptions));
        return 0;
    }
}
