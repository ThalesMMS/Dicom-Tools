using System;
using System.IO;
using System.Linq;
using FellowOakDicom;
using FellowOakDicom.Imaging;
using FellowOakDicom.IO.Buffer;

namespace DicomTools.Tests;

public class ApiUsageTests
{
    [Fact]
    public void DicomFile_Open_LoadsMetaAndDataset()
    {
        var file = DicomFile.Open(SampleSeriesHelper.GetFirstFilePath());

        Assert.NotNull(file.FileMetaInfo.TransferSyntax);
        Assert.True(file.Dataset.Contains(DicomTag.StudyInstanceUID));
        Assert.True(file.Dataset.Contains(DicomTag.PixelData));
        Assert.False(string.IsNullOrWhiteSpace(file.Dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID)));
    }

    [Fact]
    public void DicomDataset_GetAndAddOrUpdate_PersistsOnSave()
    {
        var original = DicomFile.Open(SampleSeriesHelper.GetFirstFilePath());
        var dataset = original.Dataset.Clone();
        var newPatientId = $"PAT-{Guid.NewGuid():N}";

        Assert.True(dataset.TryGetString(DicomTag.PatientName, out var patientName));
        Assert.False(string.IsNullOrWhiteSpace(patientName));

        dataset.AddOrUpdate(DicomTag.PatientID, newPatientId);

        using var memory = new MemoryStream();
        new DicomFile(dataset).Save(memory);
        memory.Position = 0;

        var reloaded = DicomFile.Open(memory);
        Assert.Equal(newPatientId, reloaded.Dataset.GetSingleValue<string>(DicomTag.PatientID));
        Assert.Equal(dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID), reloaded.Dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID));
        Assert.True(reloaded.Dataset.Contains(DicomTag.PixelData));
    }

    [Fact]
    public void DicomImage_RenderImage_ProducesPixels()
    {
        var file = DicomFile.Open(SampleSeriesHelper.GetFirstFilePath());
        var dicomImage = new DicomImage(file.Dataset)
        {
            WindowCenter = 40,
            WindowWidth = 400
        };

        var rendered = dicomImage.RenderImage(0);
        Assert.NotNull(rendered);
        Assert.NotNull(rendered.Pixels);
    }

    [Fact]
    public void DicomPixelData_GetFrame_ReturnsRawBuffer()
    {
        var file = DicomFile.Open(SampleSeriesHelper.GetFirstFilePath());
        var pixelData = DicomPixelData.Create(file.Dataset, false);

        var frame = pixelData.GetFrame(0);
        Assert.True(frame.Data.Length > 0);

        var expectedLength = pixelData.Width * pixelData.Height * (pixelData.BitsAllocated / 8);
        Assert.True(frame.Data.Length >= expectedLength);
    }

    [Fact]
    public void DicomPixelData_AddFrame_AllowsCustomDataset()
    {
        var rows = 4;
        var cols = 4;
        var buffer = new byte[rows * cols * 2];
        for (var i = 0; i < rows * cols; i++)
        {
            var value = (ushort)(100 + i);
            var bytes = BitConverter.GetBytes(value);
            Buffer.BlockCopy(bytes, 0, buffer, i * 2, 2);
        }

        var dataset = new DicomDataset(DicomTransferSyntax.ExplicitVRLittleEndian)
        {
            { DicomTag.PatientName, "Pixel^Adder" },
            { DicomTag.PatientID, "ADD-FRAME" },
            { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage },
            { DicomTag.SamplesPerPixel, (ushort)1 },
            { DicomTag.PhotometricInterpretation, PhotometricInterpretation.Monochrome2.Value },
            { DicomTag.Rows, (ushort)rows },
            { DicomTag.Columns, (ushort)cols },
            { DicomTag.BitsAllocated, (ushort)16 },
            { DicomTag.BitsStored, (ushort)16 },
            { DicomTag.HighBit, (ushort)15 },
            { DicomTag.PixelRepresentation, (ushort)0 }
        };

        var pixelData = DicomPixelData.Create(dataset, true);
        pixelData.AddFrame(new MemoryByteBuffer(buffer));

        using var memory = new MemoryStream();
        new DicomFile(dataset).Save(memory);
        memory.Position = 0;

        var reloaded = DicomFile.Open(memory);
        var reloadedPixelData = DicomPixelData.Create(reloaded.Dataset, false);
        var reloadedFrame = reloadedPixelData.GetFrame(0);

        Assert.Equal(buffer.Length, reloadedFrame.Data.Length);
        Assert.Equal(buffer, reloadedFrame.Data);
    }
}
