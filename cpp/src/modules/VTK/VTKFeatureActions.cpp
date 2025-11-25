//
// VTKFeatureActions.cpp
// DicomToolsCpp
//
// Implements VTK-driven demos for exporting volumes, resampling, marching cubes, projections, metadata, and statistics.
//
// Thales Matheus Mendonça Santos - November 2025

#include "VTKFeatureActions.h"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

#ifdef USE_VTK
#include "vtkDICOMImageReader.h"
#include "vtkColorTransferFunction.h"
#include "vtkDiscreteMarchingCubes.h"
#include "vtkExtractVOI.h"
#include "vtkImageAccumulate.h"
#include "vtkImageBlend.h"
#include "vtkImageConnectivityFilter.h"
#include "vtkImageData.h"
#include "vtkImageMapToColors.h"
#include "vtkImageMapToWindowLevelColors.h"
#include "vtkImageResample.h"
#include "vtkImageReslice.h"
#include "vtkImageShiftScale.h"
#include "vtkImageSlabReslice.h"
#include "vtkImageThreshold.h"
#include "vtkImageViewer2.h"
#include "vtkInformation.h"
#include "vtkLookupTable.h"
#include "vtkMarchingCubes.h"
#include "vtkMatrix4x4.h"
#include "vtkNIFTIImageWriter.h"
#include "vtkNew.h"
#include "vtkPNGWriter.h"
#include "vtkPiecewiseFunction.h"
#include "vtkRenderWindow.h"
#include "vtkRenderer.h"
#include "vtkSmartPointer.h"
#include "vtkSmartVolumeMapper.h"
#include "vtkSTLWriter.h"
#include "vtkStreamingDemandDrivenPipeline.h"
#include "vtkTriangleFilter.h"
#include "vtkVolume.h"
#include "vtkVolumeProperty.h"
#include "vtkWindowToImageFilter.h"
#include "vtkXMLImageDataWriter.h"

namespace fs = std::filesystem;

namespace {
// Keep path concatenation tidy across the file outputs
std::string JoinPath(const std::string& base, const std::string& filename) {
    return (fs::path(base) / filename).string();
}

// If a single file path is provided, VTK needs the enclosing directory to read the series
std::string ResolveSeriesDirectory(const std::string& path) {
    if (fs::is_directory(path)) {
        return path;
    }
    return fs::path(path).parent_path().string();
}
} // namespace

#include "VTKFeatureActions_IO.inc"
#include "VTKFeatureActions_Resample.inc"
#include "VTKFeatureActions_Advanced.inc"

#else
namespace VTKTests {
void TestImageExport(const std::string&, const std::string&) { std::cout << "VTK not enabled." << std::endl; }
void TestIsosurfaceExtraction(const std::string&, const std::string&) {}
void TestMPR(const std::string&, const std::string&) {}
void TestThresholdMask(const std::string&, const std::string&) {}
void TestMetadataExport(const std::string&, const std::string&) {}
void TestNiftiExport(const std::string&, const std::string&) {}
void TestVolumeStatistics(const std::string&, const std::string&) {}
void TestIsotropicResample(const std::string&, const std::string&) {}
void TestMaximumIntensityProjection(const std::string&, const std::string&) {}
void TestConnectivityLabels(const std::string&, const std::string&) {}
void TestViewerSnapshot(const std::string&, const std::string&) {}
void TestVolumeRenderingSnapshot(const std::string&, const std::string&) {}
void TestMultiVolumeFusion(const std::string&, const std::string&) {}
void TestTimeSeries(const std::string&, const std::string&) {}
void TestMultiplanarMPR(const std::string&, const std::string&) {}
void TestMaskOverlay(const std::string&, const std::string&) {}
void TestLabelmapSurface(const std::string&, const std::string&) {}
void TestStreamingReslice(const std::string&, const std::string&) {}
} // namespace VTKTests
#endif
