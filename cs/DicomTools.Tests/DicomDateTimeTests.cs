using System.Globalization;
using FellowOakDicom;

namespace DicomTools.Tests;

public class DicomDateTimeTests
{
    [Fact]
    public void DicomDataset_AddDate_FormatsCorrectly()
    {
        var dataset = new DicomDataset();
        var date = new DateTime(2024, 12, 25);

        dataset.AddOrUpdate(DicomTag.StudyDate, date);

        var rawValue = dataset.GetSingleValue<string>(DicomTag.StudyDate);
        Assert.Equal("20241225", rawValue);
    }

    [Fact]
    public void DicomDataset_GetDateTime_ParsesCorrectly()
    {
        var dataset = new DicomDataset
        {
            { DicomTag.StudyDate, "20240315" },
            { DicomTag.StudyTime, "143022" }
        };

        var date = dataset.GetSingleValue<DateTime>(DicomTag.StudyDate);
        var time = dataset.GetSingleValue<DateTime>(DicomTag.StudyTime);

        Assert.Equal(2024, date.Year);
        Assert.Equal(3, date.Month);
        Assert.Equal(15, date.Day);

        Assert.Equal(14, time.Hour);
        Assert.Equal(30, time.Minute);
        Assert.Equal(22, time.Second);
    }

    [Theory]
    [InlineData("20240101", 2024, 1, 1)]
    [InlineData("19991231", 1999, 12, 31)]
    [InlineData("20001015", 2000, 10, 15)]
    public void DicomDataset_ParseDate_VariousFormats(string dateString, int year, int month, int day)
    {
        var dataset = new DicomDataset
        {
            { DicomTag.PatientBirthDate, dateString }
        };

        var parsed = dataset.GetSingleValue<DateTime>(DicomTag.PatientBirthDate);

        Assert.Equal(year, parsed.Year);
        Assert.Equal(month, parsed.Month);
        Assert.Equal(day, parsed.Day);
    }

    [Theory]
    [InlineData("120000", 12, 0, 0)]
    [InlineData("235959", 23, 59, 59)]
    [InlineData("080530", 8, 5, 30)]
    [InlineData("143022.123", 14, 30, 22)]
    public void DicomDataset_ParseTime_VariousFormats(string timeString, int hour, int minute, int second)
    {
        var dataset = new DicomDataset
        {
            { DicomTag.StudyTime, timeString }
        };

        var parsed = dataset.GetSingleValue<DateTime>(DicomTag.StudyTime);

        Assert.Equal(hour, parsed.Hour);
        Assert.Equal(minute, parsed.Minute);
        Assert.Equal(second, parsed.Second);
    }

    [Fact]
    public void DicomDataset_TimeWithFraction_ParsesCorrectly()
    {
        var dataset = new DicomDataset
        {
            { DicomTag.AcquisitionTime, "143022.123456" }
        };

        var parsed = dataset.GetSingleValue<DateTime>(DicomTag.AcquisitionTime);

        Assert.Equal(14, parsed.Hour);
        Assert.Equal(30, parsed.Minute);
        Assert.Equal(22, parsed.Second);
        Assert.True(parsed.Millisecond >= 123);
    }

    [Fact]
    public void DicomDataset_DateTimeRange_ParsesCorrectly()
    {
        var dataset = new DicomDataset();
        var dateRange = new DicomDateRange(
            new DateTime(2024, 1, 1),
            new DateTime(2024, 12, 31));

        dataset.AddOrUpdate(DicomTag.StudyDate, dateRange);

        var element = dataset.GetDicomItem<DicomElement>(DicomTag.StudyDate);
        var valueString = element.Get<string>();

        Assert.Contains("-", valueString);
    }

    [Fact]
    public void DicomDataset_AgeString_ParsesCorrectly()
    {
        var dataset = new DicomDataset
        {
            { DicomTag.PatientAge, "045Y" }
        };

        var ageString = dataset.GetSingleValue<string>(DicomTag.PatientAge);
        Assert.Equal("045Y", ageString);
    }

    [Theory]
    [InlineData("001D", "001D")]
    [InlineData("006W", "006W")]
    [InlineData("011M", "011M")]
    [InlineData("065Y", "065Y")]
    public void DicomDataset_AgeStringFormats_RoundTrip(string input, string expected)
    {
        var dataset = new DicomDataset
        {
            { DicomTag.PatientAge, input }
        };

        var retrieved = dataset.GetSingleValue<string>(DicomTag.PatientAge);
        Assert.Equal(expected, retrieved);
    }

    [Fact]
    public void DicomDataset_EmptyDate_HandledGracefully()
    {
        var dataset = new DicomDataset
        {
            { DicomTag.StudyDate, string.Empty }
        };

        var success = dataset.TryGetSingleValue(DicomTag.StudyDate, out DateTime _);
        Assert.False(success);
    }

    [Fact]
    public void DicomDataset_DateTimeElement_FullPrecision()
    {
        var dataset = new DicomDataset();
        var dateTime = new DateTime(2024, 6, 15, 14, 30, 22, 500);

        dataset.AddOrUpdate(DicomTag.AcquisitionDateTime, dateTime);

        var retrieved = dataset.GetSingleValue<DateTime>(DicomTag.AcquisitionDateTime);

        Assert.Equal(2024, retrieved.Year);
        Assert.Equal(6, retrieved.Month);
        Assert.Equal(15, retrieved.Day);
        Assert.Equal(14, retrieved.Hour);
        Assert.Equal(30, retrieved.Minute);
        Assert.Equal(22, retrieved.Second);
    }

    [Fact]
    public void DicomDataset_MultipleTimeValues_CanBeRetrieved()
    {
        var dataset = new DicomDataset();
        dataset.Add(new DicomTime(DicomTag.FrameAcquisitionDateTime, "120000", "130000", "140000"));

        var values = dataset.GetValues<DateTime>(DicomTag.FrameAcquisitionDateTime);

        Assert.Equal(3, values.Length);
        Assert.Equal(12, values[0].Hour);
        Assert.Equal(13, values[1].Hour);
        Assert.Equal(14, values[2].Hour);
    }

    [Fact]
    public void DicomDataset_SaveAndReload_PreservesDates()
    {
        var dataset = new DicomDataset(DicomTransferSyntax.ExplicitVRLittleEndian)
        {
            { DicomTag.PatientName, "DateTime^Test" },
            { DicomTag.PatientID, "DT-001" },
            { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage },
            { DicomTag.StudyDate, new DateTime(2024, 7, 20) },
            { DicomTag.StudyTime, new DateTime(1, 1, 1, 15, 45, 30) },
            { DicomTag.PatientBirthDate, new DateTime(1990, 5, 10) }
        };

        using var memory = new MemoryStream();
        new DicomFile(dataset).Save(memory);
        memory.Position = 0;

        var reloaded = DicomFile.Open(memory);

        Assert.Equal("20240720", reloaded.Dataset.GetSingleValue<string>(DicomTag.StudyDate));
        Assert.StartsWith("154530", reloaded.Dataset.GetSingleValue<string>(DicomTag.StudyTime));
        Assert.Equal("19900510", reloaded.Dataset.GetSingleValue<string>(DicomTag.PatientBirthDate));
    }
}
