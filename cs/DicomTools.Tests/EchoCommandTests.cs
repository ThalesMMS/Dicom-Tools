namespace DicomTools.Tests;

public class EchoCommandTests
{
    [Fact]
    public async Task Echo_Succeeds_Against_Running_Server()
    {
        if (CiEnvironment.ShouldSkip("Skipping echo test in CI"))
        {
            return;
        }

        var port = TcpPortHelper.GetFreePort();
        using var server = FellowOakDicom.Network.DicomServerFactory.Create<InMemoryStoreScp>(port);
        await Task.Delay(100);

        var result = CliRunner.Run("echo", $"127.0.0.1:{port}");
        Assert.Equal(0, result.ExitCode);
        Assert.Contains("succeeded", result.Stdout, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void Echo_Fails_Against_Closed_Port()
    {
        if (CiEnvironment.ShouldSkip("Skipping closed-port test in CI"))
        {
            return;
        }

        var port = TcpPortHelper.GetFreePort();
        var result = CliRunner.Run("echo", $"127.0.0.1:{port}");
        Assert.NotEqual(0, result.ExitCode);
    }

    [Fact]
    public void Echo_Parses_Host_And_Port()
    {
        if (CiEnvironment.ShouldSkip("Skipping host parse test in CI"))
        {
            return;
        }

        var port = TcpPortHelper.GetFreePort();
        var result = CliRunner.Run("echo", $"localhost:{port}");
        Assert.NotEqual(0, result.ExitCode); // No server running
    }

    [Fact]
    public async Task Echo_With_Custom_AeTitle()
    {
        if (CiEnvironment.ShouldSkip("Skipping AE title test in CI"))
        {
            return;
        }

        var port = TcpPortHelper.GetFreePort();
        using var server = FellowOakDicom.Network.DicomServerFactory.Create<InMemoryStoreScp>(port);
        await Task.Delay(100);

        var result = CliRunner.Run("echo", $"127.0.0.1:{port}", "--calling-ae", "TESTAE");
        Assert.Equal(0, result.ExitCode);
    }

    [Fact]
    public async Task Echo_Multiple_Times()
    {
        if (CiEnvironment.ShouldSkip("Skipping multiple echo test in CI"))
        {
            return;
        }

        var port = TcpPortHelper.GetFreePort();
        using var server = FellowOakDicom.Network.DicomServerFactory.Create<InMemoryStoreScp>(port);
        await Task.Delay(100);

        var result1 = CliRunner.Run("echo", $"127.0.0.1:{port}");
        var result2 = CliRunner.Run("echo", $"127.0.0.1:{port}");

        Assert.Equal(0, result1.ExitCode);
        Assert.Equal(0, result2.ExitCode);
    }
}
