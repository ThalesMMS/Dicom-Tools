using System.Net;
using System.Net.Sockets;
using System.IO;
using System.Linq;

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
