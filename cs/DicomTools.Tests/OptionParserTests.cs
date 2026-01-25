using DicomTools.Cli;

namespace DicomTools.Tests;

public class OptionParserTests
{
    [Fact]
    public void Parse_Empty_Args()
    {
        var parser = new OptionParser(Array.Empty<string>());

        Assert.False(parser.HasFlag("json"));
        Assert.Null(parser.GetOption("output"));
        Assert.Throws<ArgumentException>(() => parser.RequirePositional("input"));
    }

    [Fact]
    public void Parse_Only_Positionals()
    {
        var parser = new OptionParser(new[] { "file1.dcm", "file2.dcm", "file3.dcm" });

        Assert.Equal("file1.dcm", parser.RequirePositional("first"));
        Assert.Equal("file2.dcm", parser.RequirePositional("second"));
        Assert.Equal("file3.dcm", parser.RequirePositional("third"));
        Assert.Throws<ArgumentException>(() => parser.RequirePositional("fourth"));
    }

    [Fact]
    public void Parse_Single_Dash_Options()
    {
        var parser = new OptionParser(new[] { "-o", "output.dcm", "-f", "png" });

        Assert.Equal("output.dcm", parser.GetOption("o"));
        Assert.Equal("png", parser.GetOption("f"));
    }

    [Fact]
    public void Parse_Double_Dash_Options()
    {
        var parser = new OptionParser(new[] { "--output", "output.dcm", "--format", "png" });

        Assert.Equal("output.dcm", parser.GetOption("output"));
        Assert.Equal("png", parser.GetOption("format"));
    }

    [Fact]
    public void Parse_Mixed_Dashes()
    {
        var parser = new OptionParser(new[] { "-o", "output.dcm", "--format", "png" });

        Assert.Equal("output.dcm", parser.GetOption("o"));
        Assert.Equal("png", parser.GetOption("format"));
    }

    [Fact]
    public void GetOption_Multiple_Names()
    {
        var parser = new OptionParser(new[] { "--output", "file.dcm" });

        Assert.Equal("file.dcm", parser.GetOption("output", "o"));
        Assert.Equal("file.dcm", parser.GetOption("o", "output"));
    }

    [Fact]
    public void GetOption_Short_Alias()
    {
        var parser = new OptionParser(new[] { "-o", "file.dcm" });

        Assert.Equal("file.dcm", parser.GetOption("output", "o"));
    }

    [Fact]
    public void HasFlag_Json()
    {
        var parser = new OptionParser(new[] { "--json", "input.dcm" });

        Assert.True(parser.HasFlag("json"));
        Assert.False(parser.HasFlag("verbose"));
    }

    [Fact]
    public void HasFlag_Verbose()
    {
        var parser = new OptionParser(new[] { "--verbose", "input.dcm" });

        Assert.True(parser.HasFlag("verbose"));
        Assert.False(parser.HasFlag("json"));
    }

    [Fact]
    public void HasFlag_Help()
    {
        var parser = new OptionParser(new[] { "--help" });

        Assert.True(parser.HasFlag("help"));
    }

    [Fact]
    public void HasFlag_Multiple_Names()
    {
        var parser = new OptionParser(new[] { "--json" });

        Assert.True(parser.HasFlag("json", "j"));
        Assert.False(parser.HasFlag("verbose", "v"));
    }

    [Fact]
    public void GetIntOption_Valid_Integer()
    {
        var parser = new OptionParser(new[] { "--frame", "5", "--bins", "256" });

        Assert.Equal(5, parser.GetIntOption("frame"));
        Assert.Equal(256, parser.GetIntOption("bins"));
    }

    [Fact]
    public void GetIntOption_Invalid_Integer_Returns_Null()
    {
        var parser = new OptionParser(new[] { "--frame", "not-a-number" });

        Assert.Null(parser.GetIntOption("frame"));
    }

    [Fact]
    public void GetIntOption_Missing_Returns_Null()
    {
        var parser = new OptionParser(new[] { "input.dcm" });

        Assert.Null(parser.GetIntOption("frame"));
    }

    [Fact]
    public void Options_Are_Case_Insensitive()
    {
        var parser = new OptionParser(new[] { "--OUTPUT", "file.dcm", "--JSON" });

        Assert.Equal("file.dcm", parser.GetOption("output"));
        Assert.Equal("file.dcm", parser.GetOption("Output"));
        Assert.True(parser.HasFlag("json"));
        Assert.True(parser.HasFlag("JSON"));
    }

    [Fact]
    public void Parse_Complex_Command_Line()
    {
        var args = new[]
        {
            "--json",
            "--output", "/path/to/output.dcm",
            "-f", "png",
            "--frame", "3",
            "input1.dcm",
            "input2.dcm"
        };
        var parser = new OptionParser(args);

        Assert.True(parser.HasFlag("json"));
        Assert.Equal("/path/to/output.dcm", parser.GetOption("output"));
        Assert.Equal("png", parser.GetOption("f"));
        Assert.Equal(3, parser.GetIntOption("frame"));
        Assert.Equal("input1.dcm", parser.RequirePositional("first"));
        Assert.Equal("input2.dcm", parser.RequirePositional("second"));
    }

    [Fact]
    public void Option_Without_Value_Sets_True()
    {
        var parser = new OptionParser(new[] { "--custom-flag" });

        Assert.Equal("true", parser.GetOption("custom-flag"));
    }

    [Fact]
    public void Option_At_End_Without_Value()
    {
        var parser = new OptionParser(new[] { "input.dcm", "--custom" });

        Assert.Equal("input.dcm", parser.RequirePositional("input"));
        Assert.Equal("true", parser.GetOption("custom"));
    }

    [Fact]
    public void Multiple_Flags_In_Sequence()
    {
        var parser = new OptionParser(new[] { "--json", "--verbose", "--help" });

        Assert.True(parser.HasFlag("json"));
        Assert.True(parser.HasFlag("verbose"));
        Assert.True(parser.HasFlag("help"));
    }

    [Fact]
    public void Positionals_Mixed_With_Options()
    {
        var parser = new OptionParser(new[] { "pos1", "--opt", "val", "pos2" });

        Assert.Equal("val", parser.GetOption("opt"));
        Assert.Equal("pos1", parser.RequirePositional("first"));
        Assert.Equal("pos2", parser.RequirePositional("second"));
    }

    [Fact]
    public void GetIntOption_With_Multiple_Names()
    {
        var parser = new OptionParser(new[] { "-f", "10" });

        Assert.Equal(10, parser.GetIntOption("frame", "f"));
    }

    [Fact]
    public void Negative_Integer_Option()
    {
        var parser = new OptionParser(new[] { "--offset", "-5" });

        Assert.Null(parser.GetIntOption("offset")); // -5 is treated as a flag
    }
}
