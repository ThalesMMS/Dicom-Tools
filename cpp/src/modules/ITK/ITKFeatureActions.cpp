//
// ITKFeatureActions.cpp
// DicomToolsCpp
//
// Implements ITK-based processing demos including smoothing, segmentation, resampling, projections, and format exports.
//
// Thales Matheus Mendonça Santos - November 2025

#include "ITKFeatureActions.h"

#include <filesystem>
#include <iostream>

#ifdef USE_ITK
#include "itkAdaptiveHistogramEqualizationImageFilter.h"
#include "itkBinaryThresholdImageFilter.h"
#include "itkConnectedThresholdImageFilter.h"
#include "itkCannyEdgeDetectionImageFilter.h"
#include "itkCastImageFilter.h"
#include "itkDiscreteGaussianImageFilter.h"
#include "itkExtractImageFilter.h"
#include "itkGDCMImageIO.h"
#include "itkIdentityTransform.h"
#include "itkImage.h"
#include "itkImageFileReader.h"
#include "itkImageFileWriter.h"
#include "itkLinearInterpolateImageFunction.h"
#include "itkMedianImageFilter.h"
#include "itkNrrdImageIO.h"
#include "itkNiftiImageIO.h"
#include "itkMaximumProjectionImageFilter.h"
#include "itkOtsuThresholdImageFilter.h"
#include "itkCurvatureAnisotropicDiffusionImageFilter.h"
#include "itkPNGImageIO.h"
#include "itkResampleImageFilter.h"
#include "itkRescaleIntensityImageFilter.h"

namespace {
std::string JoinPath(const std::string& base, const std::string& filename) {
    return (std::filesystem::path(base) / filename).string();
}

using ImageIOType = itk::GDCMImageIO;
}

void ITKTests::TestCannyEdgeDetection(const std::string& filename, const std::string& outputDir) {
    // Run 3D Canny edge detection and rescale for easy viewing
    std::cout << "--- [ITK] Canny Edge Detection ---" << std::endl;
    
    using InputPixelType = float;
    using OutputPixelType = unsigned char;
    const unsigned int Dimension = 3;
    
    using InputImageType = itk::Image<InputPixelType, Dimension>;
    using OutputImageType = itk::Image<OutputPixelType, Dimension>;
    
    using ReaderType = itk::ImageFileReader<InputImageType>;
    using WriterType = itk::ImageFileWriter<OutputImageType>;
    using FilterType = itk::CannyEdgeDetectionImageFilter<InputImageType, InputImageType>;
    using RescaleType = itk::RescaleIntensityImageFilter<InputImageType, OutputImageType>;

    ReaderType::Pointer reader = ReaderType::New();
    reader->SetFileName(filename);
    
    using ImageIOType = itk::GDCMImageIO;
    ImageIOType::Pointer gdcmIO = ImageIOType::New();
    reader->SetImageIO(gdcmIO);

    try {
        reader->Update();
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Exception: " << err << std::endl;
        return;
    }

    FilterType::Pointer filter = FilterType::New();
    filter->SetInput(reader->GetOutput());
    filter->SetVariance(2.0);
    filter->SetUpperThreshold(0.05);
    filter->SetLowerThreshold(0.02);
    
    RescaleType::Pointer rescaler = RescaleType::New();
    rescaler->SetInput(filter->GetOutput());
    rescaler->SetOutputMinimum(0);
    rescaler->SetOutputMaximum(255);

    WriterType::Pointer writer = WriterType::New();
    writer->SetFileName(JoinPath(outputDir, "itk_canny.dcm"));
    writer->SetInput(rescaler->GetOutput());
    writer->SetImageIO(gdcmIO);

    try {
        writer->Update();
        std::cout << "Saved to '" << writer->GetFileName() << "'" << std::endl;
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Write Exception: " << err << std::endl;
    }
}

