using FellowOakDicom;
using FellowOakDicom.Imaging;
using FellowOakDicom.IO;

namespace DicomTools.Cli;

internal static class PixelDataHelpers
{
    internal static PixelSeries ExtractPixelValues(string path, int frameIndex)
    {
        var dataset = DicomFile.Open(path).Dataset;
        var pixelData = DicomPixelData.Create(dataset, false);
        if (pixelData.NumberOfFrames == 0)
        {
            throw new InvalidOperationException("dataset does not contain frames");
        }

        if (frameIndex < 0 || frameIndex >= pixelData.NumberOfFrames)
        {
            frameIndex = 0;
        }

        var buffer = pixelData.GetFrame(frameIndex);
        var bytes = buffer.Data;
        var bytesPerSample = pixelData.BitsAllocated / 8;
        if (bytesPerSample <= 0)
        {
            throw new InvalidOperationException($"unsupported BitsAllocated={pixelData.BitsAllocated}");
        }

        var sampleCount = bytes.Length / bytesPerSample;
        var values = new double[sampleCount];
        var signed = pixelData.PixelRepresentation == PixelRepresentation.Signed;
        var littleEndian = dataset.InternalTransferSyntax.Endian == Endian.Little;

        for (var i = 0; i < sampleCount; i++)
        {
            var offset = i * bytesPerSample;
            values[i] = pixelData.BitsAllocated switch
            {
                8 => signed ? (sbyte)bytes[offset] : bytes[offset],
                16 => littleEndian
                    ? signed ? BitConverter.ToInt16(bytes, offset) : BitConverter.ToUInt16(bytes, offset)
                    : signed ? BitConverter.ToInt16(new[] { bytes[offset + 1], bytes[offset] }, 0) : BitConverter.ToUInt16(new[] { bytes[offset + 1], bytes[offset] }, 0),
                32 => littleEndian
                    ? signed ? BitConverter.ToInt32(bytes, offset) : BitConverter.ToUInt32(bytes, offset)
                    : signed ? BitConverter.ToInt32(new[] { bytes[offset + 3], bytes[offset + 2], bytes[offset + 1], bytes[offset] }, 0) : BitConverter.ToUInt32(new[] { bytes[offset + 3], bytes[offset + 2], bytes[offset + 1], bytes[offset] }, 0),
                _ => throw new NotSupportedException($"unsupported BitsAllocated={pixelData.BitsAllocated}")
            };
        }

        return new PixelSeries(pixelData.Width, pixelData.Height, pixelData.NumberOfFrames, frameIndex, values);
    }

    internal static (string Host, int Port) ParseHostPort(string target)
    {
        var parts = target.Split(':', 2);
        if (parts.Length != 2 || !int.TryParse(parts[1], out var port))
        {
            throw new ArgumentException("echo target must be in form host:port");
        }

        return (parts[0], port);
    }
}
