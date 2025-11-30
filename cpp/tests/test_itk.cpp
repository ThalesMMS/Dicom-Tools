//
// test_itk.cpp
// DicomToolsCpp
//
// Unit tests for ITK library features including image I/O, filtering, resampling,
// segmentation primitives, and volume processing.
//
// Thales Matheus Mendonça Santos - November 2025

#include "test_framework.h"

#include <filesystem>
#include <fstream>
#include <cmath>

#ifdef USE_ITK
#include <itkImage.h>
#include <itkImageFileReader.h>
#include <itkImageFileWriter.h>
#include <itkGDCMImageIO.h>
#include <itkGDCMSeriesFileNames.h>
#include <itkImageSeriesReader.h>
#include <itkImageSeriesWriter.h>
#include <itkMetaDataObject.h>
#include <itkGaussianBlurImageFunction.h>
#include <itkDiscreteGaussianImageFilter.h>
#include <itkMedianImageFilter.h>
#include <itkBinaryThresholdImageFilter.h>
#include <itkOtsuThresholdImageFilter.h>
#include <itkCannyEdgeDetectionImageFilter.h>
#include <itkResampleImageFilter.h>
#include <itkLinearInterpolateImageFunction.h>
#include <itkNearestNeighborInterpolateImageFunction.h>
#include <itkIdentityTransform.h>
#include <itkCastImageFilter.h>
#include <itkRescaleIntensityImageFilter.h>
#include <itkStatisticsImageFilter.h>
#include <itkMinimumMaximumImageCalculator.h>
#include <itkConnectedComponentImageFilter.h>
#include <itkExtractImageFilter.h>
#include <itkFlipImageFilter.h>
#include <itkImageRegionIterator.h>
#include <itkVersion.h>
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

#ifdef USE_ITK

// Common type definitions
using PixelType = short;
using ImageType3D = itk::Image<PixelType, 3>;
using ImageType2D = itk::Image<PixelType, 2>;
using FloatImageType3D = itk::Image<float, 3>;
using UCharImageType3D = itk::Image<unsigned char, 3>;

// =============================================================================
// ITK Basic Functionality Tests
// =============================================================================

TEST_CASE(ITK_Version) {
    std::string version = itk::Version::GetITKVersion();
    EXPECT_FALSE(version.empty());
    std::cerr << "  ITK Version: " << version << std::endl;
    return true;
}

TEST_CASE(ITK_CreateImage) {
    auto image = ImageType3D::New();
    
    ImageType3D::IndexType start;
    start.Fill(0);
    
    ImageType3D::SizeType size;
    size[0] = 64;
    size[1] = 64;
    size[2] = 16;
    
    ImageType3D::RegionType region;
    region.SetSize(size);
    region.SetIndex(start);
    
    image->SetRegions(region);
    image->Allocate();
    image->FillBuffer(0);
    
    EXPECT_EQ(image->GetLargestPossibleRegion().GetSize()[0], 64u);
    EXPECT_EQ(image->GetLargestPossibleRegion().GetSize()[1], 64u);
    EXPECT_EQ(image->GetLargestPossibleRegion().GetSize()[2], 16u);
    return true;
}

TEST_CASE(ITK_ImageSpacing) {
    auto image = ImageType3D::New();
    
    ImageType3D::SpacingType spacing;
    spacing[0] = 0.5;
    spacing[1] = 0.5;
    spacing[2] = 1.0;
    image->SetSpacing(spacing);
    
    auto readSpacing = image->GetSpacing();
    EXPECT_TRUE(std::abs(readSpacing[0] - 0.5) < 0.001);
    EXPECT_TRUE(std::abs(readSpacing[1] - 0.5) < 0.001);
    EXPECT_TRUE(std::abs(readSpacing[2] - 1.0) < 0.001);
    return true;
}

TEST_CASE(ITK_ImageOrigin) {
    auto image = ImageType3D::New();
    
    ImageType3D::PointType origin;
    origin[0] = -100.0;
    origin[1] = -100.0;
    origin[2] = 0.0;
    image->SetOrigin(origin);
    
    auto readOrigin = image->GetOrigin();
    EXPECT_TRUE(std::abs(readOrigin[0] - (-100.0)) < 0.001);
    return true;
}

