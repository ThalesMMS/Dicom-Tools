using System;
using System.IO;
using System.Threading.Tasks;
using FellowOakDicom;
using FellowOakDicom.Imaging;
using FellowOakDicom.IO.Buffer;
using FellowOakDicom.Network;
using FellowOakDicom.Network.Client;
using FellowOakDicom.Serialization;

namespace DicomTools.Tests;

public class DicomDatasetTests
{
    [Fact]
    public void SaveAndLoad_DicomFile_PreservesCoreTagsAndPixelData()
    {
        var dataset = DicomTestData.CreateMonochromeImage();
        var originalPixelBytes = DicomPixelData.Create(dataset, false).GetFrame(0).Data;

        using var memory = new MemoryStream();
        new DicomFile(dataset).Save(memory);
        memory.Position = 0;

        var reloaded = DicomFile.Open(memory);
        var reloadedDataset = reloaded.Dataset;

        Assert.Equal(dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID), reloadedDataset.GetSingleValue<string>(DicomTag.SOPInstanceUID));
        Assert.Equal(dataset.GetSingleValue<ushort>(DicomTag.Rows), reloadedDataset.GetSingleValue<ushort>(DicomTag.Rows));
        Assert.Equal(dataset.GetSingleValue<ushort>(DicomTag.Columns), reloadedDataset.GetSingleValue<ushort>(DicomTag.Columns));

        var roundTripPixelBytes = DicomPixelData.Create(reloadedDataset, false).GetFrame(0).Data;
        Assert.Equal(originalPixelBytes, roundTripPixelBytes);
    }

    [Fact]
    public void Anonymizer_RemovesSensitiveInformation()
    {
        var dataset = DicomTestData.CreateMonochromeImage();
        dataset.AddOrUpdate(DicomTag.PatientBirthDate, "19700101");
        dataset.AddOrUpdate(DicomTag.PatientAddress, "123 Fake Street");

        var originalStudyUid = dataset.GetSingleValue<string>(DicomTag.StudyInstanceUID);
        dataset.TryGetString(DicomTag.PatientName, out var originalPatientName);

        var anonymizer = new DicomAnonymizer();
        var anonymized = anonymizer.Anonymize(dataset);

        Assert.True(anonymized.TryGetSingleValue(DicomTag.StudyInstanceUID, out string anonymizedStudyUid));
        Assert.NotEqual(originalStudyUid, anonymizedStudyUid);

        anonymized.TryGetString(DicomTag.PatientName, out var anonymizedPatientName);
        Assert.NotEqual(originalPatientName, anonymizedPatientName);
        Assert.True(anonymized.Contains(DicomTag.PatientName));

        anonymized.TryGetString(DicomTag.PatientBirthDate, out var anonymizedBirthDate);
        anonymized.TryGetString(DicomTag.PatientAddress, out var anonymizedAddress);

        Assert.True(string.IsNullOrWhiteSpace(anonymizedBirthDate) || anonymizedBirthDate != "19700101");
        Assert.True(string.IsNullOrWhiteSpace(anonymizedAddress));
        Assert.All(anonymizer.ReplacedUIDs.Values, value => Assert.False(string.IsNullOrWhiteSpace(value)));
    }

    [Fact]
    public void Json_RoundTrip_PreservesStructure()
    {
        var dataset = DicomTestData.CreateMonochromeImage();

        var json = DicomJson.ConvertDicomToJson(dataset, formatIndented: true);
        var roundTrip = DicomJson.ConvertJsonToDicom(json);

        Assert.Equal(dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID), roundTrip.GetSingleValue<string>(DicomTag.SOPInstanceUID));
        Assert.Equal(dataset.GetSingleValue<ushort>(DicomTag.Rows), roundTrip.GetSingleValue<ushort>(DicomTag.Rows));
        Assert.Equal(dataset.GetSingleValue<ushort>(DicomTag.Columns), roundTrip.GetSingleValue<ushort>(DicomTag.Columns));

        var originalPixelBytes = DicomPixelData.Create(dataset, false).GetFrame(0).Data;
        var roundTripPixelBytes = DicomPixelData.Create(roundTrip, false).GetFrame(0).Data;
        Assert.Equal(originalPixelBytes, roundTripPixelBytes);
    }
}

public class DicomNetworkTests
{
    [Fact]
    public async Task CEcho_RoundTrip_Succeeds()
    {
        var port = TcpPortHelper.GetFreePort();

        using var server = DicomServerFactory.Create<DicomCEchoProvider>(port);
        await Task.Delay(100); // give the listener time to bind

        var client = DicomClientFactory.Create("127.0.0.1", port, useTls: false, callingAe: "SCU", calledAe: "ANY-SCP");
        var echoRequest = new DicomCEchoRequest();

        DicomStatus? responseStatus = null;
        echoRequest.OnResponseReceived += (_, response) => responseStatus = response.Status;

        await client.AddRequestAsync(echoRequest);
        await client.SendAsync();

        Assert.Equal(DicomStatus.Success, responseStatus);
    }
}

internal static class DicomTestData
{
    internal static DicomDataset CreateMonochromeImage(int rows = 2, int columns = 2)
    {
        var dataset = new DicomDataset(DicomTransferSyntax.ExplicitVRLittleEndian)
        {
            { DicomTag.PatientName, "Test^Person" },
            { DicomTag.PatientID, "TEST-123" },
            { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SeriesInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SOPInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.SOPClassUID, DicomUID.SecondaryCaptureImageStorage },
            { DicomTag.Modality, "OT" },
            { DicomTag.SamplesPerPixel, (ushort)1 },
            { DicomTag.PhotometricInterpretation, PhotometricInterpretation.Monochrome2.Value },
            { DicomTag.Rows, (ushort)rows },
            { DicomTag.Columns, (ushort)columns },
            { DicomTag.BitsAllocated, (ushort)16 },
            { DicomTag.BitsStored, (ushort)12 },
            { DicomTag.HighBit, (ushort)11 },
            { DicomTag.PixelRepresentation, (ushort)0 }
        };

        var pixelData = DicomPixelData.Create(dataset, true);
        pixelData.AddFrame(new MemoryByteBuffer(CreatePixelBuffer(rows, columns)));

        return dataset;
    }

    private static byte[] CreatePixelBuffer(int rows, int columns)
    {
        var pixelCount = rows * columns;
        var buffer = new byte[pixelCount * 2];
        for (var i = 0; i < pixelCount; i++)
        {
            var value = (ushort)(1000 + i * 30);
            var bytes = BitConverter.GetBytes(value);
            Buffer.BlockCopy(bytes, 0, buffer, i * 2, 2);
        }

        return buffer;
    }
}
