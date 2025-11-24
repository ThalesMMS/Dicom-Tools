using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text;
using FellowOakDicom;
using FellowOakDicom.Network;
using FellowOakDicom.Network.Client;
using Microsoft.Extensions.Logging;

namespace DicomTools.Tests;

internal static class SampleSeriesHelper
{
    internal static string GetFirstFilePath() =>
        GetSeriesFiles(1).Single();

    internal static IEnumerable<string> GetAllSeriesFiles() =>
        GetSeriesFiles(int.MaxValue);

    internal static IEnumerable<string> GetSeriesFiles(int count)
    {
        var sampleDir = ResolveSampleSeriesDirectory();
        return Directory.EnumerateFiles(sampleDir, "*.dcm")
            .OrderBy(path => path, StringComparer.Ordinal)
            .Take(count)
            .ToArray();
    }

    private static string ResolveSampleSeriesDirectory()
    {
        var current = new DirectoryInfo(AppContext.BaseDirectory);
        while (current != null)
        {
            var candidate = Path.Combine(current.FullName, "sample_series");
            if (Directory.Exists(candidate))
            {
                return candidate;
            }

            current = current.Parent;
        }

        throw new DirectoryNotFoundException("Could not locate sample_series folder from test base directory.");
    }
}

internal static class TcpPortHelper
{
    internal static int GetFreePort()
    {
        var listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();
        var port = ((IPEndPoint)listener.LocalEndpoint).Port;
        listener.Stop();
        return port;
    }
}

public class InMemoryStoreScp : DicomService, IDicomServiceProvider, IDicomCStoreProvider, IDicomCEchoProvider
{
    private static readonly ConcurrentBag<DicomFile> Files = new();

    public static IReadOnlyCollection<DicomFile> StoredFiles => Files;

    public InMemoryStoreScp(INetworkStream stream, Encoding fallbackEncoding, ILogger logger, DicomServiceDependencies dependencies)
        : base(stream, fallbackEncoding, logger, dependencies)
    {
    }

    public static void Clear()
    {
        while (Files.TryTake(out _))
        {
        }
    }

    public Task OnReceiveAssociationReleaseRequestAsync() => SendAssociationReleaseResponseAsync();

    public Task OnReceiveAssociationRequestAsync(DicomAssociation association)
    {
        foreach (var context in association.PresentationContexts)
        {
            if (context.AbstractSyntax == DicomUID.Verification || context.AbstractSyntax.StorageCategory != DicomStorageCategory.None)
            {
                context.AcceptTransferSyntaxes(
                    DicomTransferSyntax.ExplicitVRLittleEndian,
                    DicomTransferSyntax.ImplicitVRLittleEndian);
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

    public Task<DicomCStoreResponse> OnCStoreRequestAsync(DicomCStoreRequest request)
    {
        if (request.File != null)
        {
            Files.Add(new DicomFile(request.File.Dataset.Clone()));
        }
        else if (request.Dataset != null)
        {
            Files.Add(new DicomFile(request.Dataset.Clone()));
        }

        return Task.FromResult(new DicomCStoreResponse(request, DicomStatus.Success));
    }

    public Task OnCStoreRequestExceptionAsync(string tempFileName, Exception e) => Task.CompletedTask;

    public void OnReceiveAbort(DicomAbortSource source, DicomAbortReason reason)
    {
    }

    public void OnConnectionClosed(Exception exception)
    {
    }
}
