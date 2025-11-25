using System.Text.Json;
using FellowOakDicom;
using FellowOakDicom.Imaging;

namespace DicomTools.Cli;

internal static class InfoCommand
{
    internal static int Execute(OptionParser parser, JsonSerializerOptions jsonOptions)
    {
        var input = parser.RequirePositional("input");
        var file = DicomFile.Open(input);
        var pixelData = TryGetPixelData(file.Dataset);
        var metadata = BuildInfoMetadata(file, pixelData);

        if (parser.HasFlag("json"))
        {
            Console.WriteLine(JsonSerializer.Serialize(metadata, jsonOptions));
        }
        else
        {
            PrintInfo(metadata);
        }

        return 0;
    }

    private static InfoMetadata BuildInfoMetadata(DicomFile file, DicomPixelData? pixelData)
    {
        var dataset = file.Dataset;
        return new InfoMetadata
        {
            PatientName = CliHelpers.TryGetString(dataset, DicomTag.PatientName),
            PatientId = CliHelpers.TryGetString(dataset, DicomTag.PatientID),
            StudyInstanceUid = CliHelpers.TryGetString(dataset, DicomTag.StudyInstanceUID),
            SeriesInstanceUid = CliHelpers.TryGetString(dataset, DicomTag.SeriesInstanceUID),
            SopInstanceUid = CliHelpers.TryGetString(dataset, DicomTag.SOPInstanceUID),
            Modality = CliHelpers.TryGetString(dataset, DicomTag.Modality),
            TransferSyntax = file.FileMetaInfo.TransferSyntax?.UID?.UID ?? string.Empty,
            Rows = pixelData?.Height ?? CliHelpers.TryGetUShort(dataset, DicomTag.Rows) ?? 0,
            Columns = pixelData?.Width ?? CliHelpers.TryGetUShort(dataset, DicomTag.Columns) ?? 0,
            NumberOfFrames = pixelData?.NumberOfFrames ?? CliHelpers.TryGetInt(dataset, DicomTag.NumberOfFrames) ?? 1,
            BitsAllocated = pixelData?.BitsAllocated ?? CliHelpers.TryGetUShort(dataset, DicomTag.BitsAllocated),
            PhotometricInterpretation = CliHelpers.TryGetString(dataset, DicomTag.PhotometricInterpretation)
        };
    }

    private static void PrintInfo(InfoMetadata metadata)
    {
        Console.WriteLine($"PatientName: {metadata.PatientName ?? "<unknown>"}");
        Console.WriteLine($"PatientID: {metadata.PatientId ?? "<unknown>"}");
        Console.WriteLine($"StudyInstanceUID: {metadata.StudyInstanceUid ?? "<unknown>"}");
        Console.WriteLine($"SeriesInstanceUID: {metadata.SeriesInstanceUid ?? "<unknown>"}");
        Console.WriteLine($"SOPInstanceUID: {metadata.SopInstanceUid ?? "<unknown>"}");
        Console.WriteLine($"Modality: {metadata.Modality ?? "<unknown>"}");
        Console.WriteLine($"TransferSyntax: {metadata.TransferSyntax}");
        Console.WriteLine($"Size: {metadata.Columns}x{metadata.Rows}x{metadata.NumberOfFrames}");
        Console.WriteLine($"BitsAllocated: {metadata.BitsAllocated?.ToString() ?? "<unknown>"}");
        Console.WriteLine($"PhotometricInterpretation: {metadata.PhotometricInterpretation ?? "<unknown>"}");
    }

    private static DicomPixelData? TryGetPixelData(DicomDataset dataset)
    {
        try
        {
            return DicomPixelData.Create(dataset, false);
        }
        catch
        {
            return null;
        }
    }
}
