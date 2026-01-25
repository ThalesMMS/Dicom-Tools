using System.IO;
using System.Net.Http;
using System.Text.Json;
using FellowOakDicom;
using FellowOakDicom.Network;
using FellowOakDicom.Network.Client;

namespace DicomTools.Cli;

internal static class NetworkCommand
{
    internal static async Task<int> ExecuteStoreScuAsync(OptionParser parser, JsonSerializerOptions jsonOptions)
    {
        var input = parser.RequirePositional("input");
        var host = parser.GetOption("host") ?? "127.0.0.1";
        var port = parser.GetIntOption("port") ?? 11112;
        var calling = parser.GetOption("calling") ?? parser.GetOption("calling_aet") ?? "STORE-SCU";
        var called = parser.GetOption("called") ?? parser.GetOption("called_aet") ?? "STORE-SCP";
        var timeoutMs = parser.GetIntOption("timeout") ?? 5000;

        var file = DicomFile.Open(input);
        var request = new DicomCStoreRequest(file);
        var client = DicomClientFactory.Create(host, port, false, calling, called);

        using var cts = new CancellationTokenSource(TimeSpan.FromMilliseconds(timeoutMs));
        await client.AddRequestAsync(request);
        await client.SendAsync(cts.Token);

        var payload = new
        {
            ok = true,
            returncode = 0,
            stdout = $"C-STORE sent to {host}:{port}",
            stderr = string.Empty,
            output_files = new[] { input },
            metadata = new { host, port, calling, called }
        };
        Console.WriteLine(JsonSerializer.Serialize(payload, jsonOptions));
        return 0;
    }

    internal static async Task<int> ExecuteWorklistAsync(OptionParser parser, JsonSerializerOptions jsonOptions)
    {
        var host = parser.GetOption("host") ?? "127.0.0.1";
        var port = parser.GetIntOption("port") ?? 11112;
        var calling = parser.GetOption("calling") ?? parser.GetOption("calling_aet") ?? "MWL-SCU";
        var called = parser.GetOption("called") ?? parser.GetOption("called_aet") ?? "MWL-SCP";
        var patient = parser.GetOption("patient");
        var timeoutMs = parser.GetIntOption("timeout") ?? 5000;

        var request = DicomCFindRequest.CreateWorklistQuery(patientName: patient);
        var items = new List<Dictionary<string, string>>();
        request.OnResponseReceived += (_, response) =>
        {
            if (response.HasDataset && response.Dataset != null)
            {
                var dict = new Dictionary<string, string>
                {
                    ["PatientName"] = response.Dataset.GetSingleValueOrDefault(DicomTag.PatientName, string.Empty),
                    ["ScheduledProcedureStepDescription"] = response.Dataset.GetSingleValueOrDefault(DicomTag.ScheduledProcedureStepDescription, string.Empty)
                };
                items.Add(dict);
            }
        };

        var client = DicomClientFactory.Create(host, port, false, calling, called);
        await client.AddRequestAsync(request);
        using var cts = new CancellationTokenSource(TimeSpan.FromMilliseconds(timeoutMs));
        await client.SendAsync(cts.Token);

        var payload = new
        {
            ok = true,
            returncode = 0,
            stdout = $"MWL query to {host}:{port}",
            stderr = string.Empty,
            output_files = Array.Empty<string>(),
            metadata = new { host, port, calling, called, count = items.Count, items }
        };
        Console.WriteLine(JsonSerializer.Serialize(payload, jsonOptions));
        return 0;
    }

    internal static async Task<int> ExecuteQidoAsync(OptionParser parser, JsonSerializerOptions jsonOptions)
    {
        var url = parser.GetOption("url") ?? parser.RequirePositional("url");
        using var client = new HttpClient();
        var response = await client.GetAsync(url);
        var body = await response.Content.ReadAsStringAsync();

        var payload = new
        {
            ok = response.IsSuccessStatusCode,
            returncode = response.IsSuccessStatusCode ? 0 : 1,
            stdout = body,
            stderr = response.IsSuccessStatusCode ? string.Empty : $"HTTP {(int)response.StatusCode}",
            output_files = Array.Empty<string>(),
            metadata = new { url, status = (int)response.StatusCode }
        };
        Console.WriteLine(JsonSerializer.Serialize(payload, jsonOptions));
        return payload.ok ? 0 : 1;
    }

    internal static async Task<int> ExecuteStowAsync(OptionParser parser, JsonSerializerOptions jsonOptions)
    {
        var url = parser.GetOption("url") ?? parser.RequirePositional("url");
        var input = parser.RequirePositional("input");
        using var client = new HttpClient();
        var bytes = await File.ReadAllBytesAsync(input);
        using var content = new ByteArrayContent(bytes);
        content.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue("application/dicom");
        var response = await client.PostAsync(url, content);
        var payload = new
        {
            ok = response.IsSuccessStatusCode,
            returncode = response.IsSuccessStatusCode ? 0 : 1,
            stdout = $"STOW to {url} => {(int)response.StatusCode}",
            stderr = response.IsSuccessStatusCode ? string.Empty : $"HTTP {(int)response.StatusCode}",
            output_files = Array.Empty<string>(),
            metadata = new { url, status = (int)response.StatusCode }
        };
        Console.WriteLine(JsonSerializer.Serialize(payload, jsonOptions));
        return payload.ok ? 0 : 1;
    }

    internal static async Task<int> ExecuteWadoAsync(OptionParser parser, JsonSerializerOptions jsonOptions)
    {
        var url = parser.GetOption("url") ?? parser.RequirePositional("url");
        var output = parser.GetOption("output") ?? parser.RequirePositional("output");
        using var client = new HttpClient();
        var response = await client.GetAsync(url);
        var bytes = await response.Content.ReadAsByteArrayAsync();
        await File.WriteAllBytesAsync(output, bytes);

        var payload = new
        {
            ok = response.IsSuccessStatusCode,
            returncode = response.IsSuccessStatusCode ? 0 : 1,
            stdout = $"WADO saved to {output}",
            stderr = response.IsSuccessStatusCode ? string.Empty : $"HTTP {(int)response.StatusCode}",
            output_files = new[] { output },
            metadata = new { url, status = (int)response.StatusCode, bytes = bytes.Length }
        };
        Console.WriteLine(JsonSerializer.Serialize(payload, jsonOptions));
        return payload.ok ? 0 : 1;
    }
}
