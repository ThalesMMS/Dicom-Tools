using System.Text;
using System.Text.Json;
using System.Linq;
using FellowOakDicom;
using FellowOakDicom.Imaging;
using FellowOakDicom.Imaging.Codec;
using FellowOakDicom.IO.Buffer;
using FellowOakDicom.IO;
using FellowOakDicom.Network;
using FellowOakDicom.Network.Client;
using SixLabors.ImageSharp;
using SixLabors.ImageSharp.PixelFormats;

namespace DicomTools.Cli;

public static class Program
{
    public static async Task<int> Main(string[] args)
    {
        return await CliApp.RunAsync(args);
    }
}

internal static class CliApp
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true
    };

    internal static async Task<int> RunAsync(string[] args)
    {
        Console.OutputEncoding = Encoding.UTF8;
        if (args.Length == 0 || args[0] is "-h" or "--help")
        {
            PrintUsage();
            return 1;
        }

        var command = args[0].ToLowerInvariant();
        var parser = new OptionParser(args.Skip(1));

        try
        {
            return command switch
            {
                "info" => Info(parser),
                "anonymize" => Anonymize(parser),
                "to-image" => ToImage(parser),
                "transcode" => Transcode(parser),
                "validate" => Validate(parser),
                "echo" => await EchoAsync(parser),
                "dump" => Dump(parser),
                "stats" => Stats(parser),
                "histogram" => Histogram(parser),
                _ => Unknown(command)
            };
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"error: {ex.Message}");
            return 1;
        }
    }

    private static void PrintUsage()
    {
        const string usage = """
        DicomTools.Cli (fo-dicom) - operações suportadas:
          info <input> [--json]
          anonymize <input> --output <path>
          to-image <input> --output <path> [--frame N] [--format png|jpeg]
          transcode <input> --output <path> --transfer-syntax <syntax>
          validate <input>
          echo <host:port>
          dump <input> [--depth N] [--max-value-length N]
          stats <input> [--frame N] [--json]
          histogram <input> [--bins N] [--frame N] [--json]
        """;
        Console.WriteLine(usage);
    }

    private static int Unknown(string command)
    {
        Console.Error.WriteLine($"unknown command: {command}");
        PrintUsage();
        return 1;
    }

    private static int Info(OptionParser parser)
    {
        var input = parser.RequirePositional("input");
        var file = DicomFile.Open(input);
        var pixelData = TryGetPixelData(file.Dataset);
        var metadata = BuildInfoMetadata(file, pixelData);

        if (parser.HasFlag("json"))
        {
            Console.WriteLine(JsonSerializer.Serialize(metadata, JsonOptions));
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
            PatientName = TryGetString(dataset, DicomTag.PatientName),
            PatientId = TryGetString(dataset, DicomTag.PatientID),
            StudyInstanceUid = TryGetString(dataset, DicomTag.StudyInstanceUID),
            SeriesInstanceUid = TryGetString(dataset, DicomTag.SeriesInstanceUID),
            SopInstanceUid = TryGetString(dataset, DicomTag.SOPInstanceUID),
            Modality = TryGetString(dataset, DicomTag.Modality),
            TransferSyntax = file.FileMetaInfo.TransferSyntax?.UID?.UID ?? string.Empty,
            Rows = pixelData?.Height ?? TryGetUShort(dataset, DicomTag.Rows) ?? 0,
            Columns = pixelData?.Width ?? TryGetUShort(dataset, DicomTag.Columns) ?? 0,
            NumberOfFrames = pixelData?.NumberOfFrames ?? TryGetInt(dataset, DicomTag.NumberOfFrames) ?? 1,
            BitsAllocated = pixelData?.BitsAllocated ?? TryGetUShort(dataset, DicomTag.BitsAllocated),
            PhotometricInterpretation = TryGetString(dataset, DicomTag.PhotometricInterpretation)
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

    private static int Anonymize(OptionParser parser)
    {
        var input = parser.RequirePositional("input");
        var output = parser.GetOption("output", "o") ?? BuildDefaultOutput(input, "_anon.dcm");
        EnsureParentDirectory(output);

        var file = DicomFile.Open(input);
        var anonymizer = new DicomAnonymizer();
        var anonymized = anonymizer.Anonymize(file.Dataset);
        var outputFile = new DicomFile(anonymized);
        outputFile.Save(output);

        Console.WriteLine($"Saved anonymized file to {output}");
        return 0;
    }

    private static int ToImage(OptionParser parser)
    {
        var input = parser.RequirePositional("input");
        var frame = parser.GetIntOption("frame") ?? 0;
        var format = parser.GetOption("format", "f");
        var output = parser.GetOption("output", "o") ?? BuildDefaultOutput(input, $".{format ?? "png"}");
        EnsureParentDirectory(output);

        var pixelSeries = ExtractPixelValues(input, frame);
        if (pixelSeries.Values.Count < pixelSeries.Width * pixelSeries.Height)
        {
            throw new InvalidOperationException("pixel data is incomplete for rendering");
        }

        var min = pixelSeries.Values.Min();
        var max = pixelSeries.Values.Max();
        var range = Math.Max(1, max - min);

        using var image = new Image<L16>(pixelSeries.Width, pixelSeries.Height);
        for (var y = 0; y < pixelSeries.Height; y++)
        {
            for (var x = 0; x < pixelSeries.Width; x++)
            {
                var value = pixelSeries.Values[y * pixelSeries.Width + x];
                var scaled = (ushort)Math.Clamp(((value - min) / range) * ushort.MaxValue, ushort.MinValue, ushort.MaxValue);
                image[x, y] = new L16(scaled);
            }
        }

        image.Save(output);

        Console.WriteLine($"Saved image to {output}");
        return 0;
    }

    private static int Transcode(OptionParser parser)
    {
        var input = parser.RequirePositional("input");
        var output = parser.GetOption("output", "o") ?? BuildDefaultOutput(input, "_transcoded.dcm");
        var syntaxKey = parser.GetOption("transfer-syntax", "syntax") ?? "explicit";
        EnsureParentDirectory(output);

        var targetSyntax = ResolveTransferSyntax(syntaxKey);
        var file = DicomFile.Open(input);

        var transcoder = new DicomTranscoder(file.FileMetaInfo.TransferSyntax, targetSyntax);
        var transcoded = transcoder.Transcode(file);
        transcoded.Save(output);

        Console.WriteLine($"Transcoded to {targetSyntax.UID.UID} -> {output}");
        return 0;
    }

    private static int Validate(OptionParser parser)
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

    private static async Task<int> EchoAsync(OptionParser parser)
    {
        var target = parser.RequirePositional("host:port");
        var (host, port) = ParseHostPort(target);

        var client = DicomClientFactory.Create(host, port, useTls: false, callingAe: "SCU", calledAe: "ANY-SCP");
        var request = new DicomCEchoRequest();

        DicomStatus? status = null;
        request.OnResponseReceived += (_, response) => status = response.Status;

        await client.AddRequestAsync(request);
        await client.SendAsync();

        if (status == DicomStatus.Success)
        {
            Console.WriteLine($"echo to {host}:{port} succeeded");
            return 0;
        }

        Console.Error.WriteLine($"echo to {host}:{port} failed ({status?.Description ?? "no response"})");
        return 1;
    }

    private static int Dump(OptionParser parser)
    {
        var input = parser.RequirePositional("input");
        var depth = parser.GetIntOption("depth") ?? 4;
        var maxValueLength = parser.GetIntOption("max-value-length") ?? 64;

        var dataset = DicomFile.Open(input).Dataset;
        DumpDataset(dataset, 0, depth, maxValueLength);
        return 0;
    }

    private static int Stats(OptionParser parser)
    {
        var input = parser.RequirePositional("input");
        var frame = parser.GetIntOption("frame") ?? 0;
        var pixelSeries = ExtractPixelValues(input, frame);
        var stats = CalculateStats(pixelSeries.Values);

        var result = new StatsResult
        {
            Width = pixelSeries.Width,
            Height = pixelSeries.Height,
            FrameIndex = pixelSeries.FrameIndex,
            Frames = pixelSeries.FrameCount,
            Count = pixelSeries.Values.Count,
            Minimum = stats.Min,
            Maximum = stats.Max,
            Mean = stats.Mean,
            StandardDeviation = stats.StdDev
        };

        if (parser.HasFlag("json"))
        {
            Console.WriteLine(JsonSerializer.Serialize(result, JsonOptions));
        }
        else
        {
            Console.WriteLine($"Size: {result.Width}x{result.Height} (frame {result.FrameIndex + 1}/{result.Frames})");
            Console.WriteLine($"Count: {result.Count}");
            Console.WriteLine($"Min: {result.Minimum}");
            Console.WriteLine($"Max: {result.Maximum}");
            Console.WriteLine($"Mean: {result.Mean:F2}");
            Console.WriteLine($"StdDev: {result.StandardDeviation:F2}");
        }

        return 0;
    }

    private static int Histogram(OptionParser parser)
    {
        var input = parser.RequirePositional("input");
        var bins = parser.GetIntOption("bins") ?? 256;
        var frame = parser.GetIntOption("frame") ?? 0;

        var pixelSeries = ExtractPixelValues(input, frame);
        var stats = CalculateStats(pixelSeries.Values);
        var histogram = BuildHistogram(pixelSeries.Values, bins, stats.Min, stats.Max);

        var result = new HistogramResult
        {
            Width = pixelSeries.Width,
            Height = pixelSeries.Height,
            FrameIndex = pixelSeries.FrameIndex,
            Frames = pixelSeries.FrameCount,
            Minimum = stats.Min,
            Maximum = stats.Max,
            Bins = bins,
            Count = pixelSeries.Values.Count,
            Counts = histogram
        };

        if (parser.HasFlag("json"))
        {
            Console.WriteLine(JsonSerializer.Serialize(result, JsonOptions));
        }
        else
        {
            Console.WriteLine($"Histogram (bins={bins}, frame {result.FrameIndex + 1}/{result.Frames})");
            Console.WriteLine($"Min: {stats.Min}, Max: {stats.Max}");
            Console.WriteLine(string.Join(',', histogram.Take(10)) + (histogram.Length > 10 ? ", ..." : string.Empty));
        }

        return 0;
    }

    private static StatsSummary CalculateStats(IReadOnlyList<double> values)
    {
        if (values.Count == 0)
        {
            return new StatsSummary(0, 0, 0, 0);
        }

        double min = values[0];
        double max = values[0];
        double sum = 0;
        foreach (var value in values)
        {
            if (value < min)
            {
                min = value;
            }
            if (value > max)
            {
                max = value;
            }
            sum += value;
        }

        var mean = sum / values.Count;
        double variance = 0;
        foreach (var value in values)
        {
            var diff = value - mean;
            variance += diff * diff;
        }
        variance /= values.Count;

        return new StatsSummary(min, max, mean, Math.Sqrt(variance));
    }

    private static int[] BuildHistogram(IReadOnlyList<double> values, int bins, double min, double max)
    {
        var counts = new int[bins];
        if (values.Count == 0 || bins <= 0)
        {
            return counts;
        }

        var range = max - min;
        var step = range <= 0 ? 1.0 : range / bins;

        foreach (var value in values)
        {
            var index = step <= 0 ? 0 : (int)((value - min) / step);
            if (index >= bins)
            {
                index = bins - 1;
            }
            if (index < 0)
            {
                index = 0;
            }

            counts[index]++;
        }

        return counts;
    }

    private static PixelSeries ExtractPixelValues(string path, int frameIndex)
    {
        var dataset = DicomFile.Open(path).Dataset;
        var pixelData = DicomPixelData.Create(dataset, false);
        if (pixelData.NumberOfFrames == 0)
        {
            throw new InvalidOperationException("dataset does not contain frames");
        }

        if (frameIndex < 0 || frameIndex >= pixelData.NumberOfFrames)
        {
            frameIndex = 0;
        }

        var buffer = pixelData.GetFrame(frameIndex);
        var bytes = buffer.Data;
        var bytesPerSample = pixelData.BitsAllocated / 8;
        if (bytesPerSample <= 0)
        {
            throw new InvalidOperationException($"unsupported BitsAllocated={pixelData.BitsAllocated}");
        }

        var sampleCount = bytes.Length / bytesPerSample;
        var values = new double[sampleCount];
        var signed = pixelData.PixelRepresentation == PixelRepresentation.Signed;
        var littleEndian = dataset.InternalTransferSyntax.Endian == Endian.Little;

        for (var i = 0; i < sampleCount; i++)
        {
            var offset = i * bytesPerSample;
            values[i] = pixelData.BitsAllocated switch
            {
                8 => signed ? (sbyte)bytes[offset] : bytes[offset],
                16 => littleEndian
                    ? signed ? BitConverter.ToInt16(bytes, offset) : BitConverter.ToUInt16(bytes, offset)
                    : signed ? BitConverter.ToInt16(new[] { bytes[offset + 1], bytes[offset] }, 0) : BitConverter.ToUInt16(new[] { bytes[offset + 1], bytes[offset] }, 0),
                32 => littleEndian
                    ? signed ? BitConverter.ToInt32(bytes, offset) : BitConverter.ToUInt32(bytes, offset)
                    : signed ? BitConverter.ToInt32(new[] { bytes[offset + 3], bytes[offset + 2], bytes[offset + 1], bytes[offset] }, 0) : BitConverter.ToUInt32(new[] { bytes[offset + 3], bytes[offset + 2], bytes[offset + 1], bytes[offset] }, 0),
                _ => throw new NotSupportedException($"unsupported BitsAllocated={pixelData.BitsAllocated}")
            };
        }

        return new PixelSeries(pixelData.Width, pixelData.Height, pixelData.NumberOfFrames, frameIndex, values);
    }

    private static (string Host, int Port) ParseHostPort(string target)
    {
        var parts = target.Split(':', 2);
        if (parts.Length != 2 || !int.TryParse(parts[1], out var port))
        {
            throw new ArgumentException("echo target must be in form host:port");
        }

        return (parts[0], port);
    }

    private static DicomTransferSyntax ResolveTransferSyntax(string value)
    {
        var key = value.Trim().ToLowerInvariant();
        return key switch
        {
            "explicit" or "explicit-little" or "evr" => DicomTransferSyntax.ExplicitVRLittleEndian,
            "implicit" or "implicit-little" or "ivr" => DicomTransferSyntax.ImplicitVRLittleEndian,
            "big" or "explicit-be" or "be" => DicomTransferSyntax.ExplicitVRBigEndian,
            "jpeg2000" or "j2k" or "jp2" => DicomTransferSyntax.JPEG2000Lossless,
            "rle" => DicomTransferSyntax.RLELossless,
            "jpegls" or "jpeg-ls" => DicomTransferSyntax.JPEGLSLossless,
            "jpeg-lossless" or "jpeg-lossless-14" => DicomTransferSyntax.JPEGProcess14SV1,
            _ => DicomTransferSyntax.ExplicitVRLittleEndian
        };
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

    private static void EnsureTag(DicomDataset dataset, DicomTag tag, string name, List<string> errors)
    {
        if (!dataset.TryGetString(tag, out var value) || string.IsNullOrWhiteSpace(value))
        {
            errors.Add($"missing {name}");
        }
    }

    private static void DumpDataset(DicomDataset dataset, int level, int maxDepth, int maxValueLength)
    {
        if (level > maxDepth)
        {
            return;
        }

        foreach (var item in dataset)
        {
            var indent = new string(' ', level * 2);
            switch (item)
            {
                case DicomElement element:
                    var rendered = element.ToString();
                    if (rendered.Length > maxValueLength)
                    {
                        rendered = rendered[..maxValueLength] + "...";
                    }
                    Console.WriteLine($"{indent}{rendered}");
                    break;
                case DicomSequence sequence:
                    Console.WriteLine($"{indent}{sequence.Tag} SQ ({sequence.Items.Count} items)");
                    var index = 0;
                    foreach (var sqItem in sequence.Items)
                    {
                        Console.WriteLine($"{indent}  Item {index++}");
                        DumpDataset(sqItem, level + 2, maxDepth, maxValueLength);
                    }
                    break;
                default:
                    Console.WriteLine($"{indent}{item.Tag} {item.ValueRepresentation.Code}");
                    break;
            }
        }
    }

    private static void EnsureParentDirectory(string path)
    {
        var directory = Path.GetDirectoryName(path);
        if (!string.IsNullOrWhiteSpace(directory))
        {
            Directory.CreateDirectory(directory);
        }
    }

    private static string BuildDefaultOutput(string input, string suffix)
    {
        var directory = Path.GetDirectoryName(input) ?? ".";
        var filename = Path.GetFileNameWithoutExtension(input);
        return Path.Combine(directory, $"{filename}{suffix}");
    }

    private static string? TryGetString(DicomDataset dataset, DicomTag tag) =>
        dataset.TryGetString(tag, out var value) ? value : null;

    private static ushort? TryGetUShort(DicomDataset dataset, DicomTag tag) =>
        dataset.TryGetSingleValue(tag, out ushort value) ? value : null;

    private static int? TryGetInt(DicomDataset dataset, DicomTag tag) =>
        dataset.TryGetSingleValue(tag, out int value) ? value : null;
}

internal sealed class OptionParser
{
    private static readonly HashSet<string> FlagOptions = new(StringComparer.OrdinalIgnoreCase)
    {
        "json",
        "verbose",
        "help"
    };

    private readonly List<string> _positionals = new();
    private readonly Dictionary<string, string> _options = new(StringComparer.OrdinalIgnoreCase);
    private readonly HashSet<string> _flags = new(StringComparer.OrdinalIgnoreCase);

    internal OptionParser(IEnumerable<string> args)
    {
        var tokens = args.ToArray();
        for (var i = 0; i < tokens.Length; i++)
        {
            var token = tokens[i];
            if (token.StartsWith('-'))
            {
                var name = Normalize(token);
                if (FlagOptions.Contains(name))
                {
                    _flags.Add(name);
                    continue;
                }

                string value = "true";
                if (i + 1 < tokens.Length && !tokens[i + 1].StartsWith('-'))
                {
                    value = tokens[i + 1];
                    i++;
                }

                _options[name] = value;
            }
            else
            {
                _positionals.Add(token);
            }
        }
    }

    internal string RequirePositional(string name)
    {
        if (_positionals.Count == 0)
        {
            throw new ArgumentException($"{name} is required");
        }

        var value = _positionals[0];
        _positionals.RemoveAt(0);
        return value;
    }

    internal string? GetOption(params string[] names)
    {
        foreach (var name in names)
        {
            var key = Normalize(name);
            if (_options.TryGetValue(key, out var value))
            {
                return value;
            }
        }

        return null;
    }

    internal int? GetIntOption(params string[] names)
    {
        var value = GetOption(names);
        if (value != null && int.TryParse(value, out var parsed))
        {
            return parsed;
        }

        return null;
    }

    internal bool HasFlag(params string[] names)
    {
        return names.Any(name => _flags.Contains(Normalize(name)));
    }

    private static string Normalize(string name) => name.TrimStart('-');
}

internal sealed class PixelSeries
{
    internal PixelSeries(int width, int height, int frameCount, int frameIndex, IReadOnlyList<double> values)
    {
        Width = width;
        Height = height;
        FrameCount = frameCount;
        FrameIndex = frameIndex;
        Values = values;
    }

    internal int Width { get; }
    internal int Height { get; }
    internal int FrameCount { get; }
    internal int FrameIndex { get; }
    internal IReadOnlyList<double> Values { get; }
}

internal sealed class InfoMetadata
{
    public string? PatientName { get; set; }
    public string? PatientId { get; set; }
    public string? StudyInstanceUid { get; set; }
    public string? SeriesInstanceUid { get; set; }
    public string? SopInstanceUid { get; set; }
    public string? Modality { get; set; }
    public string? TransferSyntax { get; set; }
    public int Rows { get; set; }
    public int Columns { get; set; }
    public int NumberOfFrames { get; set; }
    public ushort? BitsAllocated { get; set; }
    public string? PhotometricInterpretation { get; set; }
}

internal sealed class StatsResult
{
    public int Width { get; set; }
    public int Height { get; set; }
    public int FrameIndex { get; set; }
    public int Frames { get; set; }
    public int Count { get; set; }
    public double Minimum { get; set; }
    public double Maximum { get; set; }
    public double Mean { get; set; }
    public double StandardDeviation { get; set; }
}

internal sealed class HistogramResult
{
    public int Width { get; set; }
    public int Height { get; set; }
    public int FrameIndex { get; set; }
    public int Frames { get; set; }
    public double Minimum { get; set; }
    public double Maximum { get; set; }
    public int Bins { get; set; }
    public int Count { get; set; }
    public int[] Counts { get; set; } = Array.Empty<int>();
}

internal readonly record struct StatsSummary(double Min, double Max, double Mean, double StdDev);
