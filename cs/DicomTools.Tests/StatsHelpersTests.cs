using DicomTools.Cli;

namespace DicomTools.Tests;

public class StatsHelpersTests
{
    [Fact]
    public void CalculateStats_Returns_Zeros_For_Empty_List()
    {
        var stats = StatsHelpers.CalculateStats(Array.Empty<double>());

        Assert.Equal(0, stats.Min);
        Assert.Equal(0, stats.Max);
        Assert.Equal(0, stats.Mean);
        Assert.Equal(0, stats.StdDev);
    }

    [Fact]
    public void CalculateStats_Handles_Single_Value()
    {
        var stats = StatsHelpers.CalculateStats(new[] { 42.0 });

        Assert.Equal(42.0, stats.Min);
        Assert.Equal(42.0, stats.Max);
        Assert.Equal(42.0, stats.Mean);
        Assert.Equal(0, stats.StdDev);
    }

    [Fact]
    public void CalculateStats_Calculates_Correct_Min_Max()
    {
        var values = new[] { 5.0, 2.0, 8.0, 1.0, 9.0 };
        var stats = StatsHelpers.CalculateStats(values);

        Assert.Equal(1.0, stats.Min);
        Assert.Equal(9.0, stats.Max);
    }

    [Fact]
    public void CalculateStats_Calculates_Correct_Mean()
    {
        var values = new[] { 10.0, 20.0, 30.0 };
        var stats = StatsHelpers.CalculateStats(values);

        Assert.Equal(20.0, stats.Mean);
    }

    [Fact]
    public void CalculateStats_Calculates_Correct_StdDev()
    {
        var values = new[] { 2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0 };
        var stats = StatsHelpers.CalculateStats(values);

        Assert.Equal(2.0, stats.StdDev, 5);
    }

    [Fact]
    public void CalculateStats_Handles_Negative_Values()
    {
        var values = new[] { -5.0, -2.0, 0.0, 3.0, 7.0 };
        var stats = StatsHelpers.CalculateStats(values);

        Assert.Equal(-5.0, stats.Min);
        Assert.Equal(7.0, stats.Max);
        Assert.Equal(0.6, stats.Mean, 5);
    }

    [Fact]
    public void BuildHistogram_Returns_Empty_For_Empty_Values()
    {
        var histogram = StatsHelpers.BuildHistogram(Array.Empty<double>(), 10, 0, 100);

        Assert.Equal(10, histogram.Length);
        Assert.All(histogram, count => Assert.Equal(0, count));
    }

    [Fact]
    public void BuildHistogram_Returns_Empty_For_Zero_Bins()
    {
        var values = new[] { 1.0, 2.0, 3.0 };
        var histogram = StatsHelpers.BuildHistogram(values, 0, 1, 3);

        Assert.Empty(histogram);
    }

    [Fact]
    public void BuildHistogram_Distributes_Values_Correctly()
    {
        var values = new[] { 0.0, 25.0, 50.0, 75.0, 100.0 };
        var histogram = StatsHelpers.BuildHistogram(values, 4, 0, 100);

        Assert.Equal(4, histogram.Length);
        Assert.Equal(1, histogram[0]);
        Assert.Equal(1, histogram[1]);
        Assert.Equal(1, histogram[2]);
        Assert.Equal(2, histogram[3]);
    }

    [Fact]
    public void BuildHistogram_Handles_All_Same_Values()
    {
        var values = new[] { 50.0, 50.0, 50.0, 50.0 };
        var histogram = StatsHelpers.BuildHistogram(values, 5, 50, 50);

        Assert.Equal(5, histogram.Length);
        Assert.Equal(4, histogram[0]);
    }

    [Fact]
    public void BuildHistogram_Clamps_Out_Of_Range_Values()
    {
        var values = new[] { -10.0, 0.0, 50.0, 100.0, 150.0 };
        var histogram = StatsHelpers.BuildHistogram(values, 2, 0, 100);

        Assert.Equal(2, histogram.Length);
        Assert.Equal(2, histogram[0]);
        Assert.Equal(3, histogram[1]);
    }

    [Fact]
    public void BuildHistogram_Handles_Large_Bin_Count()
    {
        var values = new[] { 0.0, 50.0, 100.0 };
        var histogram = StatsHelpers.BuildHistogram(values, 100, 0, 100);

        Assert.Equal(100, histogram.Length);
        Assert.Equal(3, histogram.Sum());
    }

    [Fact]
    public void CalculateStats_Handles_Large_Dataset()
    {
        var values = Enumerable.Range(1, 10000).Select(x => (double)x).ToArray();
        var stats = StatsHelpers.CalculateStats(values);

        Assert.Equal(1.0, stats.Min);
        Assert.Equal(10000.0, stats.Max);
        Assert.Equal(5000.5, stats.Mean);
    }

    [Fact]
    public void CalculateStats_Handles_Decimal_Precision()
    {
        var values = new[] { 0.1, 0.2, 0.3 };
        var stats = StatsHelpers.CalculateStats(values);

        Assert.Equal(0.1, stats.Min, 10);
        Assert.Equal(0.3, stats.Max, 10);
        Assert.Equal(0.2, stats.Mean, 10);
    }
}
