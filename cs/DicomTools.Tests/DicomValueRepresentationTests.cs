using System.IO;
using FellowOakDicom;
using FellowOakDicom.IO.Buffer;

namespace DicomTools.Tests;

public class DicomValueRepresentationTests
{
    [Fact]
    public void DicomElement_SS_StoresSigned16Bit()
    {
        var dataset = new DicomDataset();
        dataset.Add(DicomTag.TagAngleSecondAxis, (short)-1234);

        var value = dataset.GetSingleValue<short>(DicomTag.TagAngleSecondAxis);
        Assert.Equal(-1234, value);
    }

    [Fact]
    public void DicomElement_US_StoresUnsigned16Bit()
    {
        var dataset = new DicomDataset();
        dataset.Add(DicomTag.Rows, (ushort)512);
        dataset.Add(DicomTag.Columns, (ushort)512);

        Assert.Equal(512, dataset.GetSingleValue<ushort>(DicomTag.Rows));
        Assert.Equal(512, dataset.GetSingleValue<ushort>(DicomTag.Columns));
    }

    [Fact]
    public void DicomElement_SL_StoresSigned32Bit()
    {
        var dataset = new DicomDataset();
        dataset.Add(DicomTag.ReferencePixelX0, -100000);

        var value = dataset.GetSingleValue<int>(DicomTag.ReferencePixelX0);
        Assert.Equal(-100000, value);
    }

    [Fact]
    public void DicomElement_UL_StoresUnsigned32Bit()
    {
        var dataset = new DicomDataset();
        dataset.Add(DicomTag.SimpleFrameList, (uint)4000000000);

        var value = dataset.GetSingleValue<uint>(DicomTag.SimpleFrameList);
        Assert.Equal(4000000000u, value);
    }

    [Fact]
    public void DicomElement_FL_StoresFloat32()
    {
        var dataset = new DicomDataset();
        dataset.Add(DicomTag.WindowCenter, 40.5f);
        dataset.Add(DicomTag.WindowWidth, 400.25f);

        Assert.Equal(40.5f, dataset.GetSingleValue<float>(DicomTag.WindowCenter), 0.01f);
        Assert.Equal(400.25f, dataset.GetSingleValue<float>(DicomTag.WindowWidth), 0.01f);
    }

    [Fact]
    public void DicomElement_FD_StoresFloat64()
    {
        var dataset = new DicomDataset();
        dataset.Add(DicomTag.RescaleSlope, 1.23456789012345);

        var value = dataset.GetSingleValue<double>(DicomTag.RescaleSlope);
        Assert.Equal(1.23456789012345, value, 10);
    }

    [Fact]
    public void DicomElement_DS_StoresDecimalString()
    {
        var dataset = new DicomDataset();
        dataset.Add(DicomTag.SliceThickness, "2.5");

        var stringValue = dataset.GetSingleValue<string>(DicomTag.SliceThickness);
        Assert.Equal("2.5", stringValue.Trim());

        var decimalValue = dataset.GetSingleValue<decimal>(DicomTag.SliceThickness);
        Assert.Equal(2.5m, decimalValue);
    }

    [Fact]
    public void DicomElement_IS_StoresIntegerString()
    {
        var dataset = new DicomDataset();
        dataset.Add(DicomTag.InstanceNumber, "42");

        var stringValue = dataset.GetSingleValue<string>(DicomTag.InstanceNumber);
        Assert.Equal("42", stringValue.Trim());

        var intValue = dataset.GetSingleValue<int>(DicomTag.InstanceNumber);
        Assert.Equal(42, intValue);
    }

    [Fact]
    public void DicomElement_LO_StoresLongString()
    {
        var dataset = new DicomDataset();
        var longString = new string('X', 64);
        dataset.Add(DicomTag.Manufacturer, longString);

        var value = dataset.GetSingleValue<string>(DicomTag.Manufacturer);
        Assert.Equal(64, value.Length);
    }

    [Fact]
    public void DicomElement_SH_StoresShortString()
    {
        var dataset = new DicomDataset();
        dataset.Add(DicomTag.AccessionNumber, "ACC123456");

        var value = dataset.GetSingleValue<string>(DicomTag.AccessionNumber);
        Assert.Equal("ACC123456", value);
    }

    [Fact]
    public void DicomElement_PN_StoresPersonName()
    {
        var dataset = new DicomDataset();
        dataset.Add(DicomTag.PatientName, "Doe^John^Middle^Dr^Jr");

        var value = dataset.GetSingleValue<string>(DicomTag.PatientName);
        Assert.Equal("Doe^John^Middle^Dr^Jr", value);
    }

    [Fact]
    public void DicomElement_CS_StoresCodeString()
    {
        var dataset = new DicomDataset();
        dataset.Add(DicomTag.Modality, "CT");
        dataset.Add(DicomTag.PatientSex, "M");

        Assert.Equal("CT", dataset.GetSingleValue<string>(DicomTag.Modality));
        Assert.Equal("M", dataset.GetSingleValue<string>(DicomTag.PatientSex));
    }

    [Fact]
    public void DicomElement_AE_StoresApplicationEntity()
    {
        var dataset = new DicomDataset();
        dataset.Add(DicomTag.SourceApplicationEntityTitle, "MY_AE_TITLE");

        var value = dataset.GetSingleValue<string>(DicomTag.SourceApplicationEntityTitle);
        Assert.Equal("MY_AE_TITLE", value.Trim());
    }

