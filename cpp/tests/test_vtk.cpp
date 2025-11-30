//
// test_vtk.cpp
// DicomToolsCpp
//
// Unit tests for VTK library features including DICOM reading, image processing,
// surface extraction, rendering primitives, and volume statistics.
//
// Thales Matheus Mendonça Santos - November 2025

#include "test_framework.h"

#include <filesystem>
#include <fstream>
#include <cmath>

#ifdef USE_VTK
#include <vtkSmartPointer.h>
#include <vtkNew.h>
#include <vtkVersion.h>
#include <vtkDICOMImageReader.h>
#include <vtkImageData.h>
#include <vtkImageCast.h>
#include <vtkImageThreshold.h>
#include <vtkImageGaussianSmooth.h>
#include <vtkImageMedian3D.h>
#include <vtkImageReslice.h>
#include <vtkImageResample.h>
#include <vtkMarchingCubes.h>
#include <vtkContourFilter.h>
#include <vtkPolyData.h>
#include <vtkSTLWriter.h>
#include <vtkXMLImageDataWriter.h>
#include <vtkNIFTIImageWriter.h>
#include <vtkPNGWriter.h>
#include <vtkImageShiftScale.h>
#include <vtkImageExtractComponents.h>
#include <vtkImageFlip.h>
#include <vtkImagePermute.h>
#include <vtkMatrix4x4.h>
#include <vtkTransform.h>
#include <vtkLookupTable.h>
#include <vtkImageMapToColors.h>
#include <vtkImageAccumulate.h>
#include <vtkImageConnectivityFilter.h>
#include <vtkPointData.h>
#include <vtkDataArray.h>
#include <vtkStringArray.h>
#include <vtkRenderer.h>
#include <vtkRenderWindow.h>
#include <vtkRenderWindowInteractor.h>
#include <vtkWindowToImageFilter.h>
#include <vtkImageViewer2.h>
#include <vtkCamera.h>
#include <vtkProperty.h>
#include <vtkPolyDataMapper.h>
#include <vtkActor.h>
#include <vtkColorTransferFunction.h>
#include <vtkPiecewiseFunction.h>
#include <vtkVolumeProperty.h>
#include <vtkGPUVolumeRayCastMapper.h>
#include <vtkVolume.h>
#endif

namespace fs = std::filesystem;

// Helper to find test DICOM directory
static std::string FindTestDicomDir() {
    std::vector<std::string> searchPaths = {
        "../sample_series",
        "../../sample_series",
        "../../../sample_series",
        "sample_series"
    };
    for (const auto& base : searchPaths) {
        fs::path p(base);
        if (fs::exists(p) && fs::is_directory(p)) {
            return p.string();
        }
    }
    return "";
}

#ifdef USE_VTK

// =============================================================================
// VTK Basic Functionality Tests
// =============================================================================

TEST_CASE(VTK_Version) {
    std::string version = vtkVersion::GetVTKVersion();
    EXPECT_FALSE(version.empty());
    std::cerr << "  VTK Version: " << version << std::endl;
    return true;
}

TEST_CASE(VTK_CreateImageData) {
    vtkNew<vtkImageData> image;
    image->SetDimensions(64, 64, 16);
    image->AllocateScalars(VTK_SHORT, 1);
    
    int* dims = image->GetDimensions();
    EXPECT_EQ(dims[0], 64);
    EXPECT_EQ(dims[1], 64);
    EXPECT_EQ(dims[2], 16);
    return true;
}

TEST_CASE(VTK_ImageDataSpacing) {
    vtkNew<vtkImageData> image;
    image->SetDimensions(64, 64, 16);
    image->SetSpacing(0.5, 0.5, 1.0);
    image->AllocateScalars(VTK_SHORT, 1);
    
    double* spacing = image->GetSpacing();
    EXPECT_TRUE(std::abs(spacing[0] - 0.5) < 0.001);
    EXPECT_TRUE(std::abs(spacing[1] - 0.5) < 0.001);
    EXPECT_TRUE(std::abs(spacing[2] - 1.0) < 0.001);
    return true;
}

