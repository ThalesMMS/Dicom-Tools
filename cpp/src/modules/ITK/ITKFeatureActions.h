//
// ITKFeatureActions.h
// DicomToolsCpp
//
// Declares ITK feature demos for filtering, segmentation, resampling, and volume export.
//
// Thales Matheus Mendonça Santos - November 2025

#pragma once

#include <string>

namespace ITKTests {
    // Individual ITK processing demos exposed as CLI commands
    void TestCannyEdgeDetection(const std::string& filename, const std::string& outputDir);
    void TestGaussianSmoothing(const std::string& filename, const std::string& outputDir);
    void TestBinaryThresholding(const std::string& filename, const std::string& outputDir);
    void TestResampling(const std::string& filename, const std::string& outputDir);
    void TestAdaptiveHistogram(const std::string& filename, const std::string& outputDir);
    void TestSliceExtraction(const std::string& filename, const std::string& outputDir);
    void TestMedianFilter(const std::string& filename, const std::string& outputDir);
    void TestNRRDExport(const std::string& filename, const std::string& outputDir);
    void TestOtsuSegmentation(const std::string& filename, const std::string& outputDir);
    void TestConnectedThreshold(const std::string& filename, const std::string& outputDir);
    void TestAnisotropicDenoise(const std::string& filename, const std::string& outputDir);
    void TestMaximumIntensityProjection(const std::string& filename, const std::string& outputDir);
    void TestNiftiExport(const std::string& filename, const std::string& outputDir);
    void TestDistanceMapAndMorphology(const std::string& filename, const std::string& outputDir);
    void TestLabelStatistics(const std::string& filename, const std::string& outputDir);
    void TestRegistration(const std::string& filename, const std::string& outputDir);
    void TestMutualInformationRegistration(const std::string& filename, const std::string& outputDir);
    void TestVectorVolumeExport(const std::string& filename, const std::string& outputDir);
    void TestDicomSeriesWrite(const std::string& filename, const std::string& outputDir);
}
