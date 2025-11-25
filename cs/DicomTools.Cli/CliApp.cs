using System.Text;
using System.Text.Json;

namespace DicomTools.Cli;

public static class CliApp
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true
    };

    public static async Task<int> RunAsync(string[] args)
    {
        Console.OutputEncoding = Encoding.UTF8;
        if (args.Length == 0 || args[0] is "-h" or "--help")
        {
            PrintUsage();
            return 1;
        }

        var command = args[0].ToLowerInvariant();
        var parser = new OptionParser(args.Skip(1));

        try
        {
            return command switch
            {
                "info" => InfoCommand.Execute(parser, JsonOptions),
                "anonymize" => AnonymizeCommand.Execute(parser),
                "to-image" => ImageCommand.Execute(parser),
                "transcode" => TranscodeCommand.Execute(parser),
                "validate" => ValidateCommand.Execute(parser),
                "echo" => await EchoCommand.ExecuteAsync(parser),
                "dump" => DumpCommand.Execute(parser),
                "stats" => StatsCommand.ExecuteStats(parser, JsonOptions),
                "histogram" => StatsCommand.ExecuteHistogram(parser, JsonOptions),
                _ => Unknown(command)
            };
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"error: {ex.Message}");
            return 1;
        }
    }

    private static void PrintUsage()
    {
        const string usage = """
        DicomTools.Cli (fo-dicom) - operações suportadas:
          info <input> [--json]
          anonymize <input> --output <path>
          to-image <input> --output <path> [--frame N] [--format png|jpeg]
          transcode <input> --output <path> --transfer-syntax <syntax>
          validate <input>
          echo <host:port>
          dump <input> [--depth N] [--max-value-length N]
          stats <input> [--frame N] [--json]
          histogram <input> [--bins N] [--frame N] [--json]
        """;
        Console.WriteLine(usage);
    }

    private static int Unknown(string command)
    {
        Console.Error.WriteLine($"unknown command: {command}");
        PrintUsage();
        return 1;
    }
}
