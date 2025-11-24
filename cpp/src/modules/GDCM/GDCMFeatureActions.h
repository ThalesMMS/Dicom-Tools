//
// GDCMFeatureActions.h
// DicomToolsCpp
//
// Declares GDCM-based demonstrations for anonymization, transcoding, previews, and metadata scanning.
//
// Thales Matheus Mendonça Santos - November 2025

#pragma once

#include <string>

namespace GDCMTests {
    // Self-contained demonstrations of core GDCM capabilities
    void TestTagInspection(const std::string& filename, const std::string& outputDir);
    void TestAnonymization(const std::string& filename, const std::string& outputDir);
    void TestDecompression(const std::string& filename, const std::string& outputDir);
    void TestUIDRewrite(const std::string& filename, const std::string& outputDir);
    void TestDatasetDump(const std::string& filename, const std::string& outputDir);
    void TestJPEG2000Transcode(const std::string& filename, const std::string& outputDir);
    void TestRLETranscode(const std::string& filename, const std::string& outputDir);
    void TestPixelStatistics(const std::string& filename, const std::string& outputDir);
    void TestJPEGLSTranscode(const std::string& filename, const std::string& outputDir);
    void TestDirectoryScan(const std::string& path, const std::string& outputDir);
    void TestPreviewExport(const std::string& filename, const std::string& outputDir);
}