TEST_CASE(ITK_ImageDirection) {
    auto image = ImageType3D::New();
    
    ImageType3D::DirectionType direction;
    direction.SetIdentity();
    image->SetDirection(direction);
    
    auto readDir = image->GetDirection();
    EXPECT_TRUE(std::abs(readDir(0, 0) - 1.0) < 0.001);
    EXPECT_TRUE(std::abs(readDir(1, 1) - 1.0) < 0.001);
    EXPECT_TRUE(std::abs(readDir(2, 2) - 1.0) < 0.001);
    return true;
}

TEST_CASE(ITK_PixelAccess) {
    auto image = ImageType3D::New();
    
    ImageType3D::SizeType size;
    size.Fill(10);
    ImageType3D::IndexType start;
    start.Fill(0);
    ImageType3D::RegionType region(start, size);
    
    image->SetRegions(region);
    image->Allocate();
    image->FillBuffer(0);
    
    ImageType3D::IndexType idx;
    idx[0] = 5; idx[1] = 5; idx[2] = 5;
    image->SetPixel(idx, 100);
    
    EXPECT_EQ(image->GetPixel(idx), 100);
    return true;
}

// =============================================================================
// ITK DICOM I/O Tests
// =============================================================================

TEST_CASE(ITK_GDCMImageIOAvailable) {
    auto gdcmIO = itk::GDCMImageIO::New();
    EXPECT_TRUE(gdcmIO.IsNotNull());
    return true;
}

TEST_CASE(ITK_ReadDicomSeries) {
    std::string testDir = FindTestDicomDir();
    if (testDir.empty()) {
        std::cerr << "  [SKIP] No test DICOM directory found" << std::endl;
        return true;
    }
    
    using NamesGeneratorType = itk::GDCMSeriesFileNames;
    auto namesGenerator = NamesGeneratorType::New();
    namesGenerator->SetDirectory(testDir);
    
    auto seriesUIDs = namesGenerator->GetSeriesUIDs();
    if (seriesUIDs.empty()) {
        std::cerr << "  [SKIP] No DICOM series found in test directory" << std::endl;
        return true;
    }
    
    auto fileNames = namesGenerator->GetFileNames(seriesUIDs[0]);
    EXPECT_FALSE(fileNames.empty());
    
    using ReaderType = itk::ImageSeriesReader<ImageType3D>;
    auto reader = ReaderType::New();
    auto gdcmIO = itk::GDCMImageIO::New();
    
    reader->SetImageIO(gdcmIO);
    reader->SetFileNames(fileNames);
    
    try {
        reader->Update();
        auto image = reader->GetOutput();
        
        auto size = image->GetLargestPossibleRegion().GetSize();
        EXPECT_GT(size[0], 0u);
        EXPECT_GT(size[1], 0u);
    } catch (const itk::ExceptionObject& e) {
        std::cerr << "  [ERROR] " << e.what() << std::endl;
        return false;
    }
    
    return true;
}

TEST_CASE(ITK_ExtractDicomMetadata) {
    std::string testDir = FindTestDicomDir();
    if (testDir.empty()) return true;
    
    auto namesGenerator = itk::GDCMSeriesFileNames::New();
    namesGenerator->SetDirectory(testDir);
    auto seriesUIDs = namesGenerator->GetSeriesUIDs();
    if (seriesUIDs.empty()) return true;
    
    auto fileNames = namesGenerator->GetFileNames(seriesUIDs[0]);
    
    using ReaderType = itk::ImageSeriesReader<ImageType3D>;
    auto reader = ReaderType::New();
    auto gdcmIO = itk::GDCMImageIO::New();
    
    reader->SetImageIO(gdcmIO);
    reader->SetFileNames(fileNames);
    reader->Update();
    
    // Extract metadata
    auto metaDict = gdcmIO->GetMetaDataDictionary();
    
    std::string modality;
    itk::ExposeMetaData<std::string>(metaDict, "0008|0060", modality);
    // Modality may or may not exist
    
    return true;
}