void ITKTests::TestGaussianSmoothing(const std::string& filename, const std::string& outputDir) {
    // Apply a modest Gaussian blur to smooth noise in the volume
    std::cout << "--- [ITK] Gaussian Smoothing ---" << std::endl;
    
    using PixelType = signed short;
    const unsigned int Dimension = 3;
    using ImageType = itk::Image<PixelType, Dimension>;
    using ReaderType = itk::ImageFileReader<ImageType>;
    using WriterType = itk::ImageFileWriter<ImageType>;
    using FilterType = itk::DiscreteGaussianImageFilter<ImageType, ImageType>;

    ReaderType::Pointer reader = ReaderType::New();
    reader->SetFileName(filename);
    
    using ImageIOType = itk::GDCMImageIO;
    ImageIOType::Pointer gdcmIO = ImageIOType::New();
    reader->SetImageIO(gdcmIO);

    try {
        reader->Update();
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Exception: " << err << std::endl;
        return;
    }

    FilterType::Pointer filter = FilterType::New();
    filter->SetInput(reader->GetOutput());
    filter->SetVariance(1.0);

    WriterType::Pointer writer = WriterType::New();
    writer->SetFileName(JoinPath(outputDir, "itk_gaussian.dcm"));
    writer->SetInput(filter->GetOutput());
    writer->SetImageIO(gdcmIO);

    try {
        writer->Update();
        std::cout << "Saved to '" << writer->GetFileName() << "'" << std::endl;
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Write Exception: " << err << std::endl;
    }
}

void ITKTests::TestBinaryThresholding(const std::string& filename, const std::string& outputDir) {
    // Segment voxels within a fixed HU range using a binary mask
    std::cout << "--- [ITK] Binary Thresholding ---" << std::endl;
    
    using PixelType = signed short;
    const unsigned int Dimension = 3;
    using ImageType = itk::Image<PixelType, Dimension>;
    using ReaderType = itk::ImageFileReader<ImageType>;
    using WriterType = itk::ImageFileWriter<ImageType>;
    using FilterType = itk::BinaryThresholdImageFilter<ImageType, ImageType>;

    ReaderType::Pointer reader = ReaderType::New();
    reader->SetFileName(filename);
    
    using ImageIOType = itk::GDCMImageIO;
    ImageIOType::Pointer gdcmIO = ImageIOType::New();
    reader->SetImageIO(gdcmIO);

    try {
        reader->Update();
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Exception: " << err << std::endl;
        return;
    }

    FilterType::Pointer filter = FilterType::New();
    filter->SetInput(reader->GetOutput());
    filter->SetLowerThreshold(200);
    filter->SetUpperThreshold(3000);
    filter->SetInsideValue(1000);
    filter->SetOutsideValue(0);

    WriterType::Pointer writer = WriterType::New();
    writer->SetFileName(JoinPath(outputDir, "itk_threshold.dcm"));
    writer->SetInput(filter->GetOutput());
    writer->SetImageIO(gdcmIO);

    try {
        writer->Update();
        std::cout << "Saved to '" << writer->GetFileName() << "'" << std::endl;
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Write Exception: " << err << std::endl;
    }
}

