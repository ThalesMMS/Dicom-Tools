//
// ITKTests.cpp
// DicomToolsCpp
//
// Registers ITK feature commands and maps them to concrete processing demonstrations.
//
// Thales Matheus Mendonça Santos - November 2025

#include "ITKTestInterface.h"

#include "ITKFeatureActions.h"
#include "cli/CommandRegistry.h"

#ifdef USE_ITK

void ITKTests::RegisterCommands(CommandRegistry& registry) {
    // Composite command that exercises every ITK demonstration in sequence
    registry.Register({
        "test-itk",
        "ITK",
        "Run all ITK feature tests",
        [](const CommandContext& ctx) {
            TestCannyEdgeDetection(ctx.inputPath, ctx.outputDir);
            TestGaussianSmoothing(ctx.inputPath, ctx.outputDir);
            TestMedianFilter(ctx.inputPath, ctx.outputDir);
            TestBinaryThresholding(ctx.inputPath, ctx.outputDir);
            TestOtsuSegmentation(ctx.inputPath, ctx.outputDir);
            TestConnectedThreshold(ctx.inputPath, ctx.outputDir);
            TestResampling(ctx.inputPath, ctx.outputDir);
            TestAnisotropicDenoise(ctx.inputPath, ctx.outputDir);
            TestAdaptiveHistogram(ctx.inputPath, ctx.outputDir);
            TestSliceExtraction(ctx.inputPath, ctx.outputDir);
            TestMaximumIntensityProjection(ctx.inputPath, ctx.outputDir);
            TestNRRDExport(ctx.inputPath, ctx.outputDir);
            TestNiftiExport(ctx.inputPath, ctx.outputDir);
            TestDistanceMapAndMorphology(ctx.inputPath, ctx.outputDir);
            TestLabelStatistics(ctx.inputPath, ctx.outputDir);
            TestRegistration(ctx.inputPath, ctx.outputDir);
            TestMutualInformationRegistration(ctx.inputPath, ctx.outputDir);
            TestVectorVolumeExport(ctx.inputPath, ctx.outputDir);
            TestDicomSeriesWrite(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "itk:canny",
        "ITK",
        "Run 3D canny edge detection and write DICOM",
        [](const CommandContext& ctx) {
            TestCannyEdgeDetection(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "itk:gaussian",
        "ITK",
        "3D Gaussian smoothing",
        [](const CommandContext& ctx) {
            TestGaussianSmoothing(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "itk:threshold",
        "ITK",
        "Binary threshold segmentation",
        [](const CommandContext& ctx) {
            TestBinaryThresholding(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "itk:otsu",
        "ITK",
        "Automatic Otsu segmentation",
        [](const CommandContext& ctx) {
            TestOtsuSegmentation(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "itk:connected-threshold",
        "ITK",
        "Region-growing segmentation using ConnectedThresholdImageFilter",
        [](const CommandContext& ctx) {
            TestConnectedThreshold(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "itk:resample",
        "ITK",
        "Resample to isotropic spacing (1mm) using linear interpolation",
        [](const CommandContext& ctx) {
            TestResampling(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "itk:aniso",
        "ITK",
        "Curvature anisotropic diffusion denoising",
        [](const CommandContext& ctx) {
            TestAnisotropicDenoise(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "itk:histogram",
        "ITK",
        "Adaptive histogram equalization for contrast boost",
        [](const CommandContext& ctx) {
            TestAdaptiveHistogram(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "itk:mip",
        "ITK",
        "Axial maximum intensity projection saved as PNG",
        [](const CommandContext& ctx) {
            TestMaximumIntensityProjection(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "itk:slice",
        "ITK",
        "Extract middle axial slice to PNG",
        [](const CommandContext& ctx) {
            TestSliceExtraction(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "itk:median",
        "ITK",
        "Median smoothing for salt-and-pepper noise removal",
        [](const CommandContext& ctx) {
            TestMedianFilter(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "itk:nrrd",
        "ITK",
        "Export the volume to NRRD for interchange",
        [](const CommandContext& ctx) {
            TestNRRDExport(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "itk:nifti",
        "ITK",
        "Export the volume to NIfTI (.nii.gz)",
        [](const CommandContext& ctx) {
            TestNiftiExport(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "itk:distance-map",
        "ITK",
        "Compute a signed distance map and basic morphological closing",
        [](const CommandContext& ctx) {
            TestDistanceMapAndMorphology(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "itk:label-stats",
        "ITK",
        "Connected components + label statistics report",
        [](const CommandContext& ctx) {
            TestLabelStatistics(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "itk:register",
        "ITK",
        "Estimate translation via MI registration and resample moving volume",
        [](const CommandContext& ctx) {
            TestRegistration(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "itk:register-mi",
        "ITK",
        "Mutual information registration with affine transform (multi-res)",
        [](const CommandContext& ctx) {
            TestMutualInformationRegistration(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "itk:vector",
        "ITK",
        "Compose a 2-component vector volume and export as NRRD",
        [](const CommandContext& ctx) {
            TestVectorVolumeExport(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });

    registry.Register({
        "itk:dicom-series",
        "ITK",
        "Write a new DICOM series with fresh UIDs",
        [](const CommandContext& ctx) {
            TestDicomSeriesWrite(ctx.inputPath, ctx.outputDir);
            return 0;
        }
    });
}

#else
void ITKTests::RegisterCommands(CommandRegistry&) {}
#endif
