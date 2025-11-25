using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using FellowOakDicom;
using FellowOakDicom.Network;
using FellowOakDicom.Network.Client;

namespace DicomTools.Tests;

[Collection("Network")]
public class WorklistTests
{
    [Fact]
    public async Task Worklist_CFind_ReturnsMatchingStep()
    {
        CiEnvironment.SkipIfCi("Skipping worklist network tests in CI to avoid socket restrictions");
        var entry = BuildWorklistEntry();
        InMemoryWorklistScp.Reset();
        InMemoryWorklistScp.ConfigureEntries(new[] { entry });

        var port = TcpPortHelper.GetFreePort();
        using var server = DicomServerFactory.Create<InMemoryWorklistScp>(port);
        await Task.Delay(100);

        var responses = new List<DicomCFindResponse>();
        var request = DicomCFindRequest.CreateWorklistQuery(
            "WL-001",
            "WORKLIST^PATIENT",
            "ACC-123",
            "F",
            "MR",
            null);

        var queryDataset = request.Dataset ?? throw new InvalidOperationException("Worklist query dataset should not be null");
        Assert.Equal("WL-001", queryDataset.GetSingleValue<string>(DicomTag.PatientID));
        Assert.Equal("WORKLIST^PATIENT", queryDataset.GetSingleValue<string>(DicomTag.PatientName));
        var querySps = queryDataset.GetSequence(DicomTag.ScheduledProcedureStepSequence).Single();
        Assert.Equal("MR", querySps.GetSingleValue<string>(DicomTag.Modality));
        queryDataset.TryGetString(DicomTag.AccessionNumber, out _);

        request.OnResponseReceived += (_, response) => responses.Add(response);

        var client = DicomClientFactory.Create("127.0.0.1", port, useTls: false, callingAe: "SCU", calledAe: "MWL");
        await client.AddRequestAsync(request);
        using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        await client.SendAsync(cts.Token);

        Assert.Contains(responses, r => r.Status == DicomStatus.Pending);
        Assert.Contains(responses, r => r.Status == DicomStatus.Success);

        var matched = responses.First(r => r.Status == DicomStatus.Pending).Dataset!;
        Assert.Equal("WL-001", matched.GetSingleValue<string>(DicomTag.PatientID));
        Assert.Equal("WORKLIST^PATIENT", matched.GetSingleValue<string>(DicomTag.PatientName));
        Assert.Equal("ACC-123", matched.GetSingleValue<string>(DicomTag.AccessionNumber));

        var sps = matched.GetSequence(DicomTag.ScheduledProcedureStepSequence).Single();
        Assert.Equal("MR", sps.GetSingleValue<string>(DicomTag.Modality));
        Assert.Equal("20240201", sps.GetSingleValue<string>(DicomTag.ScheduledProcedureStepStartDate));
        Assert.Equal("MAIN-STATION", sps.GetSingleValue<string>(DicomTag.ScheduledStationAETitle));
    }

    private static DicomDataset BuildWorklistEntry()
    {
        var sps = new DicomDataset
        {
            { DicomTag.Modality, "MR" },
            { DicomTag.ScheduledProcedureStepStartDate, "20240201" },
            { DicomTag.ScheduledProcedureStepStartTime, "093000" },
            { DicomTag.ScheduledProcedureStepDescription, "BRAIN MRI" },
            { DicomTag.ScheduledStationAETitle, "MAIN-STATION" }
        };

        return new DicomDataset
        {
            { DicomTag.PatientName, "WORKLIST^PATIENT" },
            { DicomTag.PatientID, "WL-001" },
            { DicomTag.PatientSex, "F" },
            { DicomTag.AccessionNumber, "ACC-123" },
            { DicomTag.StudyInstanceUID, DicomUIDGenerator.GenerateDerivedFromUUID() },
            { DicomTag.RequestedProcedureID, "REQ-1" },
            { DicomTag.ScheduledProcedureStepSequence, new DicomSequence(DicomTag.ScheduledProcedureStepSequence, sps) }
        };
    }
}
