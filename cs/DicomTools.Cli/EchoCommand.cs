using FellowOakDicom;
using FellowOakDicom.Network;
using FellowOakDicom.Network.Client;
using System.Threading;

namespace DicomTools.Cli;

internal static class EchoCommand
{
    internal static async Task<int> ExecuteAsync(OptionParser parser)
    {
        var target = parser.RequirePositional("host:port");
        var (host, port) = PixelDataHelpers.ParseHostPort(target);

        var client = DicomClientFactory.Create(host, port, useTls: false, callingAe: "SCU", calledAe: "ANY-SCP");
        var request = new DicomCEchoRequest();

        DicomStatus? status = null;
        request.OnResponseReceived += (_, response) => status = response.Status;

        await client.AddRequestAsync(request);

        using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(5));
        var sendTask = client.SendAsync(cts.Token);
        var completed = await Task.WhenAny(sendTask, Task.Delay(TimeSpan.FromSeconds(5), cts.Token));
        if (completed != sendTask)
        {
            return Fail($"echo to {host}:{port} timed out");
        }

        if (status == DicomStatus.Success)
        {
            Console.WriteLine($"echo to {host}:{port} succeeded");
            return 0;
        }

        return Fail($"echo to {host}:{port} failed ({status?.Description ?? "no response"})");
    }

    private static int Fail(string message)
    {
        Console.Error.WriteLine(message);
        return 1;
    }
}
