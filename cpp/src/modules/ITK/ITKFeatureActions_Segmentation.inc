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


void ITKTests::TestDistanceMapAndMorphology(const std::string& filename, const std::string& outputDir) {
    // Build a binary mask, compute its signed distance map, and run a simple morphological closing
    std::cout << "--- [ITK] Distance Map + Morphology ---" << std::endl;

    using InputPixelType = signed short;
    using InputImageType = itk::Image<InputPixelType, 3>;
    using MaskImageType = itk::Image<unsigned char, 3>;
    using FloatImageType = itk::Image<float, 3>;

    using ReaderType = itk::ImageFileReader<InputImageType>;
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

    using OtsuType = itk::OtsuThresholdImageFilter<InputImageType, MaskImageType>;
    OtsuType::Pointer otsu = OtsuType::New();
    otsu->SetInput(reader->GetOutput());
    otsu->SetInsideValue(1);
    otsu->SetOutsideValue(0);

    using DistanceType = itk::SignedMaurerDistanceMapImageFilter<MaskImageType, FloatImageType>;
    DistanceType::Pointer distance = DistanceType::New();
    distance->SetInput(otsu->GetOutput());
    distance->SetUseImageSpacing(true);
    distance->SetSquaredDistance(false);

    using StatsType = itk::StatisticsImageFilter<FloatImageType>;
    StatsType::Pointer stats = StatsType::New();
    stats->SetInput(distance->GetOutput());

    using StructuringType = itk::BinaryBallStructuringElement<unsigned char, 3>;
    StructuringType kernel;
    kernel.SetRadius(1);
    kernel.CreateStructuringElement();

    using DilateType = itk::BinaryDilateImageFilter<MaskImageType, MaskImageType, StructuringType>;
    using ErodeType = itk::BinaryErodeImageFilter<MaskImageType, MaskImageType, StructuringType>;

    DilateType::Pointer dilate = DilateType::New();
    dilate->SetInput(otsu->GetOutput());
    dilate->SetKernel(kernel);
    dilate->SetForegroundValue(1);

    ErodeType::Pointer erode = ErodeType::New();
    erode->SetInput(dilate->GetOutput());
    erode->SetKernel(kernel);
    erode->SetForegroundValue(1);

    using FloatWriter = itk::ImageFileWriter<FloatImageType>;
    FloatWriter::Pointer distanceWriter = FloatWriter::New();
    distanceWriter->SetFileName(JoinPath(outputDir, "itk_distance_map.nrrd"));
    distanceWriter->SetInput(distance->GetOutput());
    distanceWriter->SetImageIO(itk::NrrdImageIO::New());
    distanceWriter->UseCompressionOn();

    using MaskWriter = itk::ImageFileWriter<MaskImageType>;
    MaskWriter::Pointer maskWriter = MaskWriter::New();
    maskWriter->SetFileName(JoinPath(outputDir, "itk_morphology_mask.dcm"));
    maskWriter->SetInput(erode->GetOutput());
    maskWriter->SetImageIO(gdcmIO);

    try {
        stats->Update();
        distanceWriter->Update();
        maskWriter->Update();
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Write Exception: " << err << std::endl;
        return;
    }

    const std::string reportPath = JoinPath(outputDir, "itk_distance_stats.txt");
    std::ofstream out(reportPath, std::ios::out | std::ios::trunc);
    out << "Min=" << stats->GetMinimum() << "\n";
    out << "Max=" << stats->GetMaximum() << "\n";
    out << "Mean=" << stats->GetMean() << "\n";
    out << "Variance=" << stats->GetVariance() << "\n";
    out.close();

    std::cout << "Saved distance map + morphology outputs (report: " << reportPath << ")" << std::endl;
}


void ITKTests::TestLabelStatistics(const std::string& filename, const std::string& outputDir) {
    // Compute per-label statistics after connected components on an Otsu mask
    std::cout << "--- [ITK] Label Statistics ---" << std::endl;

    using InputPixelType = signed short;
    using InputImageType = itk::Image<InputPixelType, 3>;
    using MaskImageType = itk::Image<unsigned char, 3>;
    using LabelImageType = itk::Image<unsigned int, 3>;

    using ReaderType = itk::ImageFileReader<InputImageType>;
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

    using OtsuType = itk::OtsuThresholdImageFilter<InputImageType, MaskImageType>;
    OtsuType::Pointer otsu = OtsuType::New();
    otsu->SetInput(reader->GetOutput());
    otsu->SetInsideValue(1);
    otsu->SetOutsideValue(0);

    using ConnectedType = itk::ConnectedComponentImageFilter<MaskImageType, LabelImageType>;
    ConnectedType::Pointer connected = ConnectedType::New();
    connected->SetInput(otsu->GetOutput());

    using RelabelType = itk::RelabelComponentImageFilter<LabelImageType, LabelImageType>;
    RelabelType::Pointer relabel = RelabelType::New();
    relabel->SetInput(connected->GetOutput());
    relabel->SetMinimumObjectSize(10);

    using StatsType = itk::LabelStatisticsImageFilter<InputImageType, LabelImageType>;
    StatsType::Pointer stats = StatsType::New();
    stats->SetInput(reader->GetOutput());
    stats->SetLabelInput(relabel->GetOutput());

    using LabelWriter = itk::ImageFileWriter<LabelImageType>;
    LabelWriter::Pointer labelWriter = LabelWriter::New();
    labelWriter->SetFileName(JoinPath(outputDir, "itk_labels.nrrd"));
    labelWriter->SetInput(relabel->GetOutput());
    labelWriter->UseCompressionOn();
    labelWriter->SetImageIO(itk::NrrdImageIO::New());

    try {
        stats->Update();
        labelWriter->Update();
    } catch (itk::ExceptionObject& err) {
        std::cerr << "ITK Write Exception: " << err << std::endl;
        return;
    }

    const std::string reportPath = JoinPath(outputDir, "itk_label_stats.txt");
    std::ofstream out(reportPath, std::ios::out | std::ios::trunc);
    const auto& labels = stats->GetValidLabelValues();
    for (const auto& label : labels) {
        if (label == 0) continue; // skip background
        out << "Label=" << label
            << ",Count=" << stats->GetCount(label)
            << ",Min=" << stats->GetMinimum(label)
            << ",Max=" << stats->GetMaximum(label)
            << ",Mean=" << stats->GetMean(label)
            << ",Sigma=" << stats->GetSigma(label)
            << "\n";
    }
    out.close();

    std::cout << "Label statistics written to '" << reportPath << "' with "
              << (labels.size() > 0 ? labels.size() - 1 : 0) << " object(s)" << std::endl;
}
