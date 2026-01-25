namespace DicomTools.Cli;

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
