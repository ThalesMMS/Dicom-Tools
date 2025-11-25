using Xunit.Sdk;

namespace DicomTools.Tests;

internal static class CiEnvironment
{
    internal static bool IsCi => string.Equals(Environment.GetEnvironmentVariable("CI"), "true", StringComparison.OrdinalIgnoreCase);

    internal static void SkipIfCi(string reason)
    {
        if (IsCi)
        {
            throw new SkipException(reason);
        }
    }
}