void ITKTests::TestResampling(const std::string& filename, const std::string& outputDir) {
    // Resample to 1mm isotropic spacing with linear interpolation
    std::cout << "--- [ITK] Resampling ---" << std::endl;
    
    using PixelType = signed short;
    const unsigned int Dimension = 3;
    using ImageType = itk::Image<PixelType, Dimension>;
    using ReaderType = itk::ImageFileReader<ImageType>;
    using WriterType = itk::ImageFileWriter<ImageType>;
    
    ReaderType::Pointer reader = ReaderType::New();
    reader->SetFileName(filename);
    
    using ImageIOType = itk::GDCMImageIO;
    ImageIOType::Pointer gdcmIO = ImageIOType::New();
    reader->SetImageIO(gdcmIO);
    
    try {
        reader->Update();
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Exception: " << err << std::endl;
        return;
    }
    
    ImageType::Pointer inputImage = reader->GetOutput();
    ImageType::SpacingType inputSpacing = inputImage->GetSpacing();
    ImageType::SizeType inputSize = inputImage->GetLargestPossibleRegion().GetSize();
    
    std::cout << "Original Spacing: " << inputSpacing << std::endl;
    std::cout << "Original Size: " << inputSize << std::endl;
    
    ImageType::SpacingType outputSpacing;
    outputSpacing.Fill(1.0);
    
    ImageType::SizeType outputSize;
    outputSize[0] = static_cast<unsigned long>(inputSize[0] * inputSpacing[0] / outputSpacing[0]);
    outputSize[1] = static_cast<unsigned long>(inputSize[1] * inputSpacing[1] / outputSpacing[1]);
    outputSize[2] = static_cast<unsigned long>(inputSize[2] * inputSpacing[2] / outputSpacing[2]);

    using TransformType = itk::IdentityTransform<double, Dimension>;
    using InterpolatorType = itk::LinearInterpolateImageFunction<ImageType, double>;
    using ResampleFilterType = itk::ResampleImageFilter<ImageType, ImageType>;
    
    ResampleFilterType::Pointer resampler = ResampleFilterType::New();
    resampler->SetInput(inputImage);
    resampler->SetSize(outputSize);
    resampler->SetOutputSpacing(outputSpacing);
    resampler->SetOutputOrigin(inputImage->GetOrigin());
    resampler->SetOutputDirection(inputImage->GetDirection());
    resampler->SetTransform(TransformType::New());
    resampler->SetInterpolator(InterpolatorType::New());
    resampler->SetDefaultPixelValue(0);
    
    WriterType::Pointer writer = WriterType::New();
    writer->SetFileName(JoinPath(outputDir, "itk_resampled.dcm"));
    writer->SetInput(resampler->GetOutput());
    writer->SetImageIO(gdcmIO);
    
    try {
        writer->Update();
        std::cout << "Saved to '" << writer->GetFileName() << "'" << std::endl;
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Write Exception: " << err << std::endl;
    }
}

void ITKTests::TestAdaptiveHistogram(const std::string& filename, const std::string& outputDir) {
    // Boost contrast with adaptive histogram equalization
    std::cout << "--- [ITK] Adaptive Histogram Equalization ---" << std::endl;
    using PixelType = signed short;
    const unsigned int Dimension = 3;
    using ImageType = itk::Image<PixelType, Dimension>;
    using ReaderType = itk::ImageFileReader<ImageType>;
    using WriterType = itk::ImageFileWriter<ImageType>;
    using EqualizeType = itk::AdaptiveHistogramEqualizationImageFilter<ImageType>;

    ReaderType::Pointer reader = ReaderType::New();
    reader->SetFileName(filename);

    using ImageIOType = itk::GDCMImageIO;
    ImageIOType::Pointer gdcmIO = ImageIOType::New();
    reader->SetImageIO(gdcmIO);

    try {
        reader->Update();
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Exception: " << err << std::endl;
        return;
    }

    EqualizeType::Pointer equalizer = EqualizeType::New();
    equalizer->SetInput(reader->GetOutput());
    equalizer->SetAlpha(0.3);
    equalizer->SetBeta(0.3);

    WriterType::Pointer writer = WriterType::New();
    writer->SetFileName(JoinPath(outputDir, "itk_histogram_eq.dcm"));
    writer->SetInput(equalizer->GetOutput());
    writer->SetImageIO(gdcmIO);

    try {
        writer->Update();
        std::cout << "Saved to '" << writer->GetFileName() << "'" << std::endl;
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Write Exception: " << err << std::endl;
    }
}

