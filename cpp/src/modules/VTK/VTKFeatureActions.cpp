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

#ifdef USE_VTK
#include "vtkDICOMImageReader.h"
#include "vtkImageAccumulate.h"
#include "vtkImageConnectivityFilter.h"
#include "vtkImageData.h"
#include "vtkImageReslice.h"
#include "vtkImageResample.h"
#include "vtkImageShiftScale.h"
#include "vtkImageThreshold.h"
#include "vtkImageSlabReslice.h"
#include "vtkImageViewer2.h"
#include "vtkMarchingCubes.h"
#include "vtkNew.h"
#include "vtkNIFTIImageWriter.h"
#include "vtkPNGWriter.h"
#include "vtkRenderWindow.h"
#include "vtkSmartPointer.h"
#include "vtkSTLWriter.h"
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
}

void VTKTests::TestImageExport(const std::string& filename, const std::string& outputDir) {
    // Read a series and serialize it to VTK's VTI format
    std::cout << "--- [VTK] Image Export ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetFileName(filename.c_str());
    reader->Update();

    int* dims = reader->GetOutput()->GetDimensions();
    std::cout << "Dimensions: " << dims[0] << " x " << dims[1] << " x " << dims[2] << std::endl;

    vtkNew<vtkXMLImageDataWriter> writer;
    writer->SetFileName(JoinPath(outputDir, "vtk_export.vti").c_str());
    writer->SetInputData(reader->GetOutput());
    writer->Write();
    std::cout << "Saved to '" << writer->GetFileName() << "'" << std::endl;
}

void VTKTests::TestNiftiExport(const std::string& filename, const std::string& outputDir) {
    // Export the loaded series directly to compressed NIfTI
    std::cout << "--- [VTK] NIfTI Export ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    vtkNew<vtkNIFTIImageWriter> writer;
    writer->SetFileName(JoinPath(outputDir, "vtk_volume.nii.gz").c_str());
    writer->SetInputConnection(reader->GetOutputPort());
    writer->Write();

    std::cout << "Saved to '" << writer->GetFileName() << "'" << std::endl;
}

void VTKTests::TestIsosurfaceExtraction(const std::string& filename, const std::string& outputDir) {
    // Run marching cubes on the CT volume to produce a quick STL mesh
    std::cout << "--- [VTK] Isosurface Extraction (Marching Cubes) ---" << std::endl;
    
    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();
    
    vtkNew<vtkMarchingCubes> surface;
    surface->SetInputConnection(reader->GetOutputPort());
    surface->ComputeNormalsOn();
    surface->ComputeGradientsOn();
    surface->SetValue(0, 500);

    vtkNew<vtkSTLWriter> writer;
    writer->SetFileName(JoinPath(outputDir, "vtk_isosurface.stl").c_str());
    writer->SetInputConnection(surface->GetOutputPort());
    writer->Write();
    
    std::cout << "Saved to '" << writer->GetFileName() << "'" << std::endl;
}

void VTKTests::TestMPR(const std::string& filename, const std::string& outputDir) {
    // Slice through the volume center and export a single MPR PNG
    std::cout << "--- [VTK] MPR (Single Slice Export) ---" << std::endl;
    
    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();
    
    double* center = reader->GetOutput()->GetCenter();
    double* range = reader->GetOutput()->GetScalarRange();
    
    vtkNew<vtkImageReslice> reslice;
    reslice->SetInputConnection(reader->GetOutputPort());
    reslice->SetOutputDimensionality(2);
    reslice->SetResliceAxesOrigin(center[0], center[1], center[2]);
    
    vtkNew<vtkImageShiftScale> shiftScale;
    shiftScale->SetInputConnection(reslice->GetOutputPort());
    shiftScale->SetShift(-range[0]);
    shiftScale->SetScale(255.0 / (range[1] - range[0]));
    shiftScale->SetOutputScalarTypeToUnsignedChar();
    
    vtkNew<vtkPNGWriter> writer;
    writer->SetFileName(JoinPath(outputDir, "vtk_mpr_slice.png").c_str());
    writer->SetInputConnection(shiftScale->GetOutputPort());
    writer->Write();
    
    std::cout << "Saved to '" << writer->GetFileName() << "'" << std::endl;
}

void VTKTests::TestThresholdMask(const std::string& filename, const std::string& outputDir) {
    // Create a binary mask with a simple HU window and save as VTI
    std::cout << "--- [VTK] Threshold Mask ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    vtkNew<vtkImageThreshold> threshold;
    threshold->SetInputConnection(reader->GetOutputPort());
    threshold->ThresholdBetween(300, 3000);
    threshold->SetInValue(1);
    threshold->SetOutValue(0);
    threshold->SetOutputScalarTypeToUnsignedChar();

    vtkNew<vtkXMLImageDataWriter> writer;
    writer->SetFileName(JoinPath(outputDir, "vtk_threshold_mask.vti").c_str());
    writer->SetInputConnection(threshold->GetOutputPort());
    writer->Write();

    std::cout << "Saved binary mask to '" << writer->GetFileName() << "'" << std::endl;
}

