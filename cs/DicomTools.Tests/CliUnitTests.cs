using DicomTools.Cli;

namespace DicomTools.Tests;

public class CliUnitTests
{
    [Fact]
    public void OptionParser_Parses_Flags_Options_And_Positionals()
    {
        var parser = new OptionParser(new[] { "--json", "--output", "path/file.dcm", "-f", "png", "input1", "input2" });

        Assert.True(parser.HasFlag("json"));
        Assert.Equal("path/file.dcm", parser.GetOption("output"));
        Assert.Equal("png", parser.GetOption("f"));

        Assert.Equal("input1", parser.RequirePositional("input"));
        Assert.Equal("input2", parser.RequirePositional("input"));
        Assert.Throws<ArgumentException>(() => parser.RequirePositional("missing"));
    }

    [Fact]
    public void ValidateCommand_Fails_When_Required_Tags_Missing()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"validate-missing-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var dicomPath = Path.Combine(tempDir, "missing.dcm");

        try
        {
            var dataset = new FellowOakDicom.DicomDataset
            {
                { FellowOakDicom.DicomTag.SOPClassUID, FellowOakDicom.DicomUID.SecondaryCaptureImageStorage },
                { FellowOakDicom.DicomTag.SOPInstanceUID, FellowOakDicom.DicomUIDGenerator.GenerateDerivedFromUUID() }
            };
            new FellowOakDicom.DicomFile(dataset).Save(dicomPath);

            var result = CliRunner.Run("validate", dicomPath);
            Assert.NotEqual(0, result.ExitCode);
            Assert.Contains("validation failed", result.Stderr, StringComparison.OrdinalIgnoreCase);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void UnknownCommand_Returns_Error_Code_And_Message()
    {
        var result = CliRunner.Run("unknown-cmd");
        Assert.Equal(1, result.ExitCode);
        Assert.Contains("unknown command", result.Stderr, StringComparison.OrdinalIgnoreCase);
    }
}