void ITKTests::TestSliceExtraction(const std::string& filename, const std::string& outputDir) {
    // Pull the middle axial slice and rescale it to an 8-bit PNG
    std::cout << "--- [ITK] Slice Extraction ---" << std::endl;
    using PixelType = signed short;
    using InputImageType = itk::Image<PixelType, 3>;
    using SliceImageType = itk::Image<unsigned char, 2>;
    using ReaderType = itk::ImageFileReader<InputImageType>;
    using ExtractType = itk::ExtractImageFilter<InputImageType, SliceImageType>;
    using RescaleType = itk::RescaleIntensityImageFilter<SliceImageType, SliceImageType>;
    using WriterType = itk::ImageFileWriter<SliceImageType>;

    ReaderType::Pointer reader = ReaderType::New();
    reader->SetFileName(filename);

    using ImageIOType = itk::GDCMImageIO;
    ImageIOType::Pointer gdcmIO = ImageIOType::New();
    reader->SetImageIO(gdcmIO);

    try {
        reader->Update();
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Exception: " << err << std::endl;
        return;
    }

    InputImageType::RegionType region = reader->GetOutput()->GetLargestPossibleRegion();
    InputImageType::SizeType size = region.GetSize();
    InputImageType::IndexType start = region.GetIndex();
    start[2] = region.GetIndex()[2] + (size[2] / 2);
    size[2] = 0;

    ExtractType::Pointer extract = ExtractType::New();
    extract->SetInput(reader->GetOutput());
    extract->SetExtractionRegion({start, size});
    extract->SetDirectionCollapseToSubmatrix();

    RescaleType::Pointer rescale = RescaleType::New();
    rescale->SetInput(extract->GetOutput());
    rescale->SetOutputMinimum(0);
    rescale->SetOutputMaximum(255);

    WriterType::Pointer writer = WriterType::New();
    writer->SetFileName(JoinPath(outputDir, "itk_slice.png"));
    writer->SetInput(rescale->GetOutput());
    writer->SetImageIO(itk::PNGImageIO::New());

    try {
        writer->Update();
        std::cout << "Saved middle slice PNG to '" << writer->GetFileName() << "'" << std::endl;
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Write Exception: " << err << std::endl;
    }
}

void ITKTests::TestMedianFilter(const std::string& filename, const std::string& outputDir) {
    // Apply a small 3x3x3 median filter to remove salt-and-pepper noise
    std::cout << "--- [ITK] Median Filter ---" << std::endl;

    using PixelType = signed short;
    const unsigned int Dimension = 3;
    using ImageType = itk::Image<PixelType, Dimension>;
    using ReaderType = itk::ImageFileReader<ImageType>;
    using FilterType = itk::MedianImageFilter<ImageType, ImageType>;
    using WriterType = itk::ImageFileWriter<ImageType>;

    ReaderType::Pointer reader = ReaderType::New();
    reader->SetFileName(filename);
    using ImageIOType = itk::GDCMImageIO;
    ImageIOType::Pointer gdcmIO = ImageIOType::New();
    reader->SetImageIO(gdcmIO);

    try {
        reader->Update();
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Exception: " << err << std::endl;
        return;
    }

    FilterType::Pointer median = FilterType::New();
    FilterType::InputSizeType radius;
    radius.Fill(1);
    median->SetRadius(radius);
    median->SetInput(reader->GetOutput());

    WriterType::Pointer writer = WriterType::New();
    writer->SetFileName(JoinPath(outputDir, "itk_median.dcm"));
    writer->SetInput(median->GetOutput());
    writer->SetImageIO(gdcmIO);

    try {
        writer->Update();
        std::cout << "Saved to '" << writer->GetFileName() << "'" << std::endl;
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Write Exception: " << err << std::endl;
    }
}

