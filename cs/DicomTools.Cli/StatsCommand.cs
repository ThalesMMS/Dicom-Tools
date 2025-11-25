using System.Text.Json;
using System.Linq;

namespace DicomTools.Cli;

internal static class StatsCommand
{
    internal static int ExecuteStats(OptionParser parser, JsonSerializerOptions jsonOptions)
    {
        var input = parser.RequirePositional("input");
        var frame = parser.GetIntOption("frame") ?? 0;
        var pixelSeries = PixelDataHelpers.ExtractPixelValues(input, frame);
        var stats = StatsHelpers.CalculateStats(pixelSeries.Values);

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
            Console.WriteLine(JsonSerializer.Serialize(result, jsonOptions));
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

    internal static int ExecuteHistogram(OptionParser parser, JsonSerializerOptions jsonOptions)
    {
        var input = parser.RequirePositional("input");
        var bins = parser.GetIntOption("bins") ?? 256;
        var frame = parser.GetIntOption("frame") ?? 0;

        var pixelSeries = PixelDataHelpers.ExtractPixelValues(input, frame);
        var stats = StatsHelpers.CalculateStats(pixelSeries.Values);
        var histogram = StatsHelpers.BuildHistogram(pixelSeries.Values, bins, stats.Min, stats.Max);

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
            Console.WriteLine(JsonSerializer.Serialize(result, jsonOptions));
        }
        else
        {
            Console.WriteLine($"Histogram (bins={bins}, frame {result.FrameIndex + 1}/{result.Frames})");
            Console.WriteLine($"Min: {stats.Min}, Max: {stats.Max}");
            Console.WriteLine(string.Join(',', histogram.Take(10)) + (histogram.Length > 10 ? ", ..." : string.Empty));
        }

        return 0;
    }
}
