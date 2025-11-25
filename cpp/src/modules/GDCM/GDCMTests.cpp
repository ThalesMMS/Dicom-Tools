//
// GDCMTests.cpp
// DicomToolsCpp
//
// Registers GDCM feature commands and connects them to their corresponding demo actions.
//
// Thales Matheus Mendonça Santos - November 2025

#include "GDCMTestInterface.h"

#include "GDCMFeatureActions.h"
#include "cli/CommandRegistry.h"

#ifdef USE_GDCM

void GDCMTests::RegisterCommands(CommandRegistry& registry) {
    // Master command executes the entire suite of GDCM feature demos
    registry.Register({
        "test-gdcm",
        "GDCM",
        "Run all GDCM feature tests",
        [](const CommandContext& ctx) {
            TestTagInspection(ctx.inputPath, ctx.outputDir);
            TestAnonymization(ctx.inputPath, ctx.outputDir);
            TestDecompression(ctx.inputPath, ctx.outputDir);
            TestUIDRewrite(ctx.inputPath, ctx.outputDir);
            TestDatasetDump(ctx.inputPath, ctx.outputDir);
            TestJPEGBaselineTranscode(ctx.inputPath, ctx.outputDir);
            TestJPEGLosslessP14Transcode(ctx.inputPath, ctx.outputDir);
            TestJPEG2000Transcode(ctx.inputPath, ctx.outputDir);
            TestJPEG2000Lossy(ctx.inputPath, ctx.outputDir);
            TestRLETranscode(ctx.inputPath, ctx.outputDir);
            TestRLEPlanarConfiguration(ctx.inputPath, ctx.outputDir);
            TestJPEGLSTranscode(ctx.inputPath, ctx.outputDir);
            TestPixelStatistics(ctx.inputPath, ctx.outputDir);
            TestDirectoryScan(ctx.inputPath, ctx.outputDir);
            TestPreviewExport(ctx.inputPath, ctx.outputDir);
            TestSequenceEditing(ctx.inputPath, ctx.outputDir);
            TestDicomdirRead(ctx.inputPath, ctx.outputDir);
            TestStringFilterCharsets(ctx.inputPath, ctx.outputDir);
            TestRTStructRead(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "gdcm:jpeg-baseline",
        "GDCM",
        "Transcode to JPEG Baseline (Process 1) for lossy coverage",
        [](const CommandContext& ctx) {
            TestJPEGBaselineTranscode(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "gdcm:jpeg-p14",
        "GDCM",
        "Transcode to JPEG Lossless Process 14 (12-bit corner cases)",
        [](const CommandContext& ctx) {
            TestJPEGLosslessP14Transcode(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "gdcm:tags",
        "GDCM",
        "Inspect common tags and print patient identifiers",
        [](const CommandContext& ctx) {
            TestTagInspection(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "gdcm:anonymize",
        "GDCM",
        "Strip PHI fields and write anonymized copy",
        [](const CommandContext& ctx) {
            TestAnonymization(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "gdcm:transcode-j2k",
        "GDCM",
        "Transcode to JPEG2000 (lossless) to validate codec support",
        [](const CommandContext& ctx) {
            TestJPEG2000Transcode(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "gdcm:transcode-j2k-lossy",
        "GDCM",
        "Transcode to JPEG2000 (lossy) to exercise lossy path",
        [](const CommandContext& ctx) {
            TestJPEG2000Lossy(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "gdcm:jpegls",
        "GDCM",
        "Transcode to JPEG-LS Lossless to validate codec support",
        [](const CommandContext& ctx) {
            TestJPEGLSTranscode(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "gdcm:retag-uids",
        "GDCM",
        "Regenerate Study/Series/SOP Instance UIDs and save copy",
        [](const CommandContext& ctx) {
            TestUIDRewrite(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "gdcm:dump",
        "GDCM",
        "Write a verbose dataset dump to text for QA",
        [](const CommandContext& ctx) {
            TestDatasetDump(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "gdcm:transcode-rle",
        "GDCM",
        "Transcode to RLE Lossless for encapsulated transfer syntax validation",
        [](const CommandContext& ctx) {
            TestRLETranscode(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "gdcm:transcode-rle-planar",
        "GDCM",
        "Transcode to RLE Lossless with planar configuration for RGB data",
        [](const CommandContext& ctx) {
            TestRLEPlanarConfiguration(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "gdcm:stats",
        "GDCM",
        "Compute min/max/mean pixel stats and write to text",
        [](const CommandContext& ctx) {
            TestPixelStatistics(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "gdcm:scan",
        "GDCM",
        "Scan an input directory and index studies/series to CSV",
        [](const CommandContext& ctx) {
            TestDirectoryScan(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "gdcm:preview",
        "GDCM",
        "Export an 8-bit PGM preview from the first slice",
        [](const CommandContext& ctx) {
            TestPreviewExport(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "gdcm:sequence",
        "GDCM",
        "Create/modify ReferencedSeriesSequence with nested items",
        [](const CommandContext& ctx) {
            TestSequenceEditing(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "gdcm:dicomdir",
        "GDCM",
        "Read a DICOMDIR and emit a summary of its records",
        [](const CommandContext& ctx) {
            TestDicomdirRead(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "gdcm:charset",
        "GDCM",
        "Round-trip PN/LO with StringFilter under non-default SpecificCharacterSet",
        [](const CommandContext& ctx) {
            TestStringFilterCharsets(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "gdcm:rt",
        "GDCM",
        "Summarize RTSTRUCT/SEG ROI names and contour frames",
        [](const CommandContext& ctx) {
            TestRTStructRead(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });
}

#else
void GDCMTests::RegisterCommands(CommandRegistry&) {}
#endif
