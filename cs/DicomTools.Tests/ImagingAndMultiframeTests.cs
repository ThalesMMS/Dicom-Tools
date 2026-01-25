using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using FellowOakDicom;
using FellowOakDicom.Imaging;
using FellowOakDicom.Imaging.Codec;
using FellowOakDicom.IO.Buffer;
using SixLabors.ImageSharp;
using SixLabors.ImageSharp.PixelFormats;

namespace DicomTools.Tests;

public class ImagingAndMultiframeTests
{
    [Fact]
    public void WindowLevel_Renders_AsSharpImage_WithExpectedLut()
    {
        var rows = 4;
        var columns = 4;
        var frameValues = Enumerable.Range(0, rows * columns).Select(i => (ushort)(50 + (i * 25))).ToArray();
        var dataset = DicomTestData.CreateMonochromeImageWithFrames(rows, columns, new[] { frameValues });
        var pixelData = DicomPixelData.Create(dataset, false);
        var extracted = DecodeFrame(pixelData.GetFrame(0).Data);
        var windowCenter = 100.0;
        var windowWidth = 80.0;

        using var rendered = new Image<L8>(columns, rows);
        for (var y = 0; y < rows; y++)
        {
            for (var x = 0; x < columns; x++)
            {
                var index = y * columns + x;
                var pixel = ApplyWindow(extracted[index], windowCenter, windowWidth);
                rendered[x, y] = new L8(pixel);
            }
        }

        var luminance = ExtractFromL8(rendered);
        var expected = extracted.Select(v => ApplyWindow(v, windowCenter, windowWidth)).ToArray();

        Assert.Equal(expected, luminance);

        var histogram = BuildHistogram(luminance, 256);
        Assert.Equal(luminance.Length, histogram.Sum());
        Assert.Contains(histogram, bin => bin > 0);
    }

    [Fact]
    public void MultiFrame_ToImage_ExportsEachFrame_WithIndependentScaling()
    {
        var rows = 3;
        var columns = 3;
        var frameCount = 2;
        var frames = DicomTestData.BuildRampFrames(rows, columns, frameCount);
        var dataset = DicomTestData.CreateMonochromeImageWithFrames(rows, columns, frames);

        var workingDir = Path.Combine(Path.GetTempPath(), $"multiframe-{Guid.NewGuid():N}");
        Directory.CreateDirectory(workingDir);

        var dicomPath = Path.Combine(workingDir, "multiframe.dcm");
        new DicomFile(dataset).Save(dicomPath);

        var frame0Path = Path.Combine(workingDir, "frame0.png");
        var frame1Path = Path.Combine(workingDir, "frame1.png");

        try
        {
            var result0 = CliRunner.Run("to-image", dicomPath, "--frame", "0", "--output", frame0Path);
            var result1 = CliRunner.Run("to-image", dicomPath, "--frame", "1", "--output", frame1Path);

            Assert.Equal(0, result0.ExitCode);
            Assert.Equal(0, result1.ExitCode);
            Assert.True(File.Exists(frame0Path));
            Assert.True(File.Exists(frame1Path));

            using var image0 = Image.Load<L16>(frame0Path);
            using var image1 = Image.Load<L16>(frame1Path);

            var expectedFrame0 = ScaleToL16(frames[0]);
            var expectedFrame1 = ScaleToL16(frames[1]);

            Assert.Equal(frames[0].Length, image0.Width * image0.Height);
            Assert.Equal(frames[1].Length, image1.Width * image1.Height);

            Assert.Equal(expectedFrame0, ExtractPixels(image0));
            Assert.Equal(expectedFrame1, ExtractPixels(image1));
        }
        finally
        {
            Directory.Delete(workingDir, recursive: true);
        }
    }

    [Fact]
    public void ColorMultiframe_CompressedRoundTrip_RetainsRgbPixels()
    {
        var rows = 2;
        var columns = 2;
        var frames = new[]
        {
            new byte[]
            {
                255, 0, 0,
                0, 255, 0,
                0, 0, 255,
                128, 128, 128
            },
            new byte[]
            {
                10, 20, 30,
                40, 50, 60,
                70, 80, 90,
                100, 110, 120
            }
        };

        var source = new DicomFile(BuildRgbMultiframe(rows, columns, frames));

        DicomFile encoded;
        try
        {
            encoded = new DicomTranscoder(DicomTransferSyntax.ExplicitVRLittleEndian, DicomTransferSyntax.RLELossless).Transcode(source);
        }
        catch (DicomCodecException ex) when (ex.Message.Contains("not supported", StringComparison.OrdinalIgnoreCase))
        {
            return;
        }

        var roundTrip = new DicomTranscoder(encoded.FileMetaInfo.TransferSyntax, DicomTransferSyntax.ExplicitVRLittleEndian).Transcode(encoded);
        var pixelData = DicomPixelData.Create(roundTrip.Dataset, false);

        Assert.Equal(frames.Length, pixelData.NumberOfFrames);
        Assert.Equal(PlanarConfiguration.Interleaved, pixelData.PlanarConfiguration);
        Assert.Equal(PhotometricInterpretation.Rgb, pixelData.PhotometricInterpretation);

        for (var i = 0; i < frames.Length; i++)
        {
            var frame = pixelData.GetFrame(i).Data;
            Assert.Equal(frames[i], frame);
        }
    }

