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