// =============================================================================
// ITK Filter Tests
// =============================================================================

TEST_CASE(ITK_GaussianFilter) {
    // Create test image
    auto image = ImageType3D::New();
    ImageType3D::SizeType size = {{32, 32, 8}};
    image->SetRegions(size);
    image->Allocate();
    image->FillBuffer(100);
    
    using FilterType = itk::DiscreteGaussianImageFilter<ImageType3D, ImageType3D>;
    auto filter = FilterType::New();
    filter->SetInput(image);
    filter->SetVariance(2.0);
    
    EXPECT_NO_THROW(filter->Update());
    
    auto output = filter->GetOutput();
    EXPECT_TRUE(output.IsNotNull());
    return true;
}

TEST_CASE(ITK_MedianFilter) {
    auto image = ImageType3D::New();
    ImageType3D::SizeType size = {{32, 32, 8}};
    image->SetRegions(size);
    image->Allocate();
    image->FillBuffer(100);
    
    using FilterType = itk::MedianImageFilter<ImageType3D, ImageType3D>;
    auto filter = FilterType::New();
    filter->SetInput(image);
    
    ImageType3D::SizeType radius;
    radius.Fill(1);
    filter->SetRadius(radius);
    
    EXPECT_NO_THROW(filter->Update());
    return true;
}

TEST_CASE(ITK_BinaryThreshold) {
    auto image = ImageType3D::New();
    ImageType3D::SizeType size = {{32, 32, 8}};
    image->SetRegions(size);
    image->Allocate();
    
    // Create gradient
    itk::ImageRegionIterator<ImageType3D> it(image, image->GetLargestPossibleRegion());
    short val = 0;
    for (it.GoToBegin(); !it.IsAtEnd(); ++it, ++val) {
        it.Set(val % 256);
    }
    
    using ThresholdFilter = itk::BinaryThresholdImageFilter<ImageType3D, UCharImageType3D>;
    auto threshold = ThresholdFilter::New();
    threshold->SetInput(image);
    threshold->SetLowerThreshold(100);
    threshold->SetUpperThreshold(200);
    threshold->SetInsideValue(255);
    threshold->SetOutsideValue(0);
    
    EXPECT_NO_THROW(threshold->Update());
    return true;
}

TEST_CASE(ITK_OtsuThreshold) {
    auto image = ImageType3D::New();
    ImageType3D::SizeType size = {{32, 32, 8}};
    image->SetRegions(size);
    image->Allocate();
    
    itk::ImageRegionIterator<ImageType3D> it(image, image->GetLargestPossibleRegion());
    short val = 0;
    for (it.GoToBegin(); !it.IsAtEnd(); ++it, ++val) {
        it.Set(val % 256);
    }
    
    using OtsuFilter = itk::OtsuThresholdImageFilter<ImageType3D, UCharImageType3D>;
    auto otsu = OtsuFilter::New();
    otsu->SetInput(image);
    
    EXPECT_NO_THROW(otsu->Update());
    
    auto threshold = otsu->GetThreshold();
    EXPECT_GT(threshold, 0);
    return true;
}

// =============================================================================
// ITK Resampling Tests
// =============================================================================