void VTKTests::TestVolumeStatistics(const std::string& filename, const std::string& outputDir) {
    // Compute histogram-driven stats for a CT volume and persist to text
    std::cout << "--- [VTK] Volume Statistics ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    double scalarRange[2];
    reader->GetOutput()->GetScalarRange(scalarRange);
    const int minBin = static_cast<int>(std::floor(scalarRange[0]));
    const int maxBin = static_cast<int>(std::ceil(scalarRange[1]));
    const int extent = std::max(1, std::min(8192, maxBin - minBin + 1));

    vtkNew<vtkImageAccumulate> hist;
    hist->SetInputConnection(reader->GetOutputPort());
    hist->SetComponentExtent(0, extent - 1, 0, 0, 0, 0);
    hist->SetComponentOrigin(minBin, 0, 0);
    hist->SetComponentSpacing(1, 1, 1);
    hist->IgnoreZeroOn();
    hist->Update();

    const double minValue = hist->GetMin()[0];
    const double maxValue = hist->GetMax()[0];
    const double meanValue = hist->GetMean()[0];
    const double stddevValue = hist->GetStandardDeviation()[0];

    std::string outFile = JoinPath(outputDir, "vtk_stats.txt");
    std::ofstream out(outFile, std::ios::out | std::ios::trunc);
    if (!out.is_open()) {
        std::cerr << "Failed to open stats output: " << outFile << std::endl;
        return;
    }

    int* dims = reader->GetOutput()->GetDimensions();
    out << "Dimensions=" << dims[0] << "x" << dims[1] << "x" << dims[2] << "\n";
    out << "Range=[" << minValue << ", " << maxValue << "]\n";
    out << "Mean=" << meanValue << "\n";
    out << "StdDev=" << stddevValue << "\n";
    out.close();

    std::cout << "Wrote stats to '" << outFile << "'" << std::endl;
}

void VTKTests::TestMetadataExport(const std::string& filename, const std::string& outputDir) {
    // Grab common DICOM metadata fields from the VTK reader and log them
    std::cout << "--- [VTK] Metadata Export ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    std::string outFile = JoinPath(outputDir, "vtk_metadata.txt");
    std::ofstream out(outFile, std::ios::out | std::ios::trunc);
    if (!out.is_open()) {
        std::cerr << "Failed to open metadata output: " << outFile << std::endl;
        return;
    }

    int* dims = reader->GetOutput()->GetDimensions();
    double spacing[3];
    reader->GetOutput()->GetSpacing(spacing);
    float* origin = reader->GetImagePositionPatient();
    float* orientation = reader->GetImageOrientationPatient();

    out << "PatientName: " << (reader->GetPatientName() ? reader->GetPatientName() : "") << "\n";
    out << "StudyInstanceUID: " << (reader->GetStudyUID() ? reader->GetStudyUID() : "") << "\n";
    out << "StudyID: " << (reader->GetStudyID() ? reader->GetStudyID() : "") << "\n";
    out << "TransferSyntaxUID: " << (reader->GetTransferSyntaxUID() ? reader->GetTransferSyntaxUID() : "") << "\n";
    out << "Dimensions: " << dims[0] << "x" << dims[1] << "x" << dims[2] << "\n";
    out << "Spacing: " << spacing[0] << "x" << spacing[1] << "x" << spacing[2] << "\n";
    out << "Origin: " << origin[0] << "," << origin[1] << "," << origin[2] << "\n";
    out << "Orientation: ";
    if (orientation) {
        out << orientation[0] << "," << orientation[1] << "," << orientation[2] << ","
            << orientation[3] << "," << orientation[4] << "," << orientation[5] << "\n";
    } else {
        out << "\n";
    }
    out.close();

    std::cout << "Wrote metadata summary to '" << outFile << "'" << std::endl;
}

void VTKTests::TestIsotropicResample(const std::string& filename, const std::string& outputDir) {
    // Resample the volume to 1mm spacing and export as VTI
    std::cout << "--- [VTK] Isotropic Resample ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    double* originalSpacing = reader->GetOutput()->GetSpacing();

    vtkNew<vtkImageResample> resample;
    resample->SetInputConnection(reader->GetOutputPort());
    resample->SetAxisOutputSpacing(0, 1.0);
    resample->SetAxisOutputSpacing(1, 1.0);
    resample->SetAxisOutputSpacing(2, 1.0);
    resample->SetInterpolationModeToLinear();
    resample->Update();

    vtkNew<vtkXMLImageDataWriter> writer;
    writer->SetFileName(JoinPath(outputDir, "vtk_resampled.vti").c_str());
    writer->SetInputConnection(resample->GetOutputPort());
    writer->Write();

    double* newSpacing = resample->GetOutput()->GetSpacing();
    std::cout << "Resampled spacing " << originalSpacing[0] << "x" << originalSpacing[1] << "x" << originalSpacing[2]
              << " -> " << newSpacing[0] << "x" << newSpacing[1] << "x" << newSpacing[2]
              << " and saved to '" << writer->GetFileName() << "'" << std::endl;
}

