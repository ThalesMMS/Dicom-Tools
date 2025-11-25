using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using FellowOakDicom;
using FellowOakDicom.Network;
using FellowOakDicom.Network.Client;

namespace DicomTools.Tests;

[Collection("Network")]
public class QueryRetrieveTests
{
    [Fact]
    public async Task CFind_Study_Series_And_Image_ReturnsMatches()
    {
        CiEnvironment.SkipIfCi("Skipping C-FIND/C-MOVE network tests in CI to avoid socket restrictions");
        var sampleFiles = SampleSeriesHelper.GetSeriesFiles(3).Select(path => DicomFile.Open(path)).ToArray();
        InMemoryQueryRetrieveScp.Reset();
        InMemoryQueryRetrieveScp.ConfigureSources(sampleFiles);

        var port = TcpPortHelper.GetFreePort();
        using var server = DicomServerFactory.Create<InMemoryQueryRetrieveScp>(port);
        await Task.Delay(100);

        var studyUid = sampleFiles[0].Dataset.GetSingleValue<string>(DicomTag.StudyInstanceUID);
        var seriesUid = sampleFiles[0].Dataset.GetSingleValue<string>(DicomTag.SeriesInstanceUID);
        var sopUid = sampleFiles[0].Dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID);

        var client = DicomClientFactory.Create("127.0.0.1", port, useTls: false, callingAe: "SCU", calledAe: "QR-SCP");

        var studyResponses = await SendFindAsync(client, DicomQueryRetrieveLevel.Study, new Dictionary<DicomTag, string>
        {
            { DicomTag.StudyInstanceUID, studyUid }
        });
        Assert.Contains(studyResponses, r => r.Status == DicomStatus.Pending && r.Dataset?.GetSingleValue<string>(DicomTag.StudyInstanceUID) == studyUid);
        Assert.Contains(studyResponses, r => r.Status == DicomStatus.Success);

        var seriesResponses = await SendFindAsync(client, DicomQueryRetrieveLevel.Series, new Dictionary<DicomTag, string>
        {
            { DicomTag.StudyInstanceUID, studyUid },
            { DicomTag.SeriesInstanceUID, seriesUid }
        });
        Assert.Contains(seriesResponses, r => r.Status == DicomStatus.Pending && r.Dataset?.GetSingleValue<string>(DicomTag.SeriesInstanceUID) == seriesUid);
        Assert.Contains(seriesResponses, r => r.Status == DicomStatus.Success);

        var imageResponses = await SendFindAsync(client, DicomQueryRetrieveLevel.Image, new Dictionary<DicomTag, string>
        {
            { DicomTag.StudyInstanceUID, studyUid },
            { DicomTag.SeriesInstanceUID, seriesUid },
            { DicomTag.SOPInstanceUID, sopUid }
        });
        Assert.Contains(imageResponses, r => r.Status == DicomStatus.Pending && r.Dataset?.GetSingleValue<string>(DicomTag.SOPInstanceUID) == sopUid);
        Assert.Contains(imageResponses, r => r.Status == DicomStatus.Success);
    }

    [Fact]
    public async Task CMove_Transfers_All_Matching_Instances_To_Destination()
    {
        CiEnvironment.SkipIfCi("Skipping C-FIND/C-MOVE network tests in CI to avoid socket restrictions");
        var sourceFiles = SampleSeriesHelper.GetSeriesFiles(2).Select(path => DicomFile.Open(path)).ToArray();
        var studyUid = sourceFiles[0].Dataset.GetSingleValue<string>(DicomTag.StudyInstanceUID);

        InMemoryStoreScp.Clear();
        InMemoryQueryRetrieveScp.Reset();
        InMemoryQueryRetrieveScp.ConfigureSources(sourceFiles);

        var movePort = TcpPortHelper.GetFreePort();
        var storePort = TcpPortHelper.GetFreePort();

        using var storeServer = DicomServerFactory.Create<InMemoryStoreScp>(storePort);
        using var moveServer = DicomServerFactory.Create<InMemoryQueryRetrieveScp>(movePort);
        InMemoryQueryRetrieveScp.RegisterDestination("DEST-AE", "127.0.0.1", storePort);
        await Task.Delay(100);

        var responses = new List<DicomCMoveResponse>();
        var moveRequest = new DicomCMoveRequest("DEST-AE", studyUid);
        moveRequest.OnResponseReceived += (_, response) => responses.Add(response);

        var client = DicomClientFactory.Create("127.0.0.1", movePort, useTls: false, callingAe: "SCU", calledAe: "MOVE-SCP");
        await client.AddRequestAsync(moveRequest);
        await client.SendAsync();

        Assert.Contains(responses, r => r.Status == DicomStatus.Pending);
        Assert.Contains(responses, r => r.Status == DicomStatus.Success);
        Assert.Equal(sourceFiles.Length, InMemoryStoreScp.StoredFiles.Count);

        var storedUids = InMemoryStoreScp.StoredFiles
            .Select(f => f.Dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID))
            .ToArray();
        foreach (var file in sourceFiles)
        {
            var sopInstanceUid = file.Dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID);
            Assert.Contains(sopInstanceUid, storedUids);
        }
    }

    private static async Task<IReadOnlyCollection<DicomCFindResponse>> SendFindAsync(IDicomClient client, DicomQueryRetrieveLevel level, Dictionary<DicomTag, string> keys)
    {
        var responses = new List<DicomCFindResponse>();
        var request = new DicomCFindRequest(level);
        foreach (var kvp in keys)
        {
            request.Dataset.AddOrUpdate(kvp.Key, kvp.Value);
        }

        request.OnResponseReceived += (_, response) => responses.Add(response);

        await client.AddRequestAsync(request);
        using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        await client.SendAsync(cts.Token);
        return responses;
    }
}