TEST_CASE(ITK_ResampleFilter) {
    auto image = ImageType3D::New();
    ImageType3D::SizeType size = {{64, 64, 16}};
    ImageType3D::SpacingType spacing;
    spacing[0] = 0.5; spacing[1] = 0.5; spacing[2] = 2.0;
    
    image->SetRegions(size);
    image->SetSpacing(spacing);
    image->Allocate();
    image->FillBuffer(100);
    
    using ResampleFilter = itk::ResampleImageFilter<ImageType3D, ImageType3D>;
    using InterpolatorType = itk::LinearInterpolateImageFunction<ImageType3D, double>;
    using TransformType = itk::IdentityTransform<double, 3>;
    
    auto resample = ResampleFilter::New();
    auto interpolator = InterpolatorType::New();
    auto transform = TransformType::New();
    
    // Target: isotropic 1mm
    ImageType3D::SpacingType newSpacing;
    newSpacing.Fill(1.0);
    
    ImageType3D::SizeType newSize;
    newSize[0] = static_cast<unsigned int>(size[0] * spacing[0] / newSpacing[0]);
    newSize[1] = static_cast<unsigned int>(size[1] * spacing[1] / newSpacing[1]);
    newSize[2] = static_cast<unsigned int>(size[2] * spacing[2] / newSpacing[2]);
    
    resample->SetInput(image);
    resample->SetInterpolator(interpolator);
    resample->SetTransform(transform);
    resample->SetOutputSpacing(newSpacing);
    resample->SetSize(newSize);
    resample->SetOutputOrigin(image->GetOrigin());
    resample->SetOutputDirection(image->GetDirection());
    
    EXPECT_NO_THROW(resample->Update());
    
    auto output = resample->GetOutput();
    auto outputSpacing = output->GetSpacing();
    EXPECT_TRUE(std::abs(outputSpacing[0] - 1.0) < 0.001);
    return true;
}

TEST_CASE(ITK_NearestNeighborInterpolation) {
    auto image = ImageType3D::New();
    ImageType3D::SizeType size = {{16, 16, 4}};
    image->SetRegions(size);
    image->Allocate();
    image->FillBuffer(50);
    
    using InterpolatorType = itk::NearestNeighborInterpolateImageFunction<ImageType3D, double>;
    auto interpolator = InterpolatorType::New();
    interpolator->SetInputImage(image);
    
    ImageType3D::PointType point;
    point[0] = 8.0; point[1] = 8.0; point[2] = 2.0;
    
    if (interpolator->IsInsideBuffer(point)) {
        auto value = interpolator->Evaluate(point);
        EXPECT_EQ(static_cast<int>(value), 50);
    }
    return true;
}

// =============================================================================
// ITK Statistics Tests
// =============================================================================

TEST_CASE(ITK_StatisticsFilter) {
    auto image = ImageType3D::New();
    ImageType3D::SizeType size = {{32, 32, 8}};
    image->SetRegions(size);
    image->Allocate();
    
    // Fill with known values
    itk::ImageRegionIterator<ImageType3D> it(image, image->GetLargestPossibleRegion());
    short val = 0;
    for (it.GoToBegin(); !it.IsAtEnd(); ++it, ++val) {
        it.Set(val % 100);
    }
    
    using StatsFilter = itk::StatisticsImageFilter<ImageType3D>;
    auto stats = StatsFilter::New();
    stats->SetInput(image);
    stats->Update();
    
    EXPECT_GE(stats->GetMinimum(), 0);
    EXPECT_LE(stats->GetMaximum(), 99);
    EXPECT_GT(stats->GetMean(), 0);
    return true;
}

TEST_CASE(ITK_MinMaxCalculator) {
    auto image = ImageType3D::New();
    ImageType3D::SizeType size = {{16, 16, 4}};
    image->SetRegions(size);
    image->Allocate();
    image->FillBuffer(50);
    
    // Set specific min/max
    ImageType3D::IndexType minIdx = {{0, 0, 0}};
    ImageType3D::IndexType maxIdx = {{15, 15, 3}};
    image->SetPixel(minIdx, -100);
    image->SetPixel(maxIdx, 200);
    
    using CalculatorType = itk::MinimumMaximumImageCalculator<ImageType3D>;
    auto calculator = CalculatorType::New();
    calculator->SetImage(image);
    calculator->Compute();
    
    EXPECT_EQ(calculator->GetMinimum(), -100);
    EXPECT_EQ(calculator->GetMaximum(), 200);
    return true;
}

// =============================================================================
// ITK Connected Components Tests
// =============================================================================