TEST_CASE(VTK_ImageDataOrigin) {
    vtkNew<vtkImageData> image;
    image->SetDimensions(64, 64, 16);
    image->SetOrigin(-100.0, -100.0, 0.0);
    image->AllocateScalars(VTK_SHORT, 1);
    
    double* origin = image->GetOrigin();
    EXPECT_TRUE(std::abs(origin[0] - (-100.0)) < 0.001);
    EXPECT_TRUE(std::abs(origin[1] - (-100.0)) < 0.001);
    EXPECT_TRUE(std::abs(origin[2] - 0.0) < 0.001);
    return true;
}

TEST_CASE(VTK_ImageDataPixelAccess) {
    vtkNew<vtkImageData> image;
    image->SetDimensions(16, 16, 4);
    image->AllocateScalars(VTK_SHORT, 1);
    
    // Fill with zeros
    short* ptr = static_cast<short*>(image->GetScalarPointer());
    int numVoxels = 16 * 16 * 4;
    for (int i = 0; i < numVoxels; ++i) {
        ptr[i] = 0;
    }
    
    // Set specific voxel
    short* voxel = static_cast<short*>(image->GetScalarPointer(8, 8, 2));
    *voxel = 100;
    
    // Verify
    short* readVoxel = static_cast<short*>(image->GetScalarPointer(8, 8, 2));
    EXPECT_EQ(*readVoxel, 100);
    return true;
}

TEST_CASE(VTK_SmartPointerBasics) {
    vtkSmartPointer<vtkImageData> image = vtkSmartPointer<vtkImageData>::New();
    image->SetDimensions(32, 32, 8);
    image->AllocateScalars(VTK_UNSIGNED_CHAR, 1);
    
    EXPECT_EQ(image->GetReferenceCount(), 1);
    
    vtkSmartPointer<vtkImageData> image2 = image;
    EXPECT_EQ(image->GetReferenceCount(), 2);
    
    return true;
}

// =============================================================================
// VTK DICOM Reading Tests
// =============================================================================

TEST_CASE(VTK_DICOMImageReaderAvailable) {
    vtkNew<vtkDICOMImageReader> reader;
    EXPECT_TRUE(reader != nullptr);
    return true;
}

TEST_CASE(VTK_ReadDicomDirectory) {
    std::string testDir = FindTestDicomDir();
    if (testDir.empty()) {
        std::cerr << "  [SKIP] No test DICOM directory found" << std::endl;
        return true;
    }
    
    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(testDir.c_str());
    reader->Update();
    
    vtkImageData* output = reader->GetOutput();
    EXPECT_TRUE(output != nullptr);
    
    int* dims = output->GetDimensions();
    EXPECT_GT(dims[0], 0);
    EXPECT_GT(dims[1], 0);
    return true;
}

TEST_CASE(VTK_ExtractDicomMetadata) {
    std::string testDir = FindTestDicomDir();
    if (testDir.empty()) return true;
    
    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(testDir.c_str());
    reader->Update();
    
    // Extract some metadata
    const char* patientName = reader->GetPatientName();
    const char* studyUID = reader->GetStudyUID();
    
    // Values may be empty but extraction shouldn't crash
    return true;
}

TEST_CASE(VTK_DicomImageScalarRange) {
    std::string testDir = FindTestDicomDir();
    if (testDir.empty()) return true;
    
    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(testDir.c_str());
    reader->Update();
    
    vtkImageData* output = reader->GetOutput();
    double range[2];
    output->GetScalarRange(range);
    
    // Range should be valid
    EXPECT_LE(range[0], range[1]);
    return true;
}

// =============================================================================
// VTK Image Processing Tests
// =============================================================================