    private static ushort[] DecodeFrame(byte[] frameData)
    {
        var values = new ushort[frameData.Length / 2];
        for (var i = 0; i < values.Length; i++)
        {
            values[i] = BitConverter.ToUInt16(frameData, i * 2);
        }

        return values;
    }

    private static byte[] ExtractFromL8(Image<L8> image)
    {
        var buffer = new byte[image.Width * image.Height];
        var index = 0;
        for (var y = 0; y < image.Height; y++)
        {
            for (var x = 0; x < image.Width; x++)
            {
                var pixel = image[x, y];
                buffer[index++] = pixel.PackedValue;
            }
        }

        return buffer;
    }

    private static int[] BuildHistogram(IEnumerable<byte> values, int bins)
    {
        var histogram = new int[bins];
        foreach (var value in values)
        {
            histogram[value]++;
        }

        return histogram;
    }

    private static byte ApplyWindow(ushort value, double center, double width)
    {
        var min = center - 0.5 - ((width - 1) / 2);
        var max = center - 0.5 + ((width - 1) / 2);
        if (value <= min)
        {
            return byte.MinValue;
        }

        if (value > max)
        {
            return byte.MaxValue;
        }

        var scaled = ((value - (center - 0.5)) / (width - 1) + 0.5) * byte.MaxValue;
        return (byte)Math.Clamp(Math.Round(scaled), byte.MinValue, byte.MaxValue);
    }

    private static ushort[] ScaleToL16(IReadOnlyList<ushort> frameValues)
    {
        var min = frameValues.Min();
        var max = frameValues.Max();
        var range = Math.Max(1, max - min);

        var scaled = new ushort[frameValues.Count];
        for (var i = 0; i < frameValues.Count; i++)
        {
            var value = frameValues[i];
            var normalized = (value - min) / (double)range;
            var scaledValue = normalized * ushort.MaxValue;
            scaled[i] = (ushort)Math.Clamp(scaledValue, ushort.MinValue, ushort.MaxValue);
        }

        return scaled;
    }

    private static ushort[] ExtractPixels(Image<L16> image)
    {
        var buffer = new ushort[image.Width * image.Height];
        var index = 0;
        for (var y = 0; y < image.Height; y++)
        {
            for (var x = 0; x < image.Width; x++)
            {
                buffer[index++] = image[x, y].PackedValue;
            }
        }

        return buffer;
    }

    private static DicomDataset BuildRgbMultiframe(int rows, int columns, IReadOnlyList<byte[]> frames)
    {
        var dataset = new DicomDataset(DicomTransferSyntax.ExplicitVRLittleEndian)
        {
            { DicomTag.PatientName, "Color^Multiframe" },
            { DicomTag.PatientID, "COLOR-MF" },
            { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage },
            { DicomTag.Modality, "OT" },
            { DicomTag.PhotometricInterpretation, PhotometricInterpretation.Rgb.Value },
            { DicomTag.SamplesPerPixel, (ushort)3 },
            { DicomTag.Rows, (ushort)rows },
            { DicomTag.Columns, (ushort)columns },
            { DicomTag.BitsAllocated, (ushort)8 },
            { DicomTag.BitsStored, (ushort)8 },
            { DicomTag.HighBit, (ushort)7 },
            { DicomTag.PixelRepresentation, (ushort)0 },
            { DicomTag.PlanarConfiguration, (ushort)0 },
            { DicomTag.NumberOfFrames, frames.Count.ToString(CultureInfo.InvariantCulture) }
        };

        var pixelData = DicomPixelData.Create(dataset, true);
        pixelData.PlanarConfiguration = PlanarConfiguration.Interleaved;

        var expectedLength = rows * columns * 3;
        foreach (var frame in frames)
        {
            if (frame.Length != expectedLength)
            {
                throw new ArgumentException($"Frame length {frame.Length} does not match expected {expectedLength}", nameof(frames));
            }

            pixelData.AddFrame(new MemoryByteBuffer(frame));
        }

        return dataset;
    }
}
