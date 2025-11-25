using FellowOakDicom;
using FellowOakDicom.Network;
using FellowOakDicom.Network.Client;

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
        await client.SendAsync();

        if (status == DicomStatus.Success)
        {
            Console.WriteLine($"echo to {host}:{port} succeeded");
            return 0;
        }

        Console.Error.WriteLine($"echo to {host}:{port} failed ({status?.Description ?? "no response"})");
        return 1;
    }
}
