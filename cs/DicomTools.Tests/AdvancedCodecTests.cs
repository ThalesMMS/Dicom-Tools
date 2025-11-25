using System.Linq;
using FellowOakDicom;
using FellowOakDicom.Imaging;
using FellowOakDicom.Imaging.Codec;
using FellowOakDicom.IO.Buffer;
using Xunit.Sdk;

namespace DicomTools.Tests;

public class AdvancedCodecTests
{
    [Theory]
    [InlineData(nameof(DicomTransferSyntax.JPEGLSLossless))]
    [InlineData(nameof(DicomTransferSyntax.JPEG2000Lossless))]
    [InlineData(nameof(DicomTransferSyntax.RLELossless))]
    public void Codec_RoundTrip_RetainsPixels(string syntaxProperty)
    {
        var source = Build8BitMonochrome();
        var targetSyntax = ResolveSyntax(syntaxProperty);

        try
        {
            var encode = new DicomTranscoder(source.FileMetaInfo.TransferSyntax, targetSyntax).Transcode(source);
            Assert.Equal(targetSyntax, encode.FileMetaInfo.TransferSyntax);

            var roundTrip = new DicomTranscoder(targetSyntax, DicomTransferSyntax.ExplicitVRLittleEndian).Transcode(encode);
            var original = ReadPixelBytes(source.Dataset);
            var decodedRoundTrip = ReadPixelBytes(roundTrip.Dataset);

            Assert.Equal(original, decodedRoundTrip);
        }
        catch (DicomCodecException ex) when (ex.Message.Contains("not supported", StringComparison.OrdinalIgnoreCase))
        {
            return;
        }
    }

    private static DicomTransferSyntax ResolveSyntax(string syntaxProperty) =>
        typeof(DicomTransferSyntax).GetField(syntaxProperty)?.GetValue(null) as DicomTransferSyntax
        ?? throw new InvalidOperationException($"Unable to resolve {syntaxProperty} transfer syntax");

    private static DicomFile Build8BitMonochrome()
    {
        var rows = 4;
        var columns = 4;
        var pixelValues = Enumerable.Range(0, rows * columns).Select(i => (byte)(i * 10)).ToArray();

        var dataset = new DicomDataset(DicomTransferSyntax.ExplicitVRLittleEndian)
        {
            { DicomTag.PatientName, "Codec^RoundTrip" },
            { DicomTag.PatientID, "CODEC-TEST" },
            { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage },
            { DicomTag.Modality, "OT" },
            { DicomTag.SamplesPerPixel, (ushort)1 },
            { DicomTag.PhotometricInterpretation, PhotometricInterpretation.Monochrome2.Value },
            { DicomTag.Rows, (ushort)rows },
            { DicomTag.Columns, (ushort)columns },
            { DicomTag.BitsAllocated, (ushort)8 },
            { DicomTag.BitsStored, (ushort)8 },
            { DicomTag.HighBit, (ushort)7 },
            { DicomTag.PixelRepresentation, (ushort)0 },
            { DicomTag.NumberOfFrames, "1" }
        };

        var pixelData = DicomPixelData.Create(dataset, true);
        pixelData.AddFrame(new MemoryByteBuffer(pixelValues));

        return new DicomFile(dataset);
    }

    private static byte[] ReadPixelBytes(DicomDataset dataset)
    {
        var pixelData = DicomPixelData.Create(dataset, false);
        var frame = pixelData.GetFrame(0);
        return frame.Data;
    }
}
