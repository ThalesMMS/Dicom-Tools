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
    registry.Register({
        "validate",
        "General",
        "Validate DICOM structure and required identifiers (--json for machine-readable report)",
        [](const CommandContext& ctx) {
            return ValidateDicomFile(ctx.inputPath, ctx.outputDir, ctx.jsonOutput);
        }
    });

    registry.Register({
        "info",
        "General",
        "Export DICOM metadata summary (--json to emit dcmtk_metadata.json)",
        [](const CommandContext& ctx) {
            TestMetadataReport(ctx.inputPath, ctx.outputDir, ctx.jsonOutput);
            return 0;
        }
    });

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
            TestMetadataReport(ctx.inputPath, ctx.outputDir, ctx.jsonOutput);
            TestBMPPreview(ctx.inputPath, ctx.outputDir);
            TestDICOMDIRGeneration(ctx.inputPath, ctx.outputDir);
            TestSegmentationExport(ctx.inputPath, ctx.outputDir);
            TestNetworkEchoAndStore(ctx.inputPath, ctx.outputDir);
            TestCharacterSetRoundTrip(ctx.outputDir);
            TestSecondaryCapture(ctx.inputPath, ctx.outputDir);
            TestStructuredReport(ctx.inputPath, ctx.outputDir);
            TestRTStructRead(ctx.inputPath, ctx.outputDir);
            TestFunctionalGroupRead(ctx.inputPath, ctx.outputDir);
            TestWaveformAndPSReport(ctx.inputPath, ctx.outputDir);
            ValidateDicomFile(ctx.inputPath, ctx.outputDir, ctx.jsonOutput);
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
            TestMetadataReport(ctx.inputPath, ctx.outputDir, ctx.jsonOutput);
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

    registry.Register({
        "dcmtk:validate",
        "DCMTK",
        "Validate DICOM attributes and write validation report",
        [](const CommandContext& ctx) {
            return ValidateDicomFile(ctx.inputPath, ctx.outputDir, ctx.jsonOutput);
        }
    });

    registry.Register({
        "dcmtk:net",
        "DCMTK",
        "Run a local C-ECHO and C-STORE loopback against an in-process SCP",
        [](const CommandContext& ctx) {
            TestNetworkEchoAndStore(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "dcmtk:charset",
        "DCMTK",
        "Create a UTF-8 dataset and verify PN/LO round-trip without corruption",
        [](const CommandContext& ctx) {
            (void)ctx.inputPath;
            TestCharacterSetRoundTrip(ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "dcmtk:secondary",
        "DCMTK",
        "Generate a Secondary Capture instance from scratch with synthetic pixels",
        [](const CommandContext& ctx) {
            TestSecondaryCapture(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "dcmtk:sr",
        "DCMTK",
        "Create and validate a simple Structured Report (NUM + TEXT)",
        [](const CommandContext& ctx) {
            TestStructuredReport(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "dcmtk:rt",
        "DCMTK",
        "Summarize RTSTRUCT ROIs and contour frames",
        [](const CommandContext& ctx) {
            TestRTStructRead(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "dcmtk:fg",
        "DCMTK",
        "Inspect multi-frame functional groups and export first frame preview",
        [](const CommandContext& ctx) {
            TestFunctionalGroupRead(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "dcmtk:waveform",
        "DCMTK",
        "Summarize Waveform and Softcopy Presentation State metadata",
        [](const CommandContext& ctx) {
            TestWaveformAndPSReport(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });
}

#else
void DCMTKTests::RegisterCommands(CommandRegistry&) {}
#endif
