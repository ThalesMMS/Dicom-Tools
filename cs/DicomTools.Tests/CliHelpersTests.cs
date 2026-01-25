using DicomTools.Cli;
using FellowOakDicom;

namespace DicomTools.Tests;

public class CliHelpersTests
{
    [Fact]
    public async Task EchoCommand_Succeeds_Against_InMemoryStore()
    {
        if (CiEnvironment.ShouldSkip("Skipping echo loopback in CI to avoid socket restrictions"))
        {
            return;
        }
        var port = TcpPortHelper.GetFreePort();
        using var server = FellowOakDicom.Network.DicomServerFactory.Create<InMemoryStoreScp>(port);
        await Task.Delay(100);

        var result = CliRunner.Run("echo", $"127.0.0.1:{port}");
        Assert.Equal(0, result.ExitCode);
        Assert.Contains("succeeded", result.Stdout, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void StatsCommand_Prints_Text_Output()
    {
        var path = SampleSeriesHelper.GetFirstFilePath();
        var statsResult = CliRunner.Run("stats", path);
        Assert.Equal(0, statsResult.ExitCode);
        Assert.Contains("Size:", statsResult.Stdout, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Min:", statsResult.Stdout, StringComparison.OrdinalIgnoreCase);

        var histogramResult = CliRunner.Run("histogram", path, "--bins", "8");
        Assert.Equal(0, histogramResult.ExitCode);
        Assert.Contains("Histogram", histogramResult.Stdout, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void DumpCommand_Prints_Sequence_Items()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"dump-seq-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var dicomPath = Path.Combine(tempDir, "seq.dcm");

        try
        {
            var seqItem = new DicomDataset
            {
                { DicomTag.PatientName, "SEQ^ITEM" }
            };
            var dataset = new DicomDataset
            {
                { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage },
                { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
                { DicomTag.PatientID, "SEQ-1" },
                { DicomTag.PerFrameFunctionalGroupsSequence, new DicomSequence(DicomTag.PerFrameFunctionalGroupsSequence, seqItem) }
            };
            new DicomFile(dataset).Save(dicomPath);

            var dump = CliRunner.Run("dump", dicomPath, "--depth", "3", "--max-value-length", "50");
            Assert.Equal(0, dump.ExitCode);
            Assert.Contains("SQ", dump.Stdout);
            Assert.Contains("Item", dump.Stdout);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void PixelDataHelpers_Rejects_Invalid_Target()
    {
        Assert.Throws<ArgumentException>(() => PixelDataHelpers.ParseHostPort("invalid-host-port"));
    }

    [Fact]
    public void StatsHelpers_Handle_Empty_And_Constant_Data()
    {
        var emptyStats = StatsHelpers.CalculateStats(Array.Empty<double>());
        Assert.Equal(0, emptyStats.Min);
        Assert.Equal(0, emptyStats.Max);

        var histogram = StatsHelpers.BuildHistogram(new[] { 5.0, 5.0, 5.0 }, bins: 4, min: 5, max: 5);
        Assert.Equal(3, histogram.Sum());
        Assert.Equal(3, histogram.First());

        var zeroBin = StatsHelpers.BuildHistogram(new[] { 1.0, 2.0 }, bins: 0, min: 0, max: 2);
        Assert.Empty(zeroBin);
    }
}
