using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
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
                    DicomTransferSyntax.ImplicitVRLittleEndian,
                    DicomTransferSyntax.DeflatedExplicitVRLittleEndian,
                    DicomTransferSyntax.ExplicitVRBigEndian,
                    DicomTransferSyntax.RLELossless,
                    DicomTransferSyntax.JPEG2000Lossless,
                    DicomTransferSyntax.JPEGLSLossless,
                    DicomTransferSyntax.JPEGProcess14SV1,
                    DicomTransferSyntax.JPEGProcess1);
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

internal sealed record CliResult(int ExitCode, string Stdout, string Stderr);

internal sealed class DicomWebStowServer : IAsyncDisposable
{
    private readonly HttpListener _listener = new();
    private readonly CancellationTokenSource _cts = new();
    private readonly Task _loopTask;

    private DicomWebStowServer(int port)
    {
        _listener.Prefixes.Add($"http://localhost:{port}/");
        _listener.Start();
        _loopTask = Task.Run(() => RunAsync(_cts.Token));
    }

    internal static Task<DicomWebStowServer> StartAsync(int port) =>
        Task.FromResult(new DicomWebStowServer(port));

    private async Task RunAsync(CancellationToken cancellationToken)
    {
        while (!cancellationToken.IsCancellationRequested)
        {
            HttpListenerContext? context = null;
            try
            {
                context = await _listener.GetContextAsync();
            }
            catch (HttpListenerException) when (cancellationToken.IsCancellationRequested)
            {
                break;
            }
            catch (ObjectDisposedException) when (cancellationToken.IsCancellationRequested)
            {
                break;
            }

            _ = Task.Run(() => HandleRequestAsync(context), cancellationToken);
        }
    }

    private static async Task HandleRequestAsync(HttpListenerContext context)
    {
        try
        {
            if (!string.Equals(context.Request.HttpMethod, "POST", StringComparison.OrdinalIgnoreCase)
                || context.Request.Url?.AbsolutePath != "/dicomweb/stow")
            {
                context.Response.StatusCode = (int)HttpStatusCode.NotFound;
                return;
            }

            using var ms = new MemoryStream();
            await context.Request.InputStream.CopyToAsync(ms);
            ms.Position = 0;
            var dicomFile = DicomFile.Open(ms, FileReadOption.ReadAll);
            InMemoryQueryRetrieveScp.AddSource(dicomFile);

            context.Response.StatusCode = (int)HttpStatusCode.OK;
        }
        catch
        {
            context.Response.StatusCode = (int)HttpStatusCode.BadRequest;
        }
        finally
        {
            context.Response.OutputStream.Close();
        }
    }

    public async ValueTask DisposeAsync()
    {
        _cts.Cancel();
        _listener.Stop();
        _listener.Close();
        try
        {
            await _loopTask;
        }
        catch
        {
        }

        _cts.Dispose();
    }
}

internal static class CliRunner
{
    private static string? _cachedCliPath;

    internal static CliResult Run(params string[] args)
    {
        var dllPath = EnsureCliBuilt();
        var psi = new ProcessStartInfo("dotnet")
        {
            WorkingDirectory = LocateCsRoot(),
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false
        };

        psi.ArgumentList.Add(dllPath);
        foreach (var arg in args)
        {
            psi.ArgumentList.Add(arg);
        }

        using var process = Process.Start(psi)!;
        var stdout = process.StandardOutput.ReadToEnd();
        var stderr = process.StandardError.ReadToEnd();
        process.WaitForExit();

        return new CliResult(process.ExitCode, stdout.Trim(), stderr.Trim());
    }

    private static string EnsureCliBuilt()
    {
        if (_cachedCliPath != null && File.Exists(_cachedCliPath))
        {
            return _cachedCliPath;
        }

        var csRoot = LocateCsRoot();
        var existing = FindBuiltCli(csRoot);
        if (existing != null)
        {
            _cachedCliPath = existing;
            return existing;
        }

        BuildCli(csRoot);
        existing = FindBuiltCli(csRoot);
        if (existing == null)
        {
            throw new FileNotFoundException("Could not locate built CLI after build command.");
        }

        _cachedCliPath = existing;
        return existing;
    }

    private static void BuildCli(string csRoot)
    {
        var psi = new ProcessStartInfo("dotnet")
        {
            WorkingDirectory = csRoot,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false
        };
        psi.ArgumentList.Add("build");
        psi.ArgumentList.Add("DicomTools.Cli/DicomTools.Cli.csproj");

        using var process = Process.Start(psi)!;
        var stdout = process.StandardOutput.ReadToEnd();
        var stderr = process.StandardError.ReadToEnd();
        process.WaitForExit();
        if (process.ExitCode != 0)
        {
            throw new InvalidOperationException($"Failed to build CLI: {stdout}\n{stderr}");
        }
    }

    private static string? FindBuiltCli(string csRoot)
    {
        var targets = new[] { "net10.0", "net8.0" };
        foreach (var target in targets)
        {
            var candidate = Path.Combine(csRoot, "bin", "Debug", target, "DicomTools.Cli.dll");
            if (File.Exists(candidate))
            {
                return candidate;
            }
        }

        return null;
    }

    private static string LocateCsRoot()
    {
        var current = new DirectoryInfo(AppContext.BaseDirectory);
        while (current != null)
        {
            var candidate = Path.Combine(current.FullName, "DicomTools.sln");
            if (File.Exists(candidate))
            {
                return current.FullName;
            }

            current = current.Parent;
        }

        throw new DirectoryNotFoundException("Could not locate cs root containing DicomTools.sln");
    }
}
