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
                "store-scu" => await NetworkCommand.ExecuteStoreScuAsync(parser, JsonOptions),
                "worklist" or "mwl" => await NetworkCommand.ExecuteWorklistAsync(parser, JsonOptions),
                "qido" => await NetworkCommand.ExecuteQidoAsync(parser, JsonOptions),
                "stow" => await NetworkCommand.ExecuteStowAsync(parser, JsonOptions),
                "wado" => await NetworkCommand.ExecuteWadoAsync(parser, JsonOptions),
                "sr-summary" or "sr" => StructuredReportCommand.Execute(parser, JsonOptions),
                "rt-check" => RtCheckCommand.Execute(parser, JsonOptions),
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
          store-scu <input> --host <host> --port <port> [--calling <AET>] [--called <AET>] [--timeout ms]
          worklist --host <host> --port <port> [--patient <name>] [--calling <AET>] [--called <AET>]
          qido --url <dicomweb-url>
          stow --url <dicomweb-url> <input>
          wado --url <dicomweb-url> --output <file>
          sr-summary <input>
          rt-check --plan <plan.dcm> [--dose <dose.dcm>] [--struct <struct.dcm>]
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
