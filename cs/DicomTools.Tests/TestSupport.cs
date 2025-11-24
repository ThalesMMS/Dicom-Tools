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

internal sealed record CliResult(int ExitCode, string Stdout, string Stderr);

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
