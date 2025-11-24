using System.Linq;
using FellowOakDicom;
using FellowOakDicom.Imaging;

namespace DicomTools.Tests;

public class SampleSeriesTests
{
    [Fact]
    public void SampleSeries_FilesRemainConsistent()
    {
        var files = SampleSeriesHelper.GetSeriesFiles(3)
            .Select(path => DicomFile.Open(path))
            .ToArray();

        Assert.NotEmpty(files);

        var studyUids = files
            .Select(f => f.Dataset.GetSingleValue<string>(DicomTag.StudyInstanceUID))
            .Distinct()
            .ToArray();
        var seriesUids = files
            .Select(f => f.Dataset.GetSingleValue<string>(DicomTag.SeriesInstanceUID))
            .Distinct()
            .ToArray();

        Assert.Single(studyUids);
        Assert.Single(seriesUids);

        var first = files[0].Dataset;
        var pixelData = DicomPixelData.Create(first, false);
        var frame = pixelData.GetFrame(0).Data;
        var rows = first.GetSingleValue<ushort>(DicomTag.Rows);
        var columns = first.GetSingleValue<ushort>(DicomTag.Columns);
        var bitsAllocated = first.GetSingleValue<ushort>(DicomTag.BitsAllocated);
        var expectedBytes = rows * columns * (bitsAllocated / 8);

        Assert.Equal(expectedBytes, frame.Length);
        Assert.True(pixelData.NumberOfFrames > 0);
    }

    [Fact]
    public void Anonymizer_OnSample_RetainsPixels()
    {
        var file = DicomFile.Open(SampleSeriesHelper.GetFirstFilePath());
        var originalPixels = DicomPixelData.Create(file.Dataset, false).GetFrame(0).Data;
        var originalUid = file.Dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID);
        file.Dataset.TryGetString(DicomTag.PatientName, out var originalName);

        var anonymizer = new DicomAnonymizer();
        var anonymized = anonymizer.Anonymize(file.Dataset);

        var anonymizedPixels = DicomPixelData.Create(anonymized, false).GetFrame(0).Data;
        anonymized.TryGetString(DicomTag.PatientName, out var anonymizedName);
        var anonymizedUid = anonymized.GetSingleValue<string>(DicomTag.SOPInstanceUID);

        Assert.NotEqual(originalUid, anonymizedUid);
        Assert.NotEqual(originalName, anonymizedName);
        Assert.Equal(originalPixels, anonymizedPixels);
    }
}
