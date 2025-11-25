using System.Linq;
using System.Threading.Tasks;
using FellowOakDicom;
using FellowOakDicom.Imaging;
using FellowOakDicom.Network;
using FellowOakDicom.Network.Client;

namespace DicomTools.Tests;

[Collection("Network")]
public class DicomNetworkStoreTests
{
    [Fact]
    public async Task CStore_StoresInstances_OnLocalScp()
    {
        InMemoryStoreScp.Clear();
        var port = TcpPortHelper.GetFreePort();

        using var server = DicomServerFactory.Create<InMemoryStoreScp>(port);
        await Task.Delay(100);

        var file = DicomFile.Open(SampleSeriesHelper.GetFirstFilePath());
        var request = new DicomCStoreRequest(file);

        var client = DicomClientFactory.Create("127.0.0.1", port, useTls: false, callingAe: "SCU", calledAe: "STORE");

        DicomStatus? status = null;
        request.OnResponseReceived += (_, response) => status = response.Status;

        await client.AddRequestAsync(request);
        await client.SendAsync();

        Assert.Equal(DicomStatus.Success, status);
        Assert.NotEmpty(InMemoryStoreScp.StoredFiles);

        var stored = InMemoryStoreScp.StoredFiles.Last();
        var storedUid = stored.Dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID);
        var sentUid = file.Dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID);

        Assert.Equal(sentUid, storedUid);

        var sentPixels = DicomPixelData.Create(file.Dataset, false).GetFrame(0).Data;
        var storedPixels = DicomPixelData.Create(stored.Dataset, false).GetFrame(0).Data;
        Assert.Equal(sentPixels, storedPixels);
    }

    [Fact]
    public async Task CStore_MultipleInstances_PersistsAll()
    {
        InMemoryStoreScp.Clear();
        var port = TcpPortHelper.GetFreePort();

        using var server = DicomServerFactory.Create<InMemoryStoreScp>(port);
        await Task.Delay(100);

        var files = SampleSeriesHelper.GetSeriesFiles(2)
            .Select(path => DicomFile.Open(path))
            .ToArray();

        var client = DicomClientFactory.Create("127.0.0.1", port, useTls: false, callingAe: "SCU", calledAe: "STORE");

        foreach (var file in files)
        {
            await client.AddRequestAsync(new DicomCStoreRequest(file));
        }

        await client.SendAsync();

        var storedUids = InMemoryStoreScp.StoredFiles
            .Select(f => f.Dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID))
            .ToArray();

        Assert.Equal(files.Length, storedUids.Length);
        foreach (var uid in files.Select(f => f.Dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID)))
        {
            Assert.Contains(uid, storedUids);
        }
    }
}
