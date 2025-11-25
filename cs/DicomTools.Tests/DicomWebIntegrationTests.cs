using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;
using FellowOakDicom;
using FellowOakDicom.Network;
using FellowOakDicom.Network.Client;
using Xunit.Sdk;

namespace DicomTools.Tests;

[Collection("Network")]
public class DicomWebIntegrationTests
{
    [Fact]
    public async Task Stow_Then_CMove_DeliversInstance()
    {
        InMemoryStoreScp.Clear();
        InMemoryQueryRetrieveScp.Reset();

        var dicomPath = SampleSeriesHelper.GetFirstFilePath();
        var dicomBytes = await File.ReadAllBytesAsync(dicomPath);
        var dicomFile = DicomFile.Open(dicomPath);
        var studyUid = dicomFile.Dataset.GetSingleValue<string>(DicomTag.StudyInstanceUID);
        var sopUid = dicomFile.Dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID);

        var stowPort = TcpPortHelper.GetFreePort();
        await using (await DicomWebStowServer.StartAsync(stowPort))
        {
            using var http = new HttpClient();
            var content = new ByteArrayContent(dicomBytes);
            content.Headers.ContentType = new MediaTypeHeaderValue("application/dicom");
            var stowResponse = await http.PostAsync($"http://localhost:{stowPort}/dicomweb/stow", content);
            Assert.True(stowResponse.IsSuccessStatusCode, $"STOW failed: {(int)stowResponse.StatusCode}");
        }

        Assert.Equal(1, InMemoryQueryRetrieveScp.GetSourceCount());

        var movePort = TcpPortHelper.GetFreePort();
        var storePort = TcpPortHelper.GetFreePort();
        using var storeServer = DicomServerFactory.Create<InMemoryStoreScp>(storePort);
        using var moveServer = DicomServerFactory.Create<InMemoryQueryRetrieveScp>(movePort);
        InMemoryQueryRetrieveScp.RegisterDestination("DEST-AE", "127.0.0.1", storePort);
        await Task.Delay(100);

        var moveResponses = new List<DicomCMoveResponse>();
        var moveRequest = new DicomCMoveRequest("DEST-AE", studyUid);
        moveRequest.OnResponseReceived += (_, response) => moveResponses.Add(response);

        var client = DicomClientFactory.Create("127.0.0.1", movePort, useTls: false, callingAe: "SCU", calledAe: "QR");
        await client.AddRequestAsync(moveRequest);
        using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(15));
        await client.SendAsync(cts.Token);

        if (moveResponses.Any(r => r.Status == DicomStatus.ProcessingFailure))
        {
            throw new Xunit.Sdk.XunitException(InMemoryQueryRetrieveScp.GetLastMoveError() ?? "C-MOVE processing failure");
        }

        Assert.Contains(moveResponses, r => r.Status == DicomStatus.Pending);
        Assert.Contains(moveResponses, r => r.Status == DicomStatus.Success);

        Assert.Single(InMemoryStoreScp.StoredFiles);
        var stored = InMemoryStoreScp.StoredFiles.Single();
        var storedSopUid = stored.Dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID);
        Assert.Equal(sopUid, storedSopUid);
    }
}