void VTKTests::TestMaximumIntensityProjection(const std::string& filename, const std::string& outputDir) {
    // Generate an axial MIP with a small slab thickness and export to PNG
    std::cout << "--- [VTK] Maximum Intensity Projection ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    double range[2];
    reader->GetOutput()->GetScalarRange(range);
    double center[3];
    reader->GetOutput()->GetCenter(center);
    double spacing[3];
    reader->GetOutput()->GetSpacing(spacing);

    vtkNew<vtkImageSlabReslice> slab;
    slab->SetInputConnection(reader->GetOutputPort());
    slab->SetBlendModeToMax();
    slab->SetSlabThickness(std::max(1.0, spacing[2] * 8.0));
    slab->SetSlabResolution(spacing[2]);
    slab->SetOutputDimensionality(2);
    slab->SetResliceAxesDirectionCosines(1, 0, 0, 0, 1, 0, 0, 0, 1);
    slab->SetResliceAxesOrigin(center);

    vtkNew<vtkImageShiftScale> shiftScale;
    shiftScale->SetInputConnection(slab->GetOutputPort());
    shiftScale->SetShift(-range[0]);
    shiftScale->SetScale(255.0 / std::max(1.0, range[1] - range[0]));
    shiftScale->SetOutputScalarTypeToUnsignedChar();

    vtkNew<vtkPNGWriter> writer;
    writer->SetFileName(JoinPath(outputDir, "vtk_mip.png").c_str());
    writer->SetInputConnection(shiftScale->GetOutputPort());
    writer->Write();

    std::cout << "Saved axial MIP PNG to '" << writer->GetFileName() << "'" << std::endl;
}

void VTKTests::TestConnectivityLabels(const std::string& filename, const std::string& outputDir) {
    // Label connected regions in a thresholded volume to exercise vtkImageConnectivityFilter
    std::cout << "--- [VTK] Connected Components ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    vtkNew<vtkImageThreshold> threshold;
    threshold->SetInputConnection(reader->GetOutputPort());
    threshold->ThresholdBetween(150, 3000);
    threshold->SetInValue(1);
    threshold->SetOutValue(0);
    threshold->SetOutputScalarTypeToUnsignedChar();

    vtkNew<vtkImageConnectivityFilter> connectivity;
    connectivity->SetInputConnection(threshold->GetOutputPort());
    connectivity->SetExtractionModeToAllRegions();
    connectivity->SetLabelModeToSizeRank();
    connectivity->SetLabelScalarTypeToUnsignedShort();
    connectivity->GenerateRegionExtentsOn();
    connectivity->Update();

    vtkNew<vtkXMLImageDataWriter> writer;
    writer->SetFileName(JoinPath(outputDir, "vtk_connectivity_mask.vti").c_str());
    writer->SetInputConnection(connectivity->GetOutputPort());
    writer->Write();

    std::cout << "Labeled " << connectivity->GetNumberOfExtractedRegions()
              << " connected region(s) and saved to '" << writer->GetFileName() << "'" << std::endl;
}

void VTKTests::TestViewerSnapshot(const std::string& filename, const std::string& outputDir) {
    // Render a middle slice via vtkImageViewer2 and capture an off-screen PNG
    std::cout << "--- [VTK] ImageViewer2 Snapshot ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    int extent[6];
    reader->GetOutput()->GetExtent(extent);
    const int midSlice = (extent[4] + extent[5]) / 2;

    vtkNew<vtkImageViewer2> viewer;
    viewer->SetInputConnection(reader->GetOutputPort());
    viewer->SetSlice(midSlice);
    viewer->GetRenderWindow()->SetOffScreenRendering(1);
    viewer->Render();

    vtkNew<vtkWindowToImageFilter> capture;
    capture->SetInput(viewer->GetRenderWindow());
    capture->SetInputBufferTypeToRGB();
    capture->ReadFrontBufferOff();
    capture->Update();

    vtkNew<vtkPNGWriter> writer;
    writer->SetFileName(JoinPath(outputDir, "vtk_viewer_slice.png").c_str());
    writer->SetInputConnection(capture->GetOutputPort());
    writer->Write();

    std::cout << "Captured viewer slice " << midSlice << " to '" << writer->GetFileName() << "'" << std::endl;
}

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
} // namespace VTKTests
#endif
