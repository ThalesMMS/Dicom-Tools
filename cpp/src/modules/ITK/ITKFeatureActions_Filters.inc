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
