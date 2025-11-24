//
// DCMTKTests.cpp
// DicomToolsCpp
//
// Registers DCMTK feature commands and wires them to concrete test actions for the CLI.
//
// Thales Matheus Mendonça Santos - November 2025

#include "DCMTKTestInterface.h"

#include "DCMTKFeatureActions.h"
#include "cli/CommandRegistry.h"

#ifdef USE_DCMTK

void DCMTKTests::RegisterCommands(CommandRegistry& registry) {
    // Composite command to run every DCMTK demo action in one go
    registry.Register({
        "test-dcmtk",
        "DCMTK",
        "Run DCMTK feature tests",
        [](const CommandContext& ctx) {
            TestTagModification(ctx.inputPath, ctx.outputDir);
            TestPixelDataExtraction(ctx.inputPath, ctx.outputDir);
            TestLosslessJPEGReencode(ctx.inputPath, ctx.outputDir);
            TestJPEGBaseline(ctx.inputPath, ctx.outputDir);
            TestRLEReencode(ctx.inputPath, ctx.outputDir);
            TestRawDump(ctx.inputPath, ctx.outputDir);
            TestExplicitVRRewrite(ctx.inputPath, ctx.outputDir);
            TestMetadataReport(ctx.inputPath, ctx.outputDir);
            TestBMPPreview(ctx.inputPath, ctx.outputDir);
            TestDICOMDIRGeneration(ctx.inputPath, ctx.outputDir);
            TestSegmentationExport(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "dcmtk:modify",
        "DCMTK",
        "Modify basic tags and persist a sanitized copy",
        [](const CommandContext& ctx) {
            TestTagModification(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "dcmtk:ppm",
        "DCMTK",
        "Export pixel data to portable map format",
        [](const CommandContext& ctx) {
            TestPixelDataExtraction(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "dcmtk:jpeg-lossless",
        "DCMTK",
        "Re-encode to JPEG Lossless to validate JPEG codec support",
        [](const CommandContext& ctx) {
            TestLosslessJPEGReencode(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "dcmtk:jpeg-baseline",
        "DCMTK",
        "Re-encode to JPEG Baseline (Process 1) to test lossy codecs",
        [](const CommandContext& ctx) {
            TestJPEGBaseline(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "dcmtk:rle",
        "DCMTK",
        "Re-encode to RLE Lossless",
        [](const CommandContext& ctx) {
            TestRLEReencode(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "dcmtk:raw-dump",
        "DCMTK",
        "Dump raw pixel buffer for quick regression checks",
        [](const CommandContext& ctx) {
            TestRawDump(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "dcmtk:explicit-vr",
        "DCMTK",
        "Rewrite using Explicit VR Little Endian to validate transcoding",
        [](const CommandContext& ctx) {
            TestExplicitVRRewrite(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "dcmtk:metadata",
        "DCMTK",
        "Export common metadata fields to text",
        [](const CommandContext& ctx) {
            TestMetadataReport(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "dcmtk:bmp",
        "DCMTK",
        "Export an 8-bit BMP preview frame",
        [](const CommandContext& ctx) {
            TestBMPPreview(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "dcmtk:dicomdir",
        "DCMTK",
        "Generate a simple DICOMDIR for the input series",
        [](const CommandContext& ctx) {
            TestDICOMDIRGeneration(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "dcmtk:seg",
        "DCMTK",
        "Synthesize a binary SEG instance using dcmseg",
        [](const CommandContext& ctx) {
            TestSegmentationExport(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });
}

#else
void DCMTKTests::RegisterCommands(CommandRegistry&) {}
#endif
