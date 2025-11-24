//
// VTKTests.cpp
// DicomToolsCpp
//
// Registers VTK feature commands and routes them to the underlying demo implementations.
//
// Thales Matheus Mendonça Santos - November 2025

#include "VTKTestInterface.h"

#include "VTKFeatureActions.h"
#include "cli/CommandRegistry.h"

#ifdef USE_VTK

void VTKTests::RegisterCommands(CommandRegistry& registry) {
    // Umbrella command that runs every VTK demo sequentially
    registry.Register({
        "test-vtk",
        "VTK",
        "Run all VTK feature tests",
        [](const CommandContext& ctx) {
            TestImageExport(ctx.inputPath, ctx.outputDir);
            TestNiftiExport(ctx.inputPath, ctx.outputDir);
            TestIsosurfaceExtraction(ctx.inputPath, ctx.outputDir);
            TestMPR(ctx.inputPath, ctx.outputDir);
            TestIsotropicResample(ctx.inputPath, ctx.outputDir);
            TestThresholdMask(ctx.inputPath, ctx.outputDir);
            TestConnectivityLabels(ctx.inputPath, ctx.outputDir);
            TestMaximumIntensityProjection(ctx.inputPath, ctx.outputDir);
            TestVolumeStatistics(ctx.inputPath, ctx.outputDir);
            TestMetadataExport(ctx.inputPath, ctx.outputDir);
            TestViewerSnapshot(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "vtk:export",
        "VTK",
        "Convert to VTI volume",
        [](const CommandContext& ctx) {
            TestImageExport(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "vtk:nifti",
        "VTK",
        "Export to NIfTI (.nii.gz) for interoperability",
        [](const CommandContext& ctx) {
            TestNiftiExport(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "vtk:isosurface",
        "VTK",
        "Generate STL mesh with marching cubes",
        [](const CommandContext& ctx) {
            TestIsosurfaceExtraction(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "vtk:resample",
        "VTK",
        "Resample to isotropic spacing (1mm)",
        [](const CommandContext& ctx) {
            TestIsotropicResample(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "vtk:mask",
        "VTK",
        "Binary threshold to create a segmentation mask",
        [](const CommandContext& ctx) {
            TestThresholdMask(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "vtk:connectivity",
        "VTK",
        "Label connected components after thresholding",
        [](const CommandContext& ctx) {
            TestConnectivityLabels(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "vtk:mip",
        "VTK",
        "Maximum intensity projection to PNG",
        [](const CommandContext& ctx) {
            TestMaximumIntensityProjection(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "vtk:metadata",
        "VTK",
        "Export patient/study metadata to text",
        [](const CommandContext& ctx) {
            TestMetadataExport(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "vtk:stats",
        "VTK",
        "Compute volume statistics (min/max/mean/stddev)",
        [](const CommandContext& ctx) {
            TestVolumeStatistics(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "vtk:viewer",
        "VTK",
        "Capture a vtkImageViewer2 slice as PNG",
        [](const CommandContext& ctx) {
            TestViewerSnapshot(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });
}

#else
void VTKTests::RegisterCommands(CommandRegistry&) {}
#endif