void ITKTests::TestNRRDExport(const std::string& filename, const std::string& outputDir) {
    // Export the volume to NRRD, rescaled to a convenient intensity range
    std::cout << "--- [ITK] NRRD Export ---" << std::endl;

    using PixelType = signed short;
    const unsigned int Dimension = 3;
    using ImageType = itk::Image<PixelType, Dimension>;
    using ReaderType = itk::ImageFileReader<ImageType>;
    using RescaleType = itk::RescaleIntensityImageFilter<ImageType, ImageType>;
    using WriterType = itk::ImageFileWriter<ImageType>;

    ReaderType::Pointer reader = ReaderType::New();
    reader->SetFileName(filename);
    using ImageIOType = itk::GDCMImageIO;
    ImageIOType::Pointer gdcmIO = ImageIOType::New();
    reader->SetImageIO(gdcmIO);

    try {
        reader->Update();
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Exception: " << err << std::endl;
        return;
    }

    RescaleType::Pointer rescale = RescaleType::New();
    rescale->SetInput(reader->GetOutput());
    rescale->SetOutputMinimum(0);
    rescale->SetOutputMaximum(4095);

    WriterType::Pointer writer = WriterType::New();
    writer->SetFileName(JoinPath(outputDir, "itk_volume.nrrd"));
    writer->SetInput(rescale->GetOutput());
    writer->UseCompressionOn();
    writer->SetImageIO(itk::NrrdImageIO::New());

    try {
        writer->Update();
        std::cout << "Saved to '" << writer->GetFileName() << "'" << std::endl;
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Write Exception: " << err << std::endl;
    }
}

void ITKTests::TestConnectedThreshold(const std::string& filename, const std::string& outputDir) {
    // Region-growing segmentation using itk::ConnectedThresholdImageFilter
    std::cout << "--- [ITK] Connected Threshold Segmentation ---" << std::endl;

    using PixelType = signed short;
    const unsigned int Dimension = 3;
    using ImageType = itk::Image<PixelType, Dimension>;
    using ReaderType = itk::ImageFileReader<ImageType>;
    using FilterType = itk::ConnectedThresholdImageFilter<ImageType, ImageType>;
    using WriterType = itk::ImageFileWriter<ImageType>;

    ReaderType::Pointer reader = ReaderType::New();
    reader->SetFileName(filename);
    ImageIOType::Pointer gdcmIO = ImageIOType::New();
    reader->SetImageIO(gdcmIO);

    try {
        reader->Update();
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Exception: " << err << std::endl;
        return;
    }

    ImageType::Pointer inputImage = reader->GetOutput();
    const ImageType::SizeType size = inputImage->GetLargestPossibleRegion().GetSize();
    if (size[0] == 0 || size[1] == 0 || size[2] == 0) {
        std::cerr << "Input volume has zero size; cannot seed region grower." << std::endl;
        return;
    }

    ImageType::IndexType seed = {};
    seed[0] = size[0] / 2;
    seed[1] = size[1] / 2;
    seed[2] = size[2] / 2;

    FilterType::Pointer grower = FilterType::New();
    grower->SetInput(inputImage);
    grower->AddSeed(seed);
    grower->SetLower(50);
    grower->SetUpper(400);
    grower->SetReplaceValue(1024);

    WriterType::Pointer writer = WriterType::New();
    writer->SetFileName(JoinPath(outputDir, "itk_connected_threshold.dcm"));
    writer->SetInput(grower->GetOutput());
    writer->SetImageIO(gdcmIO);

    try {
        writer->Update();
        std::cout << "Saved connected threshold mask (seed "
                  << seed[0] << "," << seed[1] << "," << seed[2]
                  << ") to '" << writer->GetFileName() << "'" << std::endl;
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Write Exception: " << err << std::endl;
    }
}

