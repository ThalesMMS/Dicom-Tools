using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using FellowOakDicom;
using FellowOakDicom.Imaging;
using FellowOakDicom.Network;

namespace DicomTools.Tests;

public class CliContractTests
{
    private readonly string _sampleFile = SampleSeriesHelper.GetFirstFilePath();

    [Fact]
    public void Info_Produces_Metadata_AsJson()
    {
        var result = CliRunner.Run("info", _sampleFile, "--json");
        Assert.Equal(0, result.ExitCode);
        using var doc = JsonDocument.Parse(result.Stdout);
        var root = doc.RootElement;

        Assert.True(root.GetProperty("Rows").GetInt32() > 0);
        Assert.True(root.GetProperty("Columns").GetInt32() > 0);
        Assert.False(string.IsNullOrWhiteSpace(root.GetProperty("StudyInstanceUid").GetString()));
        Assert.False(string.IsNullOrWhiteSpace(root.GetProperty("SopInstanceUid").GetString()));
        Assert.False(string.IsNullOrWhiteSpace(root.GetProperty("PhotometricInterpretation").GetString()));
        Assert.True(root.GetProperty("NumberOfFrames").GetInt32() >= 1);
    }

    [Fact]
    public void Anonymize_Creates_New_File_With_Different_Identifiers()
    {
        var outputPath = Path.Combine(Path.GetTempPath(), $"anon-{Guid.NewGuid():N}.dcm");
        try
        {
            var result = CliRunner.Run("anonymize", _sampleFile, "--output", outputPath);
            Assert.Equal(0, result.ExitCode);
            Assert.True(File.Exists(outputPath));

            var original = DicomFile.Open(_sampleFile);
            var anonymized = DicomFile.Open(outputPath);

            var originalUid = original.Dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID);
            var anonymizedUid = anonymized.Dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID);
            Assert.NotEqual(originalUid, anonymizedUid);
            original.Dataset.TryGetString(DicomTag.PatientName, out var originalName);
            anonymized.Dataset.TryGetString(DicomTag.PatientName, out var anonName);
            Assert.NotEqual(originalName ?? string.Empty, anonName ?? string.Empty);

            var originalPixels = DicomPixelData.Create(original.Dataset, false).GetFrame(0).Data;
            var anonymizedPixels = DicomPixelData.Create(anonymized.Dataset, false).GetFrame(0).Data;
            Assert.Equal(originalPixels, anonymizedPixels);
        }
        finally
        {
            if (File.Exists(outputPath))
            {
                File.Delete(outputPath);
            }
        }
    }

    [Fact]
    public void ToImage_Writes_Png_Header()
    {
        var outputPath = Path.Combine(Path.GetTempPath(), $"preview-{Guid.NewGuid():N}.png");
        try
        {
            var result = CliRunner.Run("to-image", _sampleFile, "--output", outputPath);
            Assert.Equal(0, result.ExitCode);
            Assert.True(File.Exists(outputPath));

            var bytes = File.ReadAllBytes(outputPath);
            Assert.True(bytes.Length > 8);
            var signature = bytes.Take(8).ToArray();
            Assert.Equal(new byte[] { 0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A }, signature);
        }
        finally
        {
            if (File.Exists(outputPath))
            {
                File.Delete(outputPath);
            }
        }
    }

    [Fact]
    public void Transcode_Writes_Target_Syntax()
    {
        var outputPath = Path.Combine(Path.GetTempPath(), $"transcode-{Guid.NewGuid():N}.dcm");
        try
        {
            var result = CliRunner.Run("transcode", _sampleFile, "--output", outputPath, "--transfer-syntax", "implicit");
            Assert.Equal(0, result.ExitCode);
            var transcoded = DicomFile.Open(outputPath);

            Assert.Equal(DicomTransferSyntax.ImplicitVRLittleEndian.UID.UID, transcoded.FileMetaInfo.TransferSyntax?.UID?.UID);
            var original = DicomFile.Open(_sampleFile);
            var originalPixels = DicomPixelData.Create(original.Dataset, false).GetFrame(0).Data;
            var transcodedPixels = DicomPixelData.Create(transcoded.Dataset, false).GetFrame(0).Data;
            Assert.Equal(originalPixels, transcodedPixels);
        }
        finally
        {
            if (File.Exists(outputPath))
            {
                File.Delete(outputPath);
            }
        }
    }

    [Fact]
    public void Validate_Returns_Ok()
    {
        var result = CliRunner.Run("validate", _sampleFile);
        Assert.Equal(0, result.ExitCode);
        Assert.Contains("validation ok", result.Stdout, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void Dump_Prints_Dataset_Content()
    {
        var result = CliRunner.Run("dump", _sampleFile, "--depth", "1", "--max-value-length", "120");
        Assert.Equal(0, result.ExitCode);
        Assert.Contains("(0028,0010)", result.Stdout); // Rows tag
        Assert.True(result.Stdout.Length > 0);
    }

    [Fact]
    public void Stats_Returns_Json_With_Bounds()
    {
        var result = CliRunner.Run("stats", _sampleFile, "--json");
        Assert.Equal(0, result.ExitCode);

        using var doc = JsonDocument.Parse(result.Stdout);
        var root = doc.RootElement;
        var min = root.GetProperty("Minimum").GetDouble();
        var max = root.GetProperty("Maximum").GetDouble();
        var count = root.GetProperty("Count").GetInt32();

        Assert.True(count > 0);
        Assert.True(min <= max);
        Assert.InRange(root.GetProperty("Mean").GetDouble(), min, max);
        Assert.True(root.GetProperty("Width").GetInt32() > 0);
        Assert.True(root.GetProperty("Height").GetInt32() > 0);
    }

    [Fact]
    public void Histogram_Returns_Counts_With_Configured_Bins()
    {
        const int bins = 32;
        var result = CliRunner.Run("histogram", _sampleFile, "--bins", bins.ToString(), "--json");
        Assert.Equal(0, result.ExitCode);

        using var doc = JsonDocument.Parse(result.Stdout);
        var root = doc.RootElement;
        var counts = root.GetProperty("Counts").EnumerateArray().Select(e => e.GetInt32()).ToArray();
        var countTotal = counts.Sum();
        var expectedCount = root.GetProperty("Count").GetInt32();

        Assert.Equal(bins, counts.Length);
        Assert.True(countTotal > 0);
        Assert.Equal(expectedCount, countTotal);
    }

    [Fact]
    public async Task Echo_Completes_RoundTrip()
    {
        CiEnvironment.SkipIfCi("Skipping echo loopback in CI to avoid socket restrictions");
        var port = TcpPortHelper.GetFreePort();
        using var server = DicomServerFactory.Create<DicomCEchoProvider>(port);
        await Task.Delay(100);

        var result = CliRunner.Run("echo", $"127.0.0.1:{port}");
        Assert.Equal(0, result.ExitCode);
        Assert.Contains("echo", result.Stdout, StringComparison.OrdinalIgnoreCase);
    }
}