TEST_CASE(ITK_ConnectedComponents) {
    auto image = UCharImageType3D::New();
    UCharImageType3D::SizeType size = {{32, 32, 8}};
    image->SetRegions(size);
    image->Allocate();
    image->FillBuffer(0);
    
    // Create two separate regions
    UCharImageType3D::IndexType idx;
    for (int x = 5; x < 10; ++x) {
        for (int y = 5; y < 10; ++y) {
            for (int z = 2; z < 4; ++z) {
                idx[0] = x; idx[1] = y; idx[2] = z;
                image->SetPixel(idx, 255);
            }
        }
    }
    for (int x = 20; x < 25; ++x) {
        for (int y = 20; y < 25; ++y) {
            for (int z = 5; z < 7; ++z) {
                idx[0] = x; idx[1] = y; idx[2] = z;
                image->SetPixel(idx, 255);
            }
        }
    }
    
    using ConnectedFilter = itk::ConnectedComponentImageFilter<UCharImageType3D, ImageType3D>;
    auto connected = ConnectedFilter::New();
    connected->SetInput(image);
    connected->Update();
    
    auto numObjects = connected->GetObjectCount();
    EXPECT_EQ(numObjects, 2u);
    return true;
}

// =============================================================================
// ITK Casting and Rescaling Tests
// =============================================================================

TEST_CASE(ITK_CastFilter) {
    auto image = ImageType3D::New();
    ImageType3D::SizeType size = {{16, 16, 4}};
    image->SetRegions(size);
    image->Allocate();
    image->FillBuffer(100);
    
    using CastFilter = itk::CastImageFilter<ImageType3D, FloatImageType3D>;
    auto caster = CastFilter::New();
    caster->SetInput(image);
    
    EXPECT_NO_THROW(caster->Update());
    
    auto output = caster->GetOutput();
    ImageType3D::IndexType idx = {{8, 8, 2}};
    EXPECT_TRUE(std::abs(output->GetPixel(idx) - 100.0f) < 0.001f);
    return true;
}

TEST_CASE(ITK_RescaleIntensity) {
    auto image = ImageType3D::New();
    ImageType3D::SizeType size = {{16, 16, 4}};
    image->SetRegions(size);
    image->Allocate();
    
    itk::ImageRegionIterator<ImageType3D> it(image, image->GetLargestPossibleRegion());
    short val = 0;
    for (it.GoToBegin(); !it.IsAtEnd(); ++it, ++val) {
        it.Set(val % 1000);
    }
    
    using RescaleFilter = itk::RescaleIntensityImageFilter<ImageType3D, UCharImageType3D>;
    auto rescale = RescaleFilter::New();
    rescale->SetInput(image);
    rescale->SetOutputMinimum(0);
    rescale->SetOutputMaximum(255);
    
    EXPECT_NO_THROW(rescale->Update());
    return true;
}

// =============================================================================
// ITK Slice Extraction Tests
// =============================================================================

TEST_CASE(ITK_ExtractSlice) {
    auto image = ImageType3D::New();
    ImageType3D::SizeType size = {{64, 64, 16}};
    image->SetRegions(size);
    image->Allocate();
    image->FillBuffer(100);
    
    using ExtractFilter = itk::ExtractImageFilter<ImageType3D, ImageType2D>;
    auto extract = ExtractFilter::New();
    extract->SetDirectionCollapseToSubmatrix();
    
    ImageType3D::RegionType extractRegion = image->GetLargestPossibleRegion();
    ImageType3D::SizeType extractSize = extractRegion.GetSize();
    extractSize[2] = 0;  // Collapse Z dimension
    
    ImageType3D::IndexType extractStart = extractRegion.GetIndex();
    extractStart[2] = 8;  // Middle slice
    
    extractRegion.SetSize(extractSize);
    extractRegion.SetIndex(extractStart);
    
    extract->SetExtractionRegion(extractRegion);
    extract->SetInput(image);
    
    EXPECT_NO_THROW(extract->Update());
    
    auto output = extract->GetOutput();
    EXPECT_EQ(output->GetLargestPossibleRegion().GetSize()[0], 64u);
    EXPECT_EQ(output->GetLargestPossibleRegion().GetSize()[1], 64u);
    return true;
}

#else // !USE_ITK

TEST_CASE(ITK_NotAvailable) {
    std::cerr << "  [INFO] ITK not available - skipping ITK tests" << std::endl;
    return true;
}

#endif // USE_ITK

// =============================================================================
// Main
// =============================================================================

int main(int argc, char* argv[]) {
    return RUN_TESTS("ITK Feature Tests");
}
