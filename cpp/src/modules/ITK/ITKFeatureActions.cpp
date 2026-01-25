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
#include <memory>

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
#include "itkSignedMaurerDistanceMapImageFilter.h"
#include "itkBinaryBallStructuringElement.h"
#include "itkBinaryDilateImageFilter.h"
#include "itkBinaryErodeImageFilter.h"
#include "itkStatisticsImageFilter.h"
#include "itkConnectedComponentImageFilter.h"
#include "itkRelabelComponentImageFilter.h"
#include "itkLabelStatisticsImageFilter.h"
#include "itkImageRegistrationMethodv4.h"
#include "itkMattesMutualInformationImageToImageMetricv4.h"
#include "itkRegularStepGradientDescentOptimizerv4.h"
#include "itkTranslationTransform.h"
#include "itkAffineTransform.h"
#include "itkCenteredTransformInitializer.h"
#include "itkResampleImageFilter.h"
#include "itkComposeImageFilter.h"
#include "itkVectorImage.h"
#include "itkImageSeriesWriter.h"
#include "itkNumericSeriesFileNames.h"
#include "gdcmUIDGenerator.h"

namespace {
std::string JoinPath(const std::string& base, const std::string& filename) {
    return (std::filesystem::path(base) / filename).string();
}

using ImageIOType = itk::GDCMImageIO;
} // namespace

#include "ITKFeatureActions_Filters.inc"
#include "ITKFeatureActions_Resample.inc"
#include "ITKFeatureActions_Segmentation.inc"
#include "ITKFeatureActions_Export.inc"
#include "ITKFeatureActions_Registration.inc"

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
void TestDistanceMapAndMorphology(const std::string&, const std::string&) {}
void TestLabelStatistics(const std::string&, const std::string&) {}
void TestRegistration(const std::string&, const std::string&) {}
void TestMutualInformationRegistration(const std::string&, const std::string&) {}
void TestVectorVolumeExport(const std::string&, const std::string&) {}
void TestDicomSeriesWrite(const std::string&, const std::string&) {}
} // namespace ITKTests
#endif