TEST_CASE(VTK_ImageCast) {
    vtkNew<vtkImageData> image;
    image->SetDimensions(32, 32, 8);
    image->AllocateScalars(VTK_SHORT, 1);
    
    short* ptr = static_cast<short*>(image->GetScalarPointer());
    for (int i = 0; i < 32 * 32 * 8; ++i) {
        ptr[i] = 100;
    }
    
    vtkNew<vtkImageCast> caster;
    caster->SetInputData(image);
    caster->SetOutputScalarTypeToFloat();
    caster->Update();
    
    vtkImageData* output = caster->GetOutput();
    EXPECT_EQ(output->GetScalarType(), VTK_FLOAT);
    return true;
}

TEST_CASE(VTK_ImageThreshold) {
    vtkNew<vtkImageData> image;
    image->SetDimensions(32, 32, 8);
    image->AllocateScalars(VTK_SHORT, 1);
    
    short* ptr = static_cast<short*>(image->GetScalarPointer());
    for (int i = 0; i < 32 * 32 * 8; ++i) {
        ptr[i] = static_cast<short>(i % 256);
    }
    
    vtkNew<vtkImageThreshold> threshold;
    threshold->SetInputData(image);
    threshold->ThresholdBetween(100, 200);
    threshold->SetInValue(255);
    threshold->SetOutValue(0);
    threshold->Update();
    
    vtkImageData* output = threshold->GetOutput();
    EXPECT_TRUE(output != nullptr);
    return true;
}

TEST_CASE(VTK_GaussianSmooth) {
    vtkNew<vtkImageData> image;
    image->SetDimensions(32, 32, 8);
    image->AllocateScalars(VTK_SHORT, 1);
    
    short* ptr = static_cast<short*>(image->GetScalarPointer());
    for (int i = 0; i < 32 * 32 * 8; ++i) {
        ptr[i] = 100;
    }
    
    vtkNew<vtkImageGaussianSmooth> smooth;
    smooth->SetInputData(image);
    smooth->SetStandardDeviations(1.0, 1.0, 1.0);
    smooth->Update();
    
    vtkImageData* output = smooth->GetOutput();
    EXPECT_TRUE(output != nullptr);
    return true;
}

TEST_CASE(VTK_MedianFilter) {
    vtkNew<vtkImageData> image;
    image->SetDimensions(32, 32, 8);
    image->AllocateScalars(VTK_SHORT, 1);
    
    short* ptr = static_cast<short*>(image->GetScalarPointer());
    for (int i = 0; i < 32 * 32 * 8; ++i) {
        ptr[i] = 100;
    }
    
    vtkNew<vtkImageMedian3D> median;
    median->SetInputData(image);
    median->SetKernelSize(3, 3, 3);
    median->Update();
    
    vtkImageData* output = median->GetOutput();
    EXPECT_TRUE(output != nullptr);
    return true;
}

// =============================================================================
// VTK Resampling Tests
// =============================================================================

TEST_CASE(VTK_ImageResample) {
    vtkNew<vtkImageData> image;
    image->SetDimensions(64, 64, 16);
    image->SetSpacing(0.5, 0.5, 2.0);
    image->AllocateScalars(VTK_SHORT, 1);
    
    short* ptr = static_cast<short*>(image->GetScalarPointer());
    for (int i = 0; i < 64 * 64 * 16; ++i) {
        ptr[i] = 100;
    }
    
    vtkNew<vtkImageResample> resample;
    resample->SetInputData(image);
    resample->SetAxisOutputSpacing(0, 1.0);
    resample->SetAxisOutputSpacing(1, 1.0);
    resample->SetAxisOutputSpacing(2, 1.0);
    resample->Update();
    
    vtkImageData* output = resample->GetOutput();
    double* spacing = output->GetSpacing();
    
    EXPECT_TRUE(std::abs(spacing[0] - 1.0) < 0.001);
    EXPECT_TRUE(std::abs(spacing[1] - 1.0) < 0.001);
    EXPECT_TRUE(std::abs(spacing[2] - 1.0) < 0.001);
    return true;
}

