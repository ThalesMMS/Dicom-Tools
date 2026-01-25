namespace DicomTools.Tests;

internal static class CiEnvironment
{
    internal static bool IsCi => string.Equals(Environment.GetEnvironmentVariable("CI"), "true", StringComparison.OrdinalIgnoreCase);

    internal static bool ShouldSkip(string reason) => IsCi;
}
