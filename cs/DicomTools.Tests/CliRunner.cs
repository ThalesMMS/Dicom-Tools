using System.IO;
using System.Text;
using DicomTools.Cli;

namespace DicomTools.Tests;

internal sealed record CliResult(int ExitCode, string Stdout, string Stderr);

internal static class CliRunner
{
    private static readonly object Sync = new();

    internal static CliResult Run(params string[] args)
    {
        lock (Sync)
        {
            var originalOut = Console.Out;
            var originalErr = Console.Error;
            using var stdout = new StringWriter();
            using var stderr = new StringWriter();
            Console.SetOut(stdout);
            Console.SetError(stderr);
            Console.OutputEncoding = Encoding.UTF8;

            int exitCode;
            try
            {
                exitCode = CliApp.RunAsync(args).GetAwaiter().GetResult();
            }
            finally
            {
                Console.SetOut(originalOut);
                Console.SetError(originalErr);
            }

            return new CliResult(exitCode, stdout.ToString().Trim(), stderr.ToString().Trim());
        }
    }
}
