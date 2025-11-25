namespace DicomTools.Cli;

internal static class StatsHelpers
{
    internal static StatsSummary CalculateStats(IReadOnlyList<double> values)
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

    internal static int[] BuildHistogram(IReadOnlyList<double> values, int bins, double min, double max)
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
}
