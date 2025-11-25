using DicomTools.Cli;

namespace DicomTools.Tests;

public class CliUnitTests
{
    [Theory]
    [InlineData("explicit", "1.2.840.10008.1.2.1")]
    [InlineData("implicit", "1.2.840.10008.1.2")]
    [InlineData("big", "1.2.840.10008.1.2.2")]
    [InlineData("jpeg2000", "1.2.840.10008.1.2.4.90")]
    [InlineData("rle", "1.2.840.10008.1.2.5")]
    [InlineData("jpegls", "1.2.840.10008.1.2.4.80")]
    [InlineData("jpeg-lossless", "1.2.840.10008.1.2.4.70")]
    public void Transcode_Respects_Syntax_Aliases(string alias, string expectedUid)
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"tx-alias-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var input = SampleSeriesHelper.GetFirstFilePath();
        var output = Path.Combine(tempDir, $"out-{alias}.dcm");

        try
        {
            var result = CliRunner.Run("transcode", input, "--output", output, "--transfer-syntax", alias);
            if (result.ExitCode != 0)
            {
                Assert.Contains("not supported", result.Stderr + result.Stdout, StringComparison.OrdinalIgnoreCase);
                return;
            }

            var transcoded = FellowOakDicom.DicomFile.Open(output);
            Assert.Equal(expectedUid, transcoded.FileMetaInfo.TransferSyntax.UID.UID);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void Info_Handles_File_Without_PixelData()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"info-nopixel-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var dicomPath = Path.Combine(tempDir, "nopixel.dcm");

        try
        {
            var dataset = new FellowOakDicom.DicomDataset
            {
                { FellowOakDicom.DicomTag.SOPClassUID, FellowOakDicom.DicomUID.SecondaryCaptureImageStorage },
                { FellowOakDicom.DicomTag.SOPInstanceUID, FellowOakDicom.DicomUIDGenerator.GenerateDerivedFromUUID() },
                { FellowOakDicom.DicomTag.PatientID, "NO-PIX" },
                { FellowOakDicom.DicomTag.Modality, "OT" }
            };
            new FellowOakDicom.DicomFile(dataset).Save(dicomPath);

            var result = CliRunner.Run("info", dicomPath);
            Assert.Equal(0, result.ExitCode);
            Assert.Contains("NO-PIX", result.Stdout);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void ToImage_Falls_Back_To_Frame0_When_OutOfRange()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"toimage-frame-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var input = SampleSeriesHelper.GetFirstFilePath();
        var output = Path.Combine(tempDir, "frame99.png");

        try
        {
            var result = CliRunner.Run("to-image", input, "--frame", "99", "--output", output);
            Assert.Equal(0, result.ExitCode);
            Assert.True(File.Exists(output));
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void Echo_Fails_When_Port_Closed()
    {
        var port = TcpPortHelper.GetFreePort();
        var result = CliRunner.Run("echo", $"127.0.0.1:{port}");
        Assert.NotEqual(0, result.ExitCode);
        Assert.NotEmpty(result.Stderr + result.Stdout);
    }

    [Fact]
    public void Dump_Stops_When_Depth_Reached()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"dump-depth-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var dicomPath = Path.Combine(tempDir, "depth.dcm");

        try
        {
            var seqItem = new FellowOakDicom.DicomDataset
            {
                { FellowOakDicom.DicomTag.PatientName, "DEPTH^ITEM" }
            };
            var dataset = new FellowOakDicom.DicomDataset
            {
                { FellowOakDicom.DicomTag.SOPClassUID, FellowOakDicom.DicomUID.SecondaryCaptureImageStorage },
                { FellowOakDicom.DicomTag.SOPInstanceUID, FellowOakDicom.DicomUIDGenerator.GenerateDerivedFromUUID() },
                { FellowOakDicom.DicomTag.PatientID, "DEPTH-1" },
                { FellowOakDicom.DicomTag.PerFrameFunctionalGroupsSequence, new FellowOakDicom.DicomSequence(FellowOakDicom.DicomTag.PerFrameFunctionalGroupsSequence, seqItem) }
            };
            new FellowOakDicom.DicomFile(dataset).Save(dicomPath);

            var dump = CliRunner.Run("dump", dicomPath, "--depth", "0");
            Assert.Equal(0, dump.ExitCode);
            Assert.Contains("SQ", dump.Stdout);
            Assert.DoesNotContain("DEPTH^ITEM", dump.Stdout);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

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
