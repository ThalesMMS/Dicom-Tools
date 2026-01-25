using FellowOakDicom;

namespace DicomTools.Cli;

internal static class DumpCommand
{
    internal static int Execute(OptionParser parser)
    {
        var input = parser.RequirePositional("input");
        var depth = parser.GetIntOption("depth") ?? 4;
        var maxValueLength = parser.GetIntOption("max-value-length") ?? 64;

        var dataset = DicomFile.Open(input).Dataset;
        DumpDataset(dataset, 0, depth, maxValueLength);
        return 0;
    }

    private static void DumpDataset(DicomDataset dataset, int level, int maxDepth, int maxValueLength)
    {
        if (level > maxDepth)
        {
            return;
        }

        foreach (var item in dataset)
        {
            var indent = new string(' ', level * 2);
            switch (item)
            {
                case DicomElement element:
                    var rendered = element.ToString();
                    if (rendered.Length > maxValueLength)
                    {
                        rendered = rendered[..maxValueLength] + "...";
                    }
                    Console.WriteLine($"{indent}{rendered}");
                    break;
                case DicomSequence sequence:
                    Console.WriteLine($"{indent}{sequence.Tag} SQ ({sequence.Items.Count} items)");
                    var index = 0;
                    foreach (var sqItem in sequence.Items)
                    {
                        Console.WriteLine($"{indent}  Item {index++}");
                        DumpDataset(sqItem, level + 2, maxDepth, maxValueLength);
                    }
                    break;
                default:
                    Console.WriteLine($"{indent}{item.Tag} {item.ValueRepresentation.Code}");
                    break;
            }
        }
    }
}