TEST_CASE(VTK_ImageReslice) {
    vtkNew<vtkImageData> image;
    image->SetDimensions(32, 32, 8);
    image->AllocateScalars(VTK_SHORT, 1);
    
    short* ptr = static_cast<short*>(image->GetScalarPointer());
    for (int i = 0; i < 32 * 32 * 8; ++i) {
        ptr[i] = 100;
    }
    
    vtkNew<vtkImageReslice> reslice;
    reslice->SetInputData(image);
    reslice->SetOutputDimensionality(2);
    reslice->SetResliceAxesDirectionCosines(1, 0, 0, 0, 1, 0, 0, 0, 1);
    reslice->SetResliceAxesOrigin(0, 0, 4);  // Middle slice
    reslice->Update();
    
    vtkImageData* output = reslice->GetOutput();
    int* dims = output->GetDimensions();
    
    EXPECT_EQ(dims[2], 1);  // 2D output
    return true;
}

// =============================================================================
// VTK Surface Extraction Tests
// =============================================================================

TEST_CASE(VTK_MarchingCubes) {
    vtkNew<vtkImageData> image;
    image->SetDimensions(32, 32, 16);
    image->AllocateScalars(VTK_SHORT, 1);
    
    // Create a sphere-like structure
    short* ptr = static_cast<short*>(image->GetScalarPointer());
    for (int z = 0; z < 16; ++z) {
        for (int y = 0; y < 32; ++y) {
            for (int x = 0; x < 32; ++x) {
                double dx = x - 16.0;
                double dy = y - 16.0;
                double dz = z - 8.0;
                double dist = std::sqrt(dx*dx + dy*dy + dz*dz);
                int idx = z * 32 * 32 + y * 32 + x;
                ptr[idx] = (dist < 8.0) ? 200 : 0;
            }
        }
    }
    
    vtkNew<vtkMarchingCubes> mc;
    mc->SetInputData(image);
    mc->SetValue(0, 100);
    mc->Update();
    
    vtkPolyData* output = mc->GetOutput();
    EXPECT_GT(output->GetNumberOfPoints(), 0);
    EXPECT_GT(output->GetNumberOfCells(), 0);
    return true;
}

TEST_CASE(VTK_ContourFilter) {
    vtkNew<vtkImageData> image;
    image->SetDimensions(32, 32, 16);
    image->AllocateScalars(VTK_SHORT, 1);
    
    short* ptr = static_cast<short*>(image->GetScalarPointer());
    for (int i = 0; i < 32 * 32 * 16; ++i) {
        ptr[i] = static_cast<short>(i % 256);
    }
    
    vtkNew<vtkContourFilter> contour;
    contour->SetInputData(image);
    contour->SetValue(0, 128);
    contour->Update();
    
    vtkPolyData* output = contour->GetOutput();
    EXPECT_TRUE(output != nullptr);
    return true;
}

// =============================================================================
// VTK Statistics Tests
// =============================================================================

TEST_CASE(VTK_ImageAccumulate) {
    vtkNew<vtkImageData> image;
    image->SetDimensions(32, 32, 8);
    image->AllocateScalars(VTK_SHORT, 1);
    
    short* ptr = static_cast<short*>(image->GetScalarPointer());
    for (int i = 0; i < 32 * 32 * 8; ++i) {
        ptr[i] = static_cast<short>(i % 100);
    }
    
    vtkNew<vtkImageAccumulate> accumulate;
    accumulate->SetInputData(image);
    accumulate->SetComponentExtent(0, 255, 0, 0, 0, 0);
    accumulate->SetComponentOrigin(0, 0, 0);
    accumulate->SetComponentSpacing(1, 1, 1);
    accumulate->Update();
    
    double* mean = accumulate->GetMean();
    double* min = accumulate->GetMin();
    double* max = accumulate->GetMax();
    
    EXPECT_GE(min[0], 0);
    EXPECT_LE(max[0], 99);
    return true;
}

