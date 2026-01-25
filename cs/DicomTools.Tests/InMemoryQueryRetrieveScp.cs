using System.Collections.Concurrent;
using FellowOakDicom;
using FellowOakDicom.Network;
using FellowOakDicom.Network.Client;
using Microsoft.Extensions.Logging;
using System.Text;

namespace DicomTools.Tests;

public class InMemoryQueryRetrieveScp : DicomService, IDicomServiceProvider, IDicomCFindProvider, IDicomCMoveProvider, IDicomCEchoProvider
{
    private static readonly List<DicomFile> SourceFiles = new();
    private static readonly ConcurrentDictionary<string, (string Host, int Port)> Destinations = new(StringComparer.OrdinalIgnoreCase);
    private static string? LastMoveError;

    public InMemoryQueryRetrieveScp(INetworkStream stream, Encoding fallbackEncoding, ILogger logger, DicomServiceDependencies dependencies)
        : base(stream, fallbackEncoding, logger, dependencies)
    {
    }

    public static void Reset()
    {
        lock (SourceFiles)
        {
            SourceFiles.Clear();
        }

        Destinations.Clear();
        LastMoveError = null;
    }

    public static void ConfigureSources(IEnumerable<DicomFile> files)
    {
        lock (SourceFiles)
        {
            SourceFiles.Clear();
            foreach (var file in files)
            {
                SourceFiles.Add(new DicomFile(file.Dataset.Clone()));
            }
        }
    }

    public static void RegisterDestination(string aeTitle, string host, int port)
    {
        Destinations[aeTitle] = (host, port);
    }

    public Task OnReceiveAssociationReleaseRequestAsync() => SendAssociationReleaseResponseAsync();

    public Task OnReceiveAssociationRequestAsync(DicomAssociation association)
    {
        foreach (var context in association.PresentationContexts)
        {
            if (context.AbstractSyntax == DicomUID.Verification
                || context.AbstractSyntax == DicomUID.StudyRootQueryRetrieveInformationModelFind
                || context.AbstractSyntax == DicomUID.StudyRootQueryRetrieveInformationModelMove)
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
        foreach (var match in ResolveMatches(request))
        {
            yield return new DicomCFindResponse(request, DicomStatus.Pending)
            {
                Dataset = BuildResponseDataset(match.Dataset, request.Level)
            };
        }

        yield return new DicomCFindResponse(request, DicomStatus.Success);
    }

    public async IAsyncEnumerable<DicomCMoveResponse> OnCMoveRequestAsync(DicomCMoveRequest request)
    {
        var matches = ResolveMatches(request).ToList();
        if (!Destinations.TryGetValue(request.DestinationAE, out var destination))
        {
            yield return new DicomCMoveResponse(request, DicomStatus.QueryRetrieveMoveDestinationUnknown);
            yield break;
        }

        var remaining = matches.Count;
        foreach (var match in matches)
        {
            var failed = false;
            try
            {
                await SendStoreRequestAsync(destination, match.File);
            }
            catch (Exception ex)
            {
                failed = true;
                LastMoveError = ex.ToString();
            }

            if (failed)
            {
                yield return new DicomCMoveResponse(request, DicomStatus.ProcessingFailure);
                yield break;
            }

            remaining--;
            yield return new DicomCMoveResponse(request, DicomStatus.Pending)
            {
                Remaining = remaining,
                Completed = matches.Count - remaining
            };
        }

        yield return new DicomCMoveResponse(request, DicomStatus.Success)
        {
            Completed = matches.Count
        };
    }

    private static IEnumerable<(DicomFile File, DicomDataset Dataset)> ResolveMatches(DicomRequest request)
    {
        var level = request switch
        {
            DicomCFindRequest findRequest => findRequest.Level,
            DicomCMoveRequest moveRequest => moveRequest.Level,
            _ => DicomQueryRetrieveLevel.Study
        };

        var dataset = request switch
        {
            DicomCFindRequest findRequest => findRequest.Dataset,
            DicomCMoveRequest moveRequest => moveRequest.Dataset,
            _ => request.Command
        } ?? new DicomDataset();
        var sources = GetSources();
        foreach (var file in sources)
        {
            var sourceDataset = file.Dataset;
            if (!Matches(dataset, sourceDataset, DicomTag.StudyInstanceUID))
            {
                continue;
            }

            if (level is DicomQueryRetrieveLevel.Series or DicomQueryRetrieveLevel.Image)
            {
                if (!Matches(dataset, sourceDataset, DicomTag.SeriesInstanceUID))
                {
                    continue;
                }
            }

            if (level == DicomQueryRetrieveLevel.Image)
            {
                if (!Matches(dataset, sourceDataset, DicomTag.SOPInstanceUID))
                {
                    continue;
                }
            }

            yield return (file, sourceDataset);
        }
    }

    private static bool Matches(DicomDataset query, DicomDataset source, DicomTag tag)
    {
        if (!query.TryGetString(tag, out var value) || string.IsNullOrWhiteSpace(value))
        {
            return true;
        }

        return source.TryGetString(tag, out var candidate) && string.Equals(candidate, value, StringComparison.Ordinal);
    }

    private static IReadOnlyList<DicomFile> GetSources()
    {
        lock (SourceFiles)
        {
            if (SourceFiles.Count == 0)
            {
                ConfigureSources(SampleSeriesHelper.GetSeriesFiles(3).Select(path => DicomFile.Open(path)));
            }

            return SourceFiles.Select(f => new DicomFile(f.Dataset.Clone())).ToArray();
        }
    }

    public static int GetSourceCount()
    {
        lock (SourceFiles)
        {
            return SourceFiles.Count;
        }
    }

    private static DicomDataset BuildResponseDataset(DicomDataset source, DicomQueryRetrieveLevel level)
    {
        var response = new DicomDataset
        {
            { DicomTag.QueryRetrieveLevel, level.ToString().ToUpperInvariant() }
        };

        CopyIfPresent(source, response, DicomTag.PatientName);
        CopyIfPresent(source, response, DicomTag.PatientID);
        CopyIfPresent(source, response, DicomTag.StudyInstanceUID);
        CopyIfPresent(source, response, DicomTag.StudyDate);
        CopyIfPresent(source, response, DicomTag.StudyTime);

        if (level is DicomQueryRetrieveLevel.Series or DicomQueryRetrieveLevel.Image)
        {
            CopyIfPresent(source, response, DicomTag.SeriesInstanceUID);
            CopyIfPresent(source, response, DicomTag.Modality);
        }

        if (level == DicomQueryRetrieveLevel.Image)
        {
            CopyIfPresent(source, response, DicomTag.SOPInstanceUID);
        }

        return response;
    }

    private static void CopyIfPresent(DicomDataset source, DicomDataset target, DicomTag tag)
    {
        if (source.TryGetString(tag, out var value) && !string.IsNullOrWhiteSpace(value))
        {
            target.AddOrUpdate(tag, value);
        }
    }

    private static async Task SendStoreRequestAsync((string Host, int Port) destination, DicomFile file)
    {
        var client = DicomClientFactory.Create(destination.Host, destination.Port, useTls: false, callingAe: "MOVE-SCP", calledAe: "DEST");
        await client.AddRequestAsync(new DicomCStoreRequest(new DicomFile(file.Dataset.Clone())));
        await client.SendAsync();
    }

    public static void AddSource(DicomFile file)
    {
        lock (SourceFiles)
        {
            SourceFiles.Add(new DicomFile(file.Dataset.Clone()));
        }
    }

    public static string? GetLastMoveError() => LastMoveError;
}
