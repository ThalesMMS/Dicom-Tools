using System.Linq;
using FellowOakDicom;
using FellowOakDicom.Imaging;

namespace DicomTools.Tests;

public class SeriesLoadTests
{
    [Fact]
    public void EntireSeries_LoadsWithConsistentMetadata()
    {
        var paths = SampleSeriesHelper.GetAllSeriesFiles().ToArray();
        Assert.NotEmpty(paths);

        var files = paths.Select(path => DicomFile.Open(path)).ToArray();
        var first = files.First().Dataset;
        var expectedStudyUid = first.GetSingleValue<string>(DicomTag.StudyInstanceUID);
        var expectedSeriesUid = first.GetSingleValue<string>(DicomTag.SeriesInstanceUID);
        var expectedRows = first.GetSingleValue<ushort>(DicomTag.Rows);
        var expectedCols = first.GetSingleValue<ushort>(DicomTag.Columns);

        foreach (var file in files)
        {
            var ds = file.Dataset;
            Assert.Equal(expectedStudyUid, ds.GetSingleValue<string>(DicomTag.StudyInstanceUID));
            Assert.Equal(expectedSeriesUid, ds.GetSingleValue<string>(DicomTag.SeriesInstanceUID));
            Assert.Equal(expectedRows, ds.GetSingleValue<ushort>(DicomTag.Rows));
            Assert.Equal(expectedCols, ds.GetSingleValue<ushort>(DicomTag.Columns));

            var pixelData = DicomPixelData.Create(ds, false);
            Assert.Equal(expectedRows, pixelData.Height);
            Assert.Equal(expectedCols, pixelData.Width);
            Assert.True(pixelData.NumberOfFrames >= 1);
        }
    }

    [Fact]
    public void InstanceNumbers_CoverAllFiles()
    {
        var paths = SampleSeriesHelper.GetAllSeriesFiles().ToArray();
        var files = paths.Select(path => DicomFile.Open(path)).ToArray();

        var instanceNumbers = files
            .Select(f => f.Dataset.TryGetSingleValue(DicomTag.InstanceNumber, out int value) ? value : (int?)null)
            .Where(v => v.HasValue)
            .Select(v => v!.Value)
            .OrderBy(v => v)
            .ToArray();

        Assert.Equal(files.Length, instanceNumbers.Length);

        var expectedSequence = Enumerable.Range(instanceNumbers.First(), instanceNumbers.Length).ToArray();
        Assert.Equal(expectedSequence, instanceNumbers);
    }
}
