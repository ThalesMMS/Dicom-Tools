namespace DicomTools.Cli;

public static class Program
{
    public static async Task<int> Main(string[] args) => await CliApp.RunAsync(args);
}
