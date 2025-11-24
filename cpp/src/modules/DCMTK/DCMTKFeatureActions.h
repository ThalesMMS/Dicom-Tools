//
// DCMTKFeatureActions.h
// DicomToolsCpp
//
// Declares the DCMTK-based feature demonstrations invoked by CLI commands to exercise codec and metadata APIs.
//
// Thales Matheus Mendonça Santos - November 2025

#pragma once

#include <string>

namespace DCMTKTests {
    // Individual feature demos executed by CLI commands; implementations live in the .cpp file
    void TestPixelDataExtraction(const std::string& filename, const std::string& outputDir);
    void TestDICOMDIRGeneration(const std::string& directory, const std::string& outputDir);
    void TestTagModification(const std::string& filename, const std::string& outputDir);
    void TestLosslessJPEGReencode(const std::string& filename, const std::string& outputDir);
    void TestRawDump(const std::string& filename, const std::string& outputDir);
    void TestExplicitVRRewrite(const std::string& filename, const std::string& outputDir);
    void TestMetadataReport(const std::string& filename, const std::string& outputDir);
    void TestRLEReencode(const std::string& filename, const std::string& outputDir);
    void TestJPEGBaseline(const std::string& filename, const std::string& outputDir);
    void TestBMPPreview(const std::string& filename, const std::string& outputDir);
    void TestSegmentationExport(const std::string& filename, const std::string& outputDir);
}