void ITKTests::TestOtsuSegmentation(const std::string& filename, const std::string& outputDir) {
    // Automatic single-threshold segmentation using Otsu's method
    std::cout << "--- [ITK] Otsu Segmentation ---" << std::endl;

    using PixelType = signed short;
    const unsigned int Dimension = 3;
    using ImageType = itk::Image<PixelType, Dimension>;
    using ReaderType = itk::ImageFileReader<ImageType>;
    using OtsuType = itk::OtsuThresholdImageFilter<ImageType, ImageType>;
    using WriterType = itk::ImageFileWriter<ImageType>;

    ReaderType::Pointer reader = ReaderType::New();
    reader->SetFileName(filename);
    ImageIOType::Pointer gdcmIO = ImageIOType::New();
    reader->SetImageIO(gdcmIO);

    try {
        reader->Update();
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Exception: " << err << std::endl;
        return;
    }

    OtsuType::Pointer otsu = OtsuType::New();
    otsu->SetInput(reader->GetOutput());
    otsu->SetInsideValue(1000);
    otsu->SetOutsideValue(0);

    WriterType::Pointer writer = WriterType::New();
    writer->SetFileName(JoinPath(outputDir, "itk_otsu.dcm"));
    writer->SetInput(otsu->GetOutput());
    writer->SetImageIO(gdcmIO);

    try {
        writer->Update();
        std::cout << "Saved to '" << writer->GetFileName() << "'" << std::endl;
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Write Exception: " << err << std::endl;
    }
}

void ITKTests::TestAnisotropicDenoise(const std::string& filename, const std::string& outputDir) {
    // Perform curvature anisotropic diffusion for edge-preserving smoothing
    std::cout << "--- [ITK] Curvature Anisotropic Diffusion ---" << std::endl;

    using InputPixelType = signed short;
    using FloatPixelType = float;
    const unsigned int Dimension = 3;
    using InputImageType = itk::Image<InputPixelType, Dimension>;
    using FloatImageType = itk::Image<FloatPixelType, Dimension>;
    using ReaderType = itk::ImageFileReader<InputImageType>;
    using CastToFloatType = itk::CastImageFilter<InputImageType, FloatImageType>;
    using DenoiseType = itk::CurvatureAnisotropicDiffusionImageFilter<FloatImageType, FloatImageType>;
    using CastToShortType = itk::CastImageFilter<FloatImageType, InputImageType>;
    using WriterType = itk::ImageFileWriter<InputImageType>;

    ReaderType::Pointer reader = ReaderType::New();
    reader->SetFileName(filename);
    ImageIOType::Pointer gdcmIO = ImageIOType::New();
    reader->SetImageIO(gdcmIO);

    try {
        reader->Update();
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Exception: " << err << std::endl;
        return;
    }

    CastToFloatType::Pointer castToFloat = CastToFloatType::New();
    castToFloat->SetInput(reader->GetOutput());

    DenoiseType::Pointer filter = DenoiseType::New();
    filter->SetInput(castToFloat->GetOutput());
    filter->SetTimeStep(0.0625);
    filter->SetConductanceParameter(2.0);
    filter->SetNumberOfIterations(5);

    CastToShortType::Pointer castBack = CastToShortType::New();
    castBack->SetInput(filter->GetOutput());

    WriterType::Pointer writer = WriterType::New();
    writer->SetFileName(JoinPath(outputDir, "itk_aniso.dcm"));
    writer->SetInput(castBack->GetOutput());
    writer->SetImageIO(gdcmIO);

    try {
        writer->Update();
        std::cout << "Saved to '" << writer->GetFileName() << "'" << std::endl;
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Write Exception: " << err << std::endl;
    }
}

