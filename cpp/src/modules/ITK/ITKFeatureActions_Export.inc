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


void ITKTests::TestVectorVolumeExport(const std::string& filename, const std::string& outputDir) {
    // Build a 2-component vector volume and export to NRRD
    std::cout << "--- [ITK] Vector / Multi-Component Volume ---" << std::endl;

    using PixelType = signed short;
    const unsigned int Dimension = 3;
    using ImageType = itk::Image<PixelType, Dimension>;
    using VectorImageType = itk::VectorImage<PixelType, Dimension>;
    using ReaderType = itk::ImageFileReader<ImageType>;
    using GaussianType = itk::DiscreteGaussianImageFilter<ImageType, ImageType>;
    using ComposeType = itk::ComposeImageFilter<ImageType, VectorImageType>;
    using WriterType = itk::ImageFileWriter<VectorImageType>;

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

    GaussianType::Pointer blur = GaussianType::New();
    blur->SetInput(reader->GetOutput());
    blur->SetVariance(2.0);

    ComposeType::Pointer compose = ComposeType::New();
    compose->SetInput1(reader->GetOutput());
    compose->SetInput2(blur->GetOutput());

    WriterType::Pointer writer = WriterType::New();
    writer->SetFileName(JoinPath(outputDir, "itk_vector.nrrd"));
    writer->SetInput(compose->GetOutput());
    writer->SetImageIO(itk::NrrdImageIO::New());
    writer->UseCompressionOn();
    try {
        writer->Update();
    } catch (itk::ExceptionObject& err) {
        std::cerr << "Failed to write vector volume: " << err << std::endl;
        return;
    }

    std::cout << "Multi-component volume written to '" << writer->GetFileName() << "'" << std::endl;
}


void ITKTests::TestDicomSeriesWrite(const std::string& filename, const std::string& outputDir) {
    // Write a fresh DICOM series from the loaded volume with new UIDs
    std::cout << "--- [ITK] DICOM Series Write ---" << std::endl;

    using PixelType = signed short;
    const unsigned int Dimension = 3;
    using ImageType = itk::Image<PixelType, Dimension>;
    using ReaderType = itk::ImageFileReader<ImageType>;
    using WriterType = itk::ImageSeriesWriter<ImageType, itk::Image<PixelType, 2>>;

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

    ImageType::RegionType region = reader->GetOutput()->GetLargestPossibleRegion();
    const auto size = region.GetSize();

    std::filesystem::path seriesDir = std::filesystem::path(outputDir) / "itk_series";
    std::filesystem::create_directories(seriesDir);

    itk::NumericSeriesFileNames::Pointer names = itk::NumericSeriesFileNames::New();
    names->SetSeriesFormat((seriesDir / "IM%04d.dcm").string());
    names->SetStartIndex(1);
    names->SetEndIndex(static_cast<int>(size[2]));
    names->SetIncrementIndex(1);

    gdcm::UIDGenerator uidGen;
    const std::string studyUID = uidGen.Generate();
    const std::string seriesUID = uidGen.Generate();

    WriterType::Pointer writer = WriterType::New();
    writer->SetInput(reader->GetOutput());
    writer->SetImageIO(gdcmIO);
    writer->SetFileNames(names->GetFileNames());

    WriterType::DictionaryArrayType dictArray;
    std::vector<std::unique_ptr<itk::MetaDataDictionary>> dictOwners;
    for (unsigned int i = 0; i < size[2]; ++i) {
        auto dictPtr = std::make_unique<itk::MetaDataDictionary>();
        itk::EncapsulateMetaData<std::string>(*dictPtr, "0008|0016", "1.2.840.10008.5.1.4.1.1.2");
        itk::EncapsulateMetaData<std::string>(*dictPtr, "0008|0018", uidGen.Generate());
        itk::EncapsulateMetaData<std::string>(*dictPtr, "0020|000D", studyUID);
        itk::EncapsulateMetaData<std::string>(*dictPtr, "0020|000E", seriesUID);
        itk::EncapsulateMetaData<std::string>(*dictPtr, "0020|0013", std::to_string(i + 1));
        dictArray.push_back(dictPtr.get());
        dictOwners.push_back(std::move(dictPtr));
    }
    writer->SetMetaDataDictionaryArray(&dictArray);

    try {
        writer->Update();
    } catch (itk::ExceptionObject& err) {
        std::cerr << "Failed to write DICOM series: " << err << std::endl;
        return;
    }

    const std::string reportPath = JoinPath(outputDir, "itk_series.txt");
    std::ofstream out(reportPath, std::ios::out | std::ios::trunc);
    out << "Slices=" << size[2] << "\n";
    out << "SeriesUID=" << seriesUID << "\n";
    out << "StudyUID=" << studyUID << "\n";
    out << "OutputDir=" << seriesDir << "\n";
    out.close();

    std::cout << "Wrote DICOM series (" << size[2] << " slices) to " << seriesDir << std::endl;
}
