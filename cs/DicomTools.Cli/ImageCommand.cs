using FellowOakDicom.Imaging;
using SixLabors.ImageSharp;
using SixLabors.ImageSharp.PixelFormats;

namespace DicomTools.Cli;

internal static class ImageCommand
{
    internal static int Execute(OptionParser parser)
    {
        var input = parser.RequirePositional("input");
        var frame = parser.GetIntOption("frame") ?? 0;
        var format = parser.GetOption("format", "f");
        var output = parser.GetOption("output", "o") ?? CliHelpers.BuildDefaultOutput(input, $".{format ?? "png"}");
        CliHelpers.EnsureParentDirectory(output);

        var pixelSeries = PixelDataHelpers.ExtractPixelValues(input, frame);
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
}
