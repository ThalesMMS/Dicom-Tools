using FellowOakDicom;
using FellowOakDicom.Network;
using Microsoft.Extensions.Logging;
using System.Text;

namespace DicomTools.Tests;

public class InMemoryWorklistScp : DicomService, IDicomServiceProvider, IDicomCFindProvider, IDicomCEchoProvider
{
    private static readonly List<DicomDataset> WorklistEntries = new();

    public InMemoryWorklistScp(INetworkStream stream, Encoding fallbackEncoding, ILogger logger, DicomServiceDependencies dependencies)
        : base(stream, fallbackEncoding, logger, dependencies)
    {
    }

    public static void Reset()
    {
        lock (WorklistEntries)
        {
            WorklistEntries.Clear();
        }
    }

    public static void ConfigureEntries(IEnumerable<DicomDataset> entries)
    {
        lock (WorklistEntries)
        {
            WorklistEntries.Clear();
            foreach (var entry in entries)
            {
                WorklistEntries.Add(entry.Clone());
            }
        }
    }

    public Task OnReceiveAssociationReleaseRequestAsync() => SendAssociationReleaseResponseAsync();

    public Task OnReceiveAssociationRequestAsync(DicomAssociation association)
    {
        foreach (var context in association.PresentationContexts)
        {
            if (context.AbstractSyntax == DicomUID.Verification || context.AbstractSyntax == DicomUID.ModalityWorklistInformationModelFind)
            {
                context.AcceptTransferSyntaxes(DicomTransferSyntax.ExplicitVRLittleEndian, DicomTransferSyntax.ImplicitVRLittleEndian);
            }
            else
            {
                context.SetResult(DicomPresentationContextResult.RejectAbstractSyntaxNotSupported);
            }
        }

        return SendAssociationAcceptAsync(association);
    }

    public Task<DicomCEchoResponse> OnCEchoRequestAsync(DicomCEchoRequest request) =>
        Task.FromResult(new DicomCEchoResponse(request, DicomStatus.Success));

    public void OnReceiveAbort(DicomAbortSource source, DicomAbortReason reason)
    {
    }

    public void OnConnectionClosed(Exception exception)
    {
    }

    public async IAsyncEnumerable<DicomCFindResponse> OnCFindRequestAsync(DicomCFindRequest request)
    {
        foreach (var match in ResolveMatches(request.Dataset))
        {
            yield return new DicomCFindResponse(request, DicomStatus.Pending)
            {
                Dataset = match
            };
        }

        yield return new DicomCFindResponse(request, DicomStatus.Success);
    }

    private static IEnumerable<DicomDataset> ResolveMatches(DicomDataset? query)
    {
        var entries = GetEntries();
        if (query == null)
        {
            return entries;
        }

        return entries.Where(entry => Matches(entry, query));
    }

    private static bool Matches(DicomDataset entry, DicomDataset query)
    {
        if (!MatchesValue(query, entry, DicomTag.PatientID)
            || !MatchesValue(query, entry, DicomTag.PatientName)
            || !MatchesValue(query, entry, DicomTag.AccessionNumber)
            || !MatchesValue(query, entry, DicomTag.PatientSex))
        {
            return false;
        }

        var querySps = GetFirstSequenceItem(query, DicomTag.ScheduledProcedureStepSequence);
        if (querySps == null)
        {
            return true;
        }

        var entrySps = GetFirstSequenceItem(entry, DicomTag.ScheduledProcedureStepSequence);
        if (entrySps == null)
        {
            return false;
        }

        if (!MatchesValue(querySps, entrySps, DicomTag.Modality))
        {
            return false;
        }

        if (!MatchesValue(querySps, entrySps, DicomTag.ScheduledProcedureStepStartDate))
        {
            return false;
        }

        return true;
    }

    private static bool MatchesValue(DicomDataset query, DicomDataset target, DicomTag tag)
    {
        if (!query.TryGetString(tag, out var expected) || string.IsNullOrWhiteSpace(expected))
        {
            return true;
        }

        return target.TryGetString(tag, out var candidate) &&
               string.Equals(candidate, expected, StringComparison.OrdinalIgnoreCase);
    }

    private static DicomDataset? GetFirstSequenceItem(DicomDataset dataset, DicomTag tag)
    {
        if (!dataset.Contains(tag))
        {
            return null;
        }

        var sequence = dataset.GetSequence(tag);
        return sequence.Items.Count > 0 ? sequence.Items[0] : null;
    }

    private static IReadOnlyList<DicomDataset> GetEntries()
    {
        lock (WorklistEntries)
        {
            return WorklistEntries.Select(entry => entry.Clone()).ToArray();
        }
    }
}