TEST_CASE(VTK_ScalarRange) {
    vtkNew<vtkImageData> image;
    image->SetDimensions(16, 16, 4);
    image->AllocateScalars(VTK_SHORT, 1);
    
    short* ptr = static_cast<short*>(image->GetScalarPointer());
    for (int i = 0; i < 16 * 16 * 4; ++i) {
        ptr[i] = 50;
    }
    ptr[0] = -100;
    ptr[16 * 16 * 4 - 1] = 200;
    
    double range[2];
    image->GetScalarRange(range);
    
    EXPECT_EQ(static_cast<int>(range[0]), -100);
    EXPECT_EQ(static_cast<int>(range[1]), 200);
    return true;
}

// =============================================================================
// VTK Color Mapping Tests
// =============================================================================

TEST_CASE(VTK_LookupTable) {
    vtkNew<vtkLookupTable> lut;
    lut->SetNumberOfTableValues(256);
    lut->SetRange(0, 255);
    lut->SetHueRange(0.0, 0.667);  // Red to blue
    lut->Build();
    
    double rgba[4];
    lut->GetTableValue(128, rgba);
    
    // Middle value should give some color
    EXPECT_GE(rgba[0], 0.0);
    EXPECT_LE(rgba[0], 1.0);
    return true;
}

TEST_CASE(VTK_ImageMapToColors) {
    vtkNew<vtkImageData> image;
    image->SetDimensions(32, 32, 1);
    image->AllocateScalars(VTK_SHORT, 1);
    
    short* ptr = static_cast<short*>(image->GetScalarPointer());
    for (int i = 0; i < 32 * 32; ++i) {
        ptr[i] = static_cast<short>(i % 256);
    }
    
    vtkNew<vtkLookupTable> lut;
    lut->SetNumberOfTableValues(256);
    lut->SetRange(0, 255);
    lut->Build();
    
    vtkNew<vtkImageMapToColors> mapper;
    mapper->SetInputData(image);
    mapper->SetLookupTable(lut);
    mapper->Update();
    
    vtkImageData* output = mapper->GetOutput();
    EXPECT_EQ(output->GetNumberOfScalarComponents(), 4);  // RGBA
    return true;
}

// =============================================================================
// VTK Transform Tests
// =============================================================================

TEST_CASE(VTK_Matrix4x4) {
    vtkNew<vtkMatrix4x4> matrix;
    matrix->Identity();
    
    EXPECT_TRUE(std::abs(matrix->GetElement(0, 0) - 1.0) < 0.001);
    EXPECT_TRUE(std::abs(matrix->GetElement(1, 1) - 1.0) < 0.001);
    EXPECT_TRUE(std::abs(matrix->GetElement(2, 2) - 1.0) < 0.001);
    EXPECT_TRUE(std::abs(matrix->GetElement(3, 3) - 1.0) < 0.001);
    return true;
}

TEST_CASE(VTK_Transform) {
    vtkNew<vtkTransform> transform;
    transform->Identity();
    transform->Translate(10.0, 20.0, 30.0);
    transform->RotateZ(45.0);
    
    vtkMatrix4x4* matrix = transform->GetMatrix();
    EXPECT_TRUE(matrix != nullptr);
    return true;
}

// =============================================================================
// VTK Image Flip Tests
// =============================================================================

TEST_CASE(VTK_ImageFlip) {
    vtkNew<vtkImageData> image;
    image->SetDimensions(32, 32, 8);
    image->AllocateScalars(VTK_SHORT, 1);
    
    short* ptr = static_cast<short*>(image->GetScalarPointer());
    for (int i = 0; i < 32 * 32 * 8; ++i) {
        ptr[i] = 100;
    }
    
    vtkNew<vtkImageFlip> flip;
    flip->SetInputData(image);
    flip->SetFilteredAxis(2);  // Flip Z
    flip->Update();
    
    vtkImageData* output = flip->GetOutput();
    int* dims = output->GetDimensions();
    
    EXPECT_EQ(dims[0], 32);
    EXPECT_EQ(dims[1], 32);
    EXPECT_EQ(dims[2], 8);
    return true;
}

