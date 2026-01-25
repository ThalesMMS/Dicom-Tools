using FellowOakDicom;

namespace DicomTools.Cli;

internal static class AnonymizeCommand
{
    internal static int Execute(OptionParser parser)
    {
        var input = parser.RequirePositional("input");
        var output = parser.GetOption("output", "o") ?? CliHelpers.BuildDefaultOutput(input, "_anon.dcm");
        CliHelpers.EnsureParentDirectory(output);

        var file = DicomFile.Open(input);
        var anonymizer = new DicomAnonymizer();
        var anonymized = anonymizer.Anonymize(file.Dataset);
        var outputFile = new DicomFile(anonymized);
        outputFile.Save(output);

        Console.WriteLine($"Saved anonymized file to {output}");
        return 0;
    }
}
