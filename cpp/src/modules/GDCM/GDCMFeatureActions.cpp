//
// GDCMFeatureActions.cpp
// DicomToolsCpp
//
// Implements GDCM-driven feature demos like anonymization, UID rewrites, codec transcodes, previews, and directory scans.
//
// Thales Matheus Mendonça Santos - November 2025

#include "GDCMFeatureActions.h"

#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <vector>
#include <set>
#include <sstream>

#ifdef USE_GDCM
#include "gdcmAnonymizer.h"
#include "gdcmAttribute.h"
#include "gdcmDataElement.h"
#include "gdcmDirectory.h"
#include "gdcmDefs.h"
#include "gdcmGlobal.h"
#include "gdcmImageChangeTransferSyntax.h"
#include "gdcmImageReader.h"
#include "gdcmImageWriter.h"
#include "gdcmReader.h"
#include "gdcmSequenceOfItems.h"
#include "gdcmScanner.h"
#include "gdcmStringFilter.h"
#include "gdcmUIDs.h"
#include "gdcmUIDGenerator.h"
#include "gdcmWriter.h"
#include "gdcmPrinter.h"

namespace fs = std::filesystem;

namespace {
// Tiny helper to keep file paths readable
std::string JoinPath(const std::string& base, const std::string& name) {
    return (fs::path(base) / name).string();
}

struct PixelStats {
    // Minimal statistics used for QA when exporting numeric reports
    double min{0.0};
    double max{0.0};
    double mean{0.0};
    std::size_t count{0};
};

template <typename T>
PixelStats CalculateStats(const std::vector<char>& buffer) {
    // Interpret the buffer as type T and compute min/max/mean
    PixelStats stats;
    const auto* data = reinterpret_cast<const T*>(buffer.data());
    const std::size_t count = buffer.size() / sizeof(T);
    if (count == 0) {
        return stats;
    }

    T minVal = std::numeric_limits<T>::max();
    T maxVal = std::numeric_limits<T>::lowest();
    long double sum = 0.0;
    for (std::size_t i = 0; i < count; ++i) {
        T value = data[i];
        minVal = std::min(minVal, value);
        maxVal = std::max(maxVal, value);
        sum += value;
    }

    stats.count = count;
    stats.min = static_cast<double>(minVal);
    stats.max = static_cast<double>(maxVal);
    stats.mean = static_cast<double>(sum / static_cast<long double>(count));
    return stats;
}

template <typename T>
bool WritePGMPreview(const gdcm::Image& image, const std::vector<char>& buffer, const std::string& outPath) {
    // Create a simple 8-bit preview from the first channel of the volume
    const unsigned int width = image.GetDimension(0);
    const unsigned int height = image.GetDimension(1);
    const unsigned int samplesPerPixel = image.GetPixelFormat().GetSamplesPerPixel();
    const std::size_t pixelsPerSlice = static_cast<std::size_t>(width) * static_cast<std::size_t>(height);
    const std::size_t valuesPerSlice = pixelsPerSlice * static_cast<std::size_t>(samplesPerPixel);

    if (buffer.size() < valuesPerSlice * sizeof(T) || width == 0 || height == 0) {
        return false;
    }

    const T* data = reinterpret_cast<const T*>(buffer.data());
    double minVal = std::numeric_limits<double>::max();
    double maxVal = std::numeric_limits<double>::lowest();
    for (std::size_t i = 0; i < valuesPerSlice; i += samplesPerPixel) {
        const double value = static_cast<double>(data[i]); // take first channel if RGB
        minVal = std::min(minVal, value);
        maxVal = std::max(maxVal, value);
    }

    if (maxVal <= minVal) {
        maxVal = minVal + 1.0;
    }

    std::vector<uint8_t> preview(pixelsPerSlice, 0);
    for (std::size_t i = 0; i < valuesPerSlice; i += samplesPerPixel) {
        const double value = static_cast<double>(data[i]);
        const double normalized = (value - minVal) / (maxVal - minVal);
        preview[i / samplesPerPixel] = static_cast<uint8_t>(std::clamp(normalized, 0.0, 1.0) * 255.0);
    }

    std::ofstream out(outPath, std::ios::binary | std::ios::out | std::ios::trunc);
    if (!out.is_open()) {
        return false;
    }

    out << "P5\n" << width << " " << height << "\n255\n";
    out.write(reinterpret_cast<const char*>(preview.data()), static_cast<std::streamsize>(preview.size()));
    return out.good();
}
} // namespace

#include "GDCMFeatureActions_Core.inc"
#include "GDCMFeatureActions_Codecs.inc"
#include "GDCMFeatureActions_Pixel.inc"
#include "GDCMFeatureActions_Directory.inc"
#include "GDCMFeatureActions_Metadata.inc"

#else
namespace GDCMTests {
void TestTagInspection(const std::string&, const std::string&) { std::cout << "GDCM not enabled." << std::endl; }
void TestAnonymization(const std::string&, const std::string&) {}
void TestDecompression(const std::string&, const std::string&) {}
void TestUIDRewrite(const std::string&, const std::string&) {}
void TestDatasetDump(const std::string&, const std::string&) {}
void TestJPEG2000Transcode(const std::string&, const std::string&) {}
void TestRLETranscode(const std::string&, const std::string&) {}
void TestPixelStatistics(const std::string&, const std::string&) {}
void TestJPEGLSTranscode(const std::string&, const std::string&) {}
void TestDirectoryScan(const std::string&, const std::string&) {}
void TestPreviewExport(const std::string&, const std::string&) {}
void TestSequenceEditing(const std::string&, const std::string&) {}
void TestDicomdirRead(const std::string&, const std::string&) {}
void TestStringFilterCharsets(const std::string&, const std::string&) {}
void TestRTStructRead(const std::string&, const std::string&) {}
void TestJPEG2000Lossy(const std::string&, const std::string&) {}
void TestRLEPlanarConfiguration(const std::string&, const std::string&) {}
void TestJPEGBaselineTranscode(const std::string&, const std::string&) {}
void TestJPEGLosslessP14Transcode(const std::string&, const std::string&) {}
} // namespace GDCMTests
#endif