// =============================================================================
// VTK File Writing Tests
// =============================================================================

TEST_CASE(VTK_WriteVTI) {
    vtkNew<vtkImageData> image;
    image->SetDimensions(16, 16, 4);
    image->AllocateScalars(VTK_SHORT, 1);
    
    short* ptr = static_cast<short*>(image->GetScalarPointer());
    for (int i = 0; i < 16 * 16 * 4; ++i) {
        ptr[i] = 100;
    }
    
    std::string outPath = fs::temp_directory_path().string() + "/test_vtk.vti";
    
    vtkNew<vtkXMLImageDataWriter> writer;
    writer->SetInputData(image);
    writer->SetFileName(outPath.c_str());
    int success = writer->Write();
    
    EXPECT_EQ(success, 1);
    EXPECT_TRUE(fs::exists(outPath));
    
    fs::remove(outPath);
    return true;
}

TEST_CASE(VTK_WriteSTL) {
    // Create simple cube-like structure for surface
    vtkNew<vtkImageData> image;
    image->SetDimensions(16, 16, 8);
    image->AllocateScalars(VTK_SHORT, 1);
    
    short* ptr = static_cast<short*>(image->GetScalarPointer());
    for (int z = 0; z < 8; ++z) {
        for (int y = 0; y < 16; ++y) {
            for (int x = 0; x < 16; ++x) {
                int idx = z * 16 * 16 + y * 16 + x;
                bool inside = (x >= 4 && x < 12 && y >= 4 && y < 12 && z >= 2 && z < 6);
                ptr[idx] = inside ? 200 : 0;
            }
        }
    }
    
    vtkNew<vtkMarchingCubes> mc;
    mc->SetInputData(image);
    mc->SetValue(0, 100);
    mc->Update();
    
    std::string outPath = fs::temp_directory_path().string() + "/test_vtk.stl";
    
    vtkNew<vtkSTLWriter> writer;
    writer->SetInputConnection(mc->GetOutputPort());
    writer->SetFileName(outPath.c_str());
    writer->Write();
    
    EXPECT_TRUE(fs::exists(outPath));
    fs::remove(outPath);
    return true;
}

// =============================================================================
// VTK Rendering Pipeline Tests (Offscreen)
// =============================================================================

TEST_CASE(VTK_RendererCreation) {
    vtkNew<vtkRenderer> renderer;
    renderer->SetBackground(0.0, 0.0, 0.0);
    
    double* bg = renderer->GetBackground();
    EXPECT_TRUE(std::abs(bg[0] - 0.0) < 0.001);
    return true;
}

TEST_CASE(VTK_CameraSetup) {
    vtkNew<vtkRenderer> renderer;
    vtkCamera* camera = renderer->GetActiveCamera();
    
    camera->SetPosition(0, 0, 100);
    camera->SetFocalPoint(0, 0, 0);
    camera->SetViewUp(0, 1, 0);
    
    double* pos = camera->GetPosition();
    EXPECT_TRUE(std::abs(pos[2] - 100.0) < 0.001);
    return true;
}

TEST_CASE(VTK_ActorCreation) {
    vtkNew<vtkPolyDataMapper> mapper;
    vtkNew<vtkActor> actor;
    actor->SetMapper(mapper);
    
    vtkProperty* prop = actor->GetProperty();
    prop->SetColor(1.0, 0.0, 0.0);
    
    double* color = prop->GetColor();
    EXPECT_TRUE(std::abs(color[0] - 1.0) < 0.001);
    return true;
}

#else // !USE_VTK

TEST_CASE(VTK_NotAvailable) {
    std::cerr << "  [INFO] VTK not available - skipping VTK tests" << std::endl;
    return true;
}

#endif // USE_VTK

// =============================================================================
// Main
// =============================================================================

int main(int argc, char* argv[]) {
    return RUN_TESTS("VTK Feature Tests");
}
