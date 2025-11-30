using FellowOakDicom;

namespace DicomTools.Tests;

public class DicomDictionaryTests
{
    [Fact]
    public void DicomTag_PatientName_HasCorrectProperties()
    {
        var entry = DicomDictionary.Default[DicomTag.PatientName];

        Assert.NotNull(entry);
        Assert.Equal("PatientName", entry.Keyword);
        Assert.Equal(DicomVR.PN, entry.ValueRepresentations.First());
        Assert.Equal("Patient's Name", entry.Name);
    }

    [Fact]
    public void DicomTag_PixelData_HasCorrectVR()
    {
        var entry = DicomDictionary.Default[DicomTag.PixelData];

        Assert.NotNull(entry);
        Assert.Equal("PixelData", entry.Keyword);
        Assert.Contains(DicomVR.OW, entry.ValueRepresentations);
    }

    [Fact]
    public void DicomTag_FromKeyword_ResolvesCorrectly()
    {
        var tag = DicomDictionary.Default["PatientID"];

        Assert.Equal(DicomTag.PatientID.Group, tag.Group);
        Assert.Equal(DicomTag.PatientID.Element, tag.Element);
    }

    [Fact]
    public void DicomTag_PrivateCreator_CanBeRegistered()
    {
        var privateCreator = DicomDictionary.Default.GetPrivateCreator("TestOrg");
        var privateTag = new DicomTag(0x0011, 0x1001, privateCreator);

        Assert.Equal(0x0011, privateTag.Group);
        Assert.True(privateTag.IsPrivate);
        Assert.Equal("TestOrg", privateTag.PrivateCreator?.Creator);
    }

    [Theory]
    [InlineData(0x0008, 0x0018, "SOPInstanceUID")]
    [InlineData(0x0010, 0x0020, "PatientID")]
    [InlineData(0x0020, 0x000D, "StudyInstanceUID")]
    [InlineData(0x0020, 0x000E, "SeriesInstanceUID")]
    [InlineData(0x7FE0, 0x0010, "PixelData")]
    public void DicomDictionary_ContainsStandardTags(ushort group, ushort element, string expectedKeyword)
    {
        var tag = new DicomTag(group, element);
        var entry = DicomDictionary.Default[tag];

        Assert.NotNull(entry);
        Assert.Equal(expectedKeyword, entry.Keyword);
    }

    [Fact]
    public void DicomVR_Parse_ReturnsCorrectType()
    {
        Assert.Equal(DicomVR.LO, DicomVR.Parse("LO"));
        Assert.Equal(DicomVR.PN, DicomVR.Parse("PN"));
        Assert.Equal(DicomVR.DA, DicomVR.Parse("DA"));
        Assert.Equal(DicomVR.TM, DicomVR.Parse("TM"));
        Assert.Equal(DicomVR.UI, DicomVR.Parse("UI"));
        Assert.Equal(DicomVR.OB, DicomVR.Parse("OB"));
        Assert.Equal(DicomVR.OW, DicomVR.Parse("OW"));
    }

    [Fact]
    public void DicomVR_StringTypes_HaveCorrectMaxLength()
    {
        Assert.Equal(16u, DicomVR.AE.MaximumLength);
        Assert.Equal(4u, DicomVR.AS.MaximumLength);
        Assert.Equal(8u, DicomVR.DA.MaximumLength);
        Assert.Equal(64u, DicomVR.LO.MaximumLength);
        Assert.True(DicomVR.PN.MaximumLength >= 64u);
        Assert.Equal(16u, DicomVR.SH.MaximumLength);
        Assert.Equal(64u, DicomVR.UI.MaximumLength);
    }

    [Theory]
    [InlineData("AE", true)]
    [InlineData("AS", true)]
    [InlineData("CS", true)]
    [InlineData("DA", true)]
    [InlineData("DS", true)]
    [InlineData("IS", true)]
    [InlineData("LO", true)]
    [InlineData("LT", true)]
    [InlineData("PN", true)]
    [InlineData("SH", true)]
    [InlineData("ST", true)]
    [InlineData("TM", true)]
    [InlineData("UC", true)]
    [InlineData("UI", true)]
    [InlineData("UR", true)]
    [InlineData("UT", true)]
    [InlineData("OB", false)]
    [InlineData("OW", false)]
    [InlineData("SL", false)]
    [InlineData("SS", false)]
    [InlineData("UL", false)]
    [InlineData("US", false)]
    [InlineData("FL", false)]
    [InlineData("FD", false)]
    public void DicomVR_IsString_ReturnsExpectedValue(string vrCode, bool expectedIsString)
    {
        var vr = DicomVR.Parse(vrCode);
        Assert.Equal(expectedIsString, vr.IsString);
    }

    [Fact]
    public void DicomTag_Equality_WorksCorrectly()
    {
        var tag1 = new DicomTag(0x0010, 0x0010);
        var tag2 = DicomTag.PatientName;

        Assert.Equal(tag1, tag2);
        Assert.True(tag1 == tag2);
        Assert.Equal(tag1.GetHashCode(), tag2.GetHashCode());
    }

    [Fact]
    public void DicomTag_ToString_ReturnsFormattedString()
    {
        var tag = DicomTag.PatientName;
        var tagString = tag.ToString();

        Assert.Contains("0010", tagString);
        Assert.Contains("0010", tagString);
    }
}
