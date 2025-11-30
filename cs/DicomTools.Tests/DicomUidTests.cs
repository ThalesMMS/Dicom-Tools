using FellowOakDicom;

namespace DicomTools.Tests;

public class DicomUidTests
{
    [Fact]
    public void DicomUIDGenerator_GenerateDerivedFromUUID_ReturnsValidUid()
    {
        var uid = DicomUIDGenerator.GenerateDerivedFromUUID();

        Assert.NotNull(uid);
        Assert.True(uid.UID.Length <= 64);
        Assert.StartsWith("2.25.", uid.UID);
        Assert.DoesNotContain(" ", uid.UID);
    }

    [Fact]
    public void DicomUIDGenerator_GeneratesUniqueUids()
    {
        var uids = Enumerable.Range(0, 100)
            .Select(_ => DicomUIDGenerator.GenerateDerivedFromUUID().UID)
            .ToList();

        Assert.Equal(100, uids.Distinct().Count());
    }

    [Fact]
    public void DicomUID_WellKnown_HasCorrectProperties()
    {
        Assert.Equal("1.2.840.10008.1.1", DicomUID.Verification.UID);
        Assert.Contains("Verification", DicomUID.Verification.Name);
        Assert.Equal(DicomUidType.SOPClass, DicomUID.Verification.Type);
    }

    [Fact]
    public void DicomUID_WellKnownStorage_HasCorrectProperties()
    {
        Assert.Equal("1.2.840.10008.5.1.4.1.1.2", DicomUID.CTImageStorage.UID);
        Assert.Equal("CT Image Storage", DicomUID.CTImageStorage.Name);
        Assert.Equal(DicomUidType.SOPClass, DicomUID.CTImageStorage.Type);

        Assert.Equal("1.2.840.10008.5.1.4.1.1.4", DicomUID.MRImageStorage.UID);
        Assert.Equal("MR Image Storage", DicomUID.MRImageStorage.Name);

        Assert.Equal("1.2.840.10008.5.1.4.1.1.7", DicomUID.SecondaryCaptureImageStorage.UID);
        Assert.Equal("Secondary Capture Image Storage", DicomUID.SecondaryCaptureImageStorage.Name);
    }

    [Fact]
    public void DicomUID_TransferSyntax_HasCorrectType()
    {
        var explicitLE = DicomTransferSyntax.ExplicitVRLittleEndian.UID;
        var implicitLE = DicomTransferSyntax.ImplicitVRLittleEndian.UID;

        Assert.Equal(DicomUidType.TransferSyntax, explicitLE.Type);
        Assert.Equal(DicomUidType.TransferSyntax, implicitLE.Type);
    }

    [Fact]
    public void DicomUID_Custom_CanBeCreated()
    {
        var customUid = new DicomUID("1.2.3.4.5.6.7.8.9", "Custom UID", DicomUidType.Unknown);

        Assert.Equal("1.2.3.4.5.6.7.8.9", customUid.UID);
        Assert.Equal("Custom UID", customUid.Name);
        Assert.Equal(DicomUidType.Unknown, customUid.Type);
    }

    [Fact]
    public void DicomUID_Equality_WorksCorrectly()
    {
        var uid1 = DicomUID.CTImageStorage;
        var uid2 = new DicomUID("1.2.840.10008.5.1.4.1.1.2", "CT Image Storage", DicomUidType.SOPClass);

        Assert.Equal(uid1.UID, uid2.UID);
    }

    [Fact]
    public void DicomUID_ToString_ReturnsUidString()
    {
        var uid = DicomUID.CTImageStorage;
        var text = uid.ToString();
        Assert.Contains(uid.UID, text);
    }

    [Fact]
    public void DicomUID_IsValid_ChecksFormat()
    {
        Assert.True(DicomUID.IsValidUid("1.2.3.4.5"));
        Assert.True(DicomUID.IsValidUid("2.25.123456789"));
        Assert.True(DicomUID.IsValidUid("1.2.840.10008.1.1"));
    }

    [Fact]
    public void DicomUID_StorageClasses_AreSOPClassType()
    {
        Assert.Equal(DicomUidType.SOPClass, DicomUID.CTImageStorage.Type);
        Assert.Equal(DicomUidType.SOPClass, DicomUID.MRImageStorage.Type);
        Assert.Equal(DicomUidType.SOPClass, DicomUID.SecondaryCaptureImageStorage.Type);
        Assert.Equal(DicomUidType.SOPClass, DicomUID.BasicTextSRStorage.Type);
    }

    [Fact]
    public void DicomUID_SOPClassUIDs_CommonModalities()
    {
        Assert.NotNull(DicomUID.CTImageStorage);
        Assert.NotNull(DicomUID.MRImageStorage);
        Assert.NotNull(DicomUID.UltrasoundImageStorage);
        Assert.NotNull(DicomUID.DigitalXRayImageStorageForPresentation);
        Assert.NotNull(DicomUID.SecondaryCaptureImageStorage);
    }

    [Fact]
    public void DicomDataset_GetUid_ReturnsCorrectValue()
    {
        var dataset = new DicomDataset
        {
            { DicomTag.SOPClassUID, DicomUID.CTImageStorage },
            { DicomTag.SOPInstanceUID, "1.2.3.4.5.6.7.8.9" }
        };

        Assert.Equal(DicomUID.CTImageStorage.UID, dataset.GetSingleValue<string>(DicomTag.SOPClassUID));
        Assert.Equal("1.2.3.4.5.6.7.8.9", dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID));
    }

    [Fact]
    public void DicomDataset_AddUid_AcceptsMultipleFormats()
    {
        var dataset = new DicomDataset();

        // Add as DicomUID
        dataset.AddOrUpdate(DicomTag.SOPClassUID, DicomUID.CTImageStorage);
        Assert.Equal(DicomUID.CTImageStorage.UID, dataset.GetSingleValue<string>(DicomTag.SOPClassUID));

        // Add as string
        dataset.AddOrUpdate(DicomTag.SOPInstanceUID, "1.2.3.4.5");
        Assert.Equal("1.2.3.4.5", dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID));
    }
}
