//
// VTKFeatureActions.h
// DicomToolsCpp
//
// Declares VTK-based feature demonstrations for IO, resampling, masking, statistics, and lightweight visualizations.
//
// Thales Matheus Mendonça Santos - November 2025

#pragma once

#include <string>

namespace VTKTests {
    // VTK-based demonstrations of volume IO, resampling, and basic visualization
    void TestImageExport(const std::string& filename, const std::string& outputDir);
    void TestIsosurfaceExtraction(const std::string& filename, const std::string& outputDir);
    void TestMPR(const std::string& filename, const std::string& outputDir);
    void TestThresholdMask(const std::string& filename, const std::string& outputDir);
    void TestMetadataExport(const std::string& filename, const std::string& outputDir);
    void TestNiftiExport(const std::string& filename, const std::string& outputDir);
    void TestVolumeStatistics(const std::string& filename, const std::string& outputDir);
    void TestIsotropicResample(const std::string& filename, const std::string& outputDir);
    void TestMaximumIntensityProjection(const std::string& filename, const std::string& outputDir);
    void TestConnectivityLabels(const std::string& filename, const std::string& outputDir);
    void TestViewerSnapshot(const std::string& filename, const std::string& outputDir);
}
