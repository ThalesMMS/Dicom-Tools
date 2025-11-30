using System.IO;
using System.Text;
using FellowOakDicom;

namespace DicomTools.Tests;

public class DicomCharsetTests
{
    [Fact]
    public void DicomDataset_DefaultCharset_IsISO_IR_6()
    {
        var dataset = new DicomDataset
        {
            { DicomTag.PatientName, "Test^Person" }
        };

        // Default charset is ISO-IR 6 (ASCII) if not specified
        Assert.False(dataset.Contains(DicomTag.SpecificCharacterSet));
    }

    [Fact]
    public void DicomDataset_SpecificCharacterSet_CanBeSet()
    {
        var dataset = new DicomDataset
        {
            { DicomTag.SpecificCharacterSet, "ISO_IR 192" },
            { DicomTag.PatientName, "Test^Person" }
        };

        var charset = dataset.GetSingleValue<string>(DicomTag.SpecificCharacterSet);
        Assert.Equal("ISO_IR 192", charset);
    }

    [Fact]
    public void DicomDataset_UTF8_SupportsSpecialCharacters()
    {
        var dataset = new DicomDataset
        {
            { DicomTag.SpecificCharacterSet, "ISO_IR 192" },
            { DicomTag.PatientName, "Müller^François" }
        };

        var name = dataset.GetSingleValue<string>(DicomTag.PatientName);
        Assert.Contains("ü", name);
        Assert.Contains("ç", name);
    }

    [Fact]
    public void DicomDataset_Latin1_SupportsEuropeanCharacters()
    {
        var dataset = new DicomDataset
        {
            { DicomTag.SpecificCharacterSet, "ISO_IR 100" },
            { DicomTag.PatientName, "Señor^José" }
        };

        var name = dataset.GetSingleValue<string>(DicomTag.PatientName);
        Assert.Contains("ñ", name);
        Assert.Contains("é", name);
    }

    [Fact]
    public void DicomDataset_SaveAndReload_PreservesCharset()
    {
        var dataset = new DicomDataset(DicomTransferSyntax.ExplicitVRLittleEndian)
        {
            { DicomTag.SpecificCharacterSet, "ISO_IR 192" },
            { DicomTag.PatientName, "Tëst^Pérson" },
            { DicomTag.PatientID, "CHARSET-001" },
            { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage }
        };

        using var memory = new MemoryStream();
        new DicomFile(dataset).Save(memory);
        memory.Position = 0;

        var reloaded = DicomFile.Open(memory);

        Assert.Equal("ISO_IR 192", reloaded.Dataset.GetSingleValue<string>(DicomTag.SpecificCharacterSet));
        var name = reloaded.Dataset.GetSingleValue<string>(DicomTag.PatientName);
        Assert.Contains("ë", name);
        Assert.Contains("é", name);
    }

    [Theory]
    [InlineData("ISO_IR 100", "Latin1")]
    [InlineData("ISO_IR 192", "UTF-8")]
    [InlineData("ISO 2022 IR 6", "ASCII")]
    public void DicomEncoding_SupportsCommonCharsets(string charsetName, string description)
    {
        var dataset = new DicomDataset
        {
            { DicomTag.SpecificCharacterSet, charsetName }
        };

        var charset = dataset.GetSingleValue<string>(DicomTag.SpecificCharacterSet);
        Assert.Equal(charsetName, charset);
        Assert.NotEmpty(description); // Just to use the parameter
    }

    [Fact]
    public void DicomDataset_MultiValueCharset_CanBeSet()
    {
        var dataset = new DicomDataset();
        dataset.Add(DicomTag.SpecificCharacterSet, "ISO 2022 IR 6", "ISO 2022 IR 87");

        var values = dataset.GetValues<string>(DicomTag.SpecificCharacterSet);
        Assert.Equal(2, values.Length);
        Assert.Equal("ISO 2022 IR 6", values[0]);
        Assert.Equal("ISO 2022 IR 87", values[1]);
    }

    [Fact]
    public void DicomDataset_PersonName_HandlesComponents()
    {
        var dataset = new DicomDataset
        {
            { DicomTag.SpecificCharacterSet, "ISO_IR 192" },
            { DicomTag.PatientName, "Family^Given^Middle^Prefix^Suffix" }
        };

        var name = dataset.GetSingleValue<string>(DicomTag.PatientName);
        var parts = name.Split('^');

        Assert.Equal(5, parts.Length);
        Assert.Equal("Family", parts[0]);
        Assert.Equal("Given", parts[1]);
        Assert.Equal("Middle", parts[2]);
        Assert.Equal("Prefix", parts[3]);
        Assert.Equal("Suffix", parts[4]);
    }

    [Fact]
    public void DicomDataset_LongText_PreservesEncoding()
    {
        var longText = "This is a longer text with special characters: äöü ñ é ç. " +
                       "It should be preserved correctly when saving and reloading.";

        var dataset = new DicomDataset(DicomTransferSyntax.ExplicitVRLittleEndian)
        {
            { DicomTag.SpecificCharacterSet, "ISO_IR 192" },
            { DicomTag.PatientName, "Test^Person" },
            { DicomTag.PatientID, "LT-001" },
            { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage },
            { DicomTag.StudyDescription, longText }
        };

        using var memory = new MemoryStream();
        new DicomFile(dataset).Save(memory);
        memory.Position = 0;

        var reloaded = DicomFile.Open(memory);
        var retrievedText = reloaded.Dataset.GetSingleValue<string>(DicomTag.StudyDescription);

        Assert.Equal(longText, retrievedText);
    }

    [Fact]
    public void DicomDataset_EmptyStringValue_IsHandled()
    {
        var dataset = new DicomDataset
        {
            { DicomTag.PatientName, string.Empty }
        };

        Assert.True(dataset.Contains(DicomTag.PatientName));
        var success = dataset.TryGetSingleValue(DicomTag.PatientName, out string value);
        Assert.True(success);
        Assert.Equal(string.Empty, value);
    }

    [Fact]
    public void DicomDataset_NullPaddedString_IsTrimmed()
    {
        var dataset = new DicomDataset
        {
            { DicomTag.PatientID, "PATIENT001\0" }
        };

        var patientId = dataset.GetSingleValue<string>(DicomTag.PatientID);
        Assert.DoesNotContain("\0", patientId);
    }
}
