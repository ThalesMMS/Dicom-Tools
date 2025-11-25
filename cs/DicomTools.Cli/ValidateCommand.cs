using FellowOakDicom;
using FellowOakDicom.Imaging;

namespace DicomTools.Cli;

internal static class ValidateCommand
{
    internal static int Execute(OptionParser parser)
    {
        var input = parser.RequirePositional("input");
        var file = DicomFile.Open(input);
        var dataset = file.Dataset;
        var errors = new List<string>();

        EnsureTag(dataset, DicomTag.SOPInstanceUID, "SOPInstanceUID", errors);
        EnsureTag(dataset, DicomTag.StudyInstanceUID, "StudyInstanceUID", errors);
        EnsureTag(dataset, DicomTag.SeriesInstanceUID, "SeriesInstanceUID", errors);

        if (dataset.Contains(DicomTag.PixelData))
        {
            try
            {
                _ = DicomPixelData.Create(dataset, false);
            }
            catch (Exception ex)
            {
                errors.Add($"PixelData not readable: {ex.Message}");
            }
        }

        if (errors.Count > 0)
        {
            Console.Error.WriteLine("validation failed:");
            foreach (var error in errors)
            {
                Console.Error.WriteLine($"- {error}");
            }

            return 1;
        }

        Console.WriteLine("validation ok");
        return 0;
    }

    private static void EnsureTag(DicomDataset dataset, DicomTag tag, string name, List<string> errors)
    {
        if (!dataset.TryGetString(tag, out var value) || string.IsNullOrWhiteSpace(value))
        {
            errors.Add($"missing {name}");
        }
    }
}