void ITKTests::TestMaximumIntensityProjection(const std::string& filename, const std::string& outputDir) {
    // Generate a simple axial maximum intensity projection and save as PNG
    std::cout << "--- [ITK] Maximum Intensity Projection ---" << std::endl;

    using PixelType = signed short;
    using InputImageType = itk::Image<PixelType, 3>;
    using OutputImageType = itk::Image<unsigned char, 2>;
    using ReaderType = itk::ImageFileReader<InputImageType>;
    using ProjectType = itk::MaximumProjectionImageFilter<InputImageType, OutputImageType>;
    using RescaleType = itk::RescaleIntensityImageFilter<OutputImageType, OutputImageType>;
    using WriterType = itk::ImageFileWriter<OutputImageType>;

    ReaderType::Pointer reader = ReaderType::New();
    reader->SetFileName(filename);
    ImageIOType::Pointer gdcmIO = ImageIOType::New();
    reader->SetImageIO(gdcmIO);

    try {
        reader->Update();
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Exception: " << err << std::endl;
        return;
    }

    ProjectType::Pointer mip = ProjectType::New();
    mip->SetInput(reader->GetOutput());
    mip->SetProjectionDimension(2);

    RescaleType::Pointer rescale = RescaleType::New();
    rescale->SetInput(mip->GetOutput());
    rescale->SetOutputMinimum(0);
    rescale->SetOutputMaximum(255);

    WriterType::Pointer writer = WriterType::New();
    writer->SetFileName(JoinPath(outputDir, "itk_mip.png"));
    writer->SetInput(rescale->GetOutput());
    writer->SetImageIO(itk::PNGImageIO::New());

    try {
        writer->Update();
        std::cout << "Saved axial MIP PNG to '" << writer->GetFileName() << "'" << std::endl;
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Write Exception: " << err << std::endl;
    }
}

void ITKTests::TestNiftiExport(const std::string& filename, const std::string& outputDir) {
    // Rescale intensities and export the 3D volume to compressed NIfTI
    std::cout << "--- [ITK] NIfTI Export ---" << std::endl;

    using PixelType = signed short;
    const unsigned int Dimension = 3;
    using ImageType = itk::Image<PixelType, Dimension>;
    using ReaderType = itk::ImageFileReader<ImageType>;
    using RescaleType = itk::RescaleIntensityImageFilter<ImageType, ImageType>;
    using WriterType = itk::ImageFileWriter<ImageType>;

    ReaderType::Pointer reader = ReaderType::New();
    reader->SetFileName(filename);
    ImageIOType::Pointer gdcmIO = ImageIOType::New();
    reader->SetImageIO(gdcmIO);

    try {
        reader->Update();
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Exception: " << err << std::endl;
        return;
    }

    RescaleType::Pointer rescale = RescaleType::New();
    rescale->SetInput(reader->GetOutput());
    rescale->SetOutputMinimum(0);
    rescale->SetOutputMaximum(4095);

    WriterType::Pointer writer = WriterType::New();
    writer->SetFileName(JoinPath(outputDir, "itk_volume.nii.gz"));
    writer->SetInput(rescale->GetOutput());
    writer->UseCompressionOn();
    writer->SetImageIO(itk::NiftiImageIO::New());

    try {
        writer->Update();
        std::cout << "Saved to '" << writer->GetFileName() << "'" << std::endl;
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Write Exception: " << err << std::endl;
    }
}

#else
namespace ITKTests {
void TestCannyEdgeDetection(const std::string&, const std::string&) { std::cout << "ITK not enabled." << std::endl; }
void TestGaussianSmoothing(const std::string&, const std::string&) {}
void TestBinaryThresholding(const std::string&, const std::string&) {}
void TestResampling(const std::string&, const std::string&) {}
void TestAdaptiveHistogram(const std::string&, const std::string&) {}
void TestSliceExtraction(const std::string&, const std::string&) {}
void TestMedianFilter(const std::string&, const std::string&) {}
void TestNRRDExport(const std::string&, const std::string&) {}
void TestConnectedThreshold(const std::string&, const std::string&) {}
void TestOtsuSegmentation(const std::string&, const std::string&) {}
void TestAnisotropicDenoise(const std::string&, const std::string&) {}
void TestMaximumIntensityProjection(const std::string&, const std::string&) {}
void TestNiftiExport(const std::string&, const std::string&) {}
} // namespace ITKTests
#endif
