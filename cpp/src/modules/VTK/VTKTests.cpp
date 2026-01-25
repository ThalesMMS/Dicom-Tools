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
            TestVolumeRenderingSnapshot(ctx.inputPath, ctx.outputDir);
            TestMultiVolumeFusion(ctx.inputPath, ctx.outputDir);
            TestTimeSeries(ctx.inputPath, ctx.outputDir);
            TestMultiplanarMPR(ctx.inputPath, ctx.outputDir);
            TestMaskOverlay(ctx.inputPath, ctx.outputDir);
            TestLabelmapSurface(ctx.inputPath, ctx.outputDir);
            TestStreamingReslice(ctx.inputPath, ctx.outputDir);
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

    registry.Register({
        "vtk:volume-render",
        "VTK",
        "Off-screen volume rendering snapshot via vtkSmartVolumeMapper",
        [](const CommandContext& ctx) {
            TestVolumeRenderingSnapshot(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "vtk:fusion",
        "VTK",
        "Blend two volumes (PET/CT style) into a fused PNG",
        [](const CommandContext& ctx) {
            TestMultiVolumeFusion(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "vtk:time-series",
        "VTK",
        "Inspect time dimension/spacing for 4D series",
        [](const CommandContext& ctx) {
            TestTimeSeries(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "vtk:mpr-multi",
        "VTK",
        "Generate sagittal, coronal, and oblique MPR PNGs",
        [](const CommandContext& ctx) {
            TestMultiplanarMPR(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "vtk:overlay",
        "VTK",
        "Create a HU threshold mask overlay on an axial slice",
        [](const CommandContext& ctx) {
            TestMaskOverlay(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "vtk:label-surface",
        "VTK",
        "Threshold into a labelmap and export an STL surface + stats",
        [](const CommandContext& ctx) {
            TestLabelmapSurface(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "vtk:stream",
        "VTK",
        "Stream volume in Z-chunks using update extents (memory-friendly)",
        [](const CommandContext& ctx) {
            TestStreamingReslice(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });
}

#else
void VTKTests::RegisterCommands(CommandRegistry&) {}
#endif
