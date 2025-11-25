namespace DicomTools.Cli;

internal sealed class OptionParser
{
    private static readonly HashSet<string> FlagOptions = new(StringComparer.OrdinalIgnoreCase)
    {
        "json",
        "verbose",
        "help"
    };

    private readonly List<string> _positionals = new();
    private readonly Dictionary<string, string> _options = new(StringComparer.OrdinalIgnoreCase);
    private readonly HashSet<string> _flags = new(StringComparer.OrdinalIgnoreCase);

    internal OptionParser(IEnumerable<string> args)
    {
        var tokens = args.ToArray();
        for (var i = 0; i < tokens.Length; i++)
        {
            var token = tokens[i];
            if (token.StartsWith('-'))
            {
                var name = Normalize(token);
                if (FlagOptions.Contains(name))
                {
                    _flags.Add(name);
                    continue;
                }

                string value = "true";
                if (i + 1 < tokens.Length && !tokens[i + 1].StartsWith('-'))
                {
                    value = tokens[i + 1];
                    i++;
                }

                _options[name] = value;
            }
            else
            {
                _positionals.Add(token);
            }
        }
    }

    internal string RequirePositional(string name)
    {
        if (_positionals.Count == 0)
        {
            throw new ArgumentException($"{name} is required");
        }

        var value = _positionals[0];
        _positionals.RemoveAt(0);
        return value;
    }

    internal string? GetOption(params string[] names)
    {
        foreach (var name in names)
        {
            var key = Normalize(name);
            if (_options.TryGetValue(key, out var value))
            {
                return value;
            }
        }

        return null;
    }

    internal int? GetIntOption(params string[] names)
    {
        var value = GetOption(names);
        if (value != null && int.TryParse(value, out var parsed))
        {
            return parsed;
        }

        return null;
    }

    internal bool HasFlag(params string[] names) =>
        names.Any(name => _flags.Contains(Normalize(name)));

    private static string Normalize(string name) => name.TrimStart('-');
}
