using System.Net;
using FellowOakDicom;

namespace DicomTools.Tests;

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
