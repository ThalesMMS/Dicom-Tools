using FellowOakDicom;
using FellowOakDicom.Imaging.Codec;

namespace DicomTools.Cli;

internal static class TranscodeCommand
{
    internal static int Execute(OptionParser parser)
    {
        var input = parser.RequirePositional("input");
        var output = parser.GetOption("output", "o") ?? CliHelpers.BuildDefaultOutput(input, "_transcoded.dcm");
        var syntaxKey = parser.GetOption("transfer-syntax", "syntax") ?? "explicit";
        CliHelpers.EnsureParentDirectory(output);

        var targetSyntax = ResolveTransferSyntax(syntaxKey);
        var file = DicomFile.Open(input);

        var transcoder = new DicomTranscoder(file.FileMetaInfo.TransferSyntax, targetSyntax);
        var transcoded = transcoder.Transcode(file);
        transcoded.Save(output);

        Console.WriteLine($"Transcoded to {targetSyntax.UID.UID} -> {output}");
        return 0;
    }

    private static DicomTransferSyntax ResolveTransferSyntax(string value)
    {
        var key = value.Trim().ToLowerInvariant();
        return key switch
        {
            "explicit" or "explicit-little" or "evr" => DicomTransferSyntax.ExplicitVRLittleEndian,
            "implicit" or "implicit-little" or "ivr" => DicomTransferSyntax.ImplicitVRLittleEndian,
            "big" or "explicit-be" or "be" => DicomTransferSyntax.ExplicitVRBigEndian,
            "jpeg2000" or "j2k" or "jp2" => DicomTransferSyntax.JPEG2000Lossless,
            "rle" => DicomTransferSyntax.RLELossless,
            "jpegls" or "jpeg-ls" => DicomTransferSyntax.JPEGLSLossless,
            "jpeg-lossless" or "jpeg-lossless-14" => DicomTransferSyntax.JPEGProcess14SV1,
            _ => DicomTransferSyntax.ExplicitVRLittleEndian
        };
    }
}
