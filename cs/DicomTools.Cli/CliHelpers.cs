using FellowOakDicom;

namespace DicomTools.Cli;

internal static class CliHelpers
{
    internal static void EnsureParentDirectory(string path)
    {
        var directory = Path.GetDirectoryName(path);
        if (!string.IsNullOrWhiteSpace(directory))
        {
            Directory.CreateDirectory(directory);
        }
    }

    internal static string BuildDefaultOutput(string input, string suffix)
    {
        var directory = Path.GetDirectoryName(input) ?? ".";
        var filename = Path.GetFileNameWithoutExtension(input);
        return Path.Combine(directory, $"{filename}{suffix}");
    }

    internal static string? TryGetString(DicomDataset dataset, DicomTag tag) =>
        dataset.TryGetString(tag, out var value) ? value : null;

    internal static ushort? TryGetUShort(DicomDataset dataset, DicomTag tag) =>
        dataset.TryGetSingleValue(tag, out ushort value) ? value : null;

    internal static int? TryGetInt(DicomDataset dataset, DicomTag tag) =>
        dataset.TryGetSingleValue(tag, out int value) ? value : null;
}