    [Fact]
    public void DicomElement_OB_StoresByteArray()
    {
        var dataset = new DicomDataset();
        var bytes = new byte[] { 0x01, 0x02, 0x03, 0x04, 0x05 };
        dataset.Add(new DicomOtherByte(DicomTag.EncapsulatedDocument, bytes));

        var element = dataset.GetDicomItem<DicomOtherByte>(DicomTag.EncapsulatedDocument);
        Assert.Equal(bytes, element.Get<byte[]>());
    }

    [Fact]
    public void DicomElement_OW_StoresWordArray()
    {
        var dataset = new DicomDataset();
        var words = new ushort[] { 0x1234, 0x5678, 0x9ABC };
        var bytes = new byte[words.Length * 2];
        Buffer.BlockCopy(words, 0, bytes, 0, bytes.Length);

        dataset.Add(new DicomOtherWord(DicomTag.RedPaletteColorLookupTableData, new MemoryByteBuffer(bytes)));

        var element = dataset.GetDicomItem<DicomOtherWord>(DicomTag.RedPaletteColorLookupTableData);
        var retrieved = element.Get<byte[]>();
        Assert.Equal(bytes, retrieved);
    }

    [Fact]
    public void DicomElement_MultiValue_US_StoresArray()
    {
        var dataset = new DicomDataset();
        dataset.Add(DicomTag.PixelAspectRatio, (ushort)1, (ushort)1);

        var values = dataset.GetValues<ushort>(DicomTag.PixelAspectRatio);
        Assert.Equal(2, values.Length);
        Assert.Equal(1, values[0]);
        Assert.Equal(1, values[1]);
    }

    [Fact]
    public void DicomElement_MultiValue_DS_StoresArray()
    {
        var dataset = new DicomDataset();
        dataset.Add(DicomTag.ImagePositionPatient, "0.0", "0.0", "0.0");

        var values = dataset.GetValues<decimal>(DicomTag.ImagePositionPatient);
        Assert.Equal(3, values.Length);
        Assert.All(values, v => Assert.Equal(0.0m, v));
    }

    [Fact]
    public void DicomElement_MultiValue_FD_StoresArray()
    {
        var dataset = new DicomDataset();
        dataset.Add(DicomTag.ImageOrientationPatient, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0);

        var values = dataset.GetValues<double>(DicomTag.ImageOrientationPatient);
        Assert.Equal(6, values.Length);
        Assert.Equal(1.0, values[0]);
        Assert.Equal(0.0, values[1]);
        Assert.Equal(0.0, values[2]);
        Assert.Equal(0.0, values[3]);
        Assert.Equal(1.0, values[4]);
        Assert.Equal(0.0, values[5]);
    }

    [Fact]
    public void DicomDataset_Clone_CopiesAllElements()
    {
        var original = new DicomDataset
        {
            { DicomTag.PatientName, "Original^Patient" },
            { DicomTag.PatientID, "ORIG-001" },
            { DicomTag.Rows, (ushort)256 },
            { DicomTag.Columns, (ushort)256 }
        };

        var cloned = original.Clone();
        cloned.AddOrUpdate(DicomTag.PatientName, "Cloned^Patient");

        Assert.Equal("Original^Patient", original.GetSingleValue<string>(DicomTag.PatientName));
        Assert.Equal("Cloned^Patient", cloned.GetSingleValue<string>(DicomTag.PatientName));
        Assert.Equal(original.GetSingleValue<ushort>(DicomTag.Rows), cloned.GetSingleValue<ushort>(DicomTag.Rows));
    }

    [Fact]
    public void DicomDataset_Remove_DeletesElement()
    {
        var dataset = new DicomDataset
        {
            { DicomTag.PatientName, "Test^Person" },
            { DicomTag.PatientID, "TEST-001" }
        };

        Assert.True(dataset.Contains(DicomTag.PatientName));
        dataset.Remove(DicomTag.PatientName);
        Assert.False(dataset.Contains(DicomTag.PatientName));
        Assert.True(dataset.Contains(DicomTag.PatientID));
    }

    [Fact]
    public void DicomDataset_AddOrUpdate_UpdatesExisting()
    {
        var dataset = new DicomDataset
        {
            { DicomTag.PatientName, "Original^Name" }
        };

        dataset.AddOrUpdate(DicomTag.PatientName, "Updated^Name");

        Assert.Equal("Updated^Name", dataset.GetSingleValue<string>(DicomTag.PatientName));
    }

    [Fact]
    public void DicomDataset_SaveAndReload_PreservesAllVRs()
    {
        var dataset = new DicomDataset(DicomTransferSyntax.ExplicitVRLittleEndian)
        {
            { DicomTag.PatientName, "VR^Test" },
            { DicomTag.PatientID, "VR-001" },
            { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage },
            { DicomTag.Rows, (ushort)64 },
            { DicomTag.Columns, (ushort)64 },
            { DicomTag.InstanceNumber, "1" },
            { DicomTag.SliceThickness, "5.0" },
            { DicomTag.ImagePositionPatient, "0.0", "0.0", "0.0" }
        };

        using var memory = new MemoryStream();
        new DicomFile(dataset).Save(memory);
        memory.Position = 0;

        var reloaded = DicomFile.Open(memory);

        Assert.Equal("VR^Test", reloaded.Dataset.GetSingleValue<string>(DicomTag.PatientName));
        Assert.Equal(64, reloaded.Dataset.GetSingleValue<ushort>(DicomTag.Rows));
        Assert.Equal(1, reloaded.Dataset.GetSingleValue<int>(DicomTag.InstanceNumber));
        Assert.Equal(5.0m, reloaded.Dataset.GetSingleValue<decimal>(DicomTag.SliceThickness));

        var position = reloaded.Dataset.GetValues<decimal>(DicomTag.ImagePositionPatient);
        Assert.Equal(3, position.Length);
    }
}
