void GDCMTests::TestPixelStatistics(const std::string& filename, const std::string& outputDir) {
    // Calculates min/max/mean of the pixel buffer for quick QC
    std::cout << "--- [GDCM] Pixel Statistics ---" << std::endl;

    gdcm::ImageReader reader;
    reader.SetFileName(filename.c_str());
    if (!reader.Read()) {
        std::cerr << "Could not read file for statistics." << std::endl;
        return;
    }

    const gdcm::Image& image = reader.GetImage();
    const unsigned long bufferLength = image.GetBufferLength();
    if (bufferLength == 0) {
        std::cerr << "Image buffer length is zero." << std::endl;
        return;
    }

    std::vector<char> buffer(bufferLength);
    if (!image.GetBuffer(buffer.data())) {
        std::cerr << "Failed to read pixel buffer for statistics." << std::endl;
        return;
    }

    const gdcm::PixelFormat& pf = image.GetPixelFormat();
    PixelStats stats;
    bool supported = true;
    switch (pf.GetScalarType()) {
        case gdcm::PixelFormat::UINT8:
            stats = CalculateStats<uint8_t>(buffer);
            break;
        case gdcm::PixelFormat::INT8:
            stats = CalculateStats<int8_t>(buffer);
            break;
        case gdcm::PixelFormat::UINT16:
            stats = CalculateStats<uint16_t>(buffer);
            break;
        case gdcm::PixelFormat::INT16:
            stats = CalculateStats<int16_t>(buffer);
            break;
        default:
            supported = false;
            stats = CalculateStats<uint8_t>(buffer);
            break;
    }

    std::string outFilename = JoinPath(outputDir, "gdcm_stats.txt");
    std::ofstream out(outFilename, std::ios::out | std::ios::trunc);
    if (!out.is_open()) {
        std::cerr << "Failed to open output for statistics: " << outFilename << std::endl;
        return;
    }

    out << "PixelCount=" << stats.count << "\n";
    out << "BitsAllocated=" << pf.GetBitsAllocated() << "\n";
    out << "SamplesPerPixel=" << pf.GetSamplesPerPixel() << "\n";
    out << "Min=" << stats.min << "\n";
    out << "Max=" << stats.max << "\n";
    out << "Mean=" << stats.mean << "\n";
    out << "ScalarTypeSupported=" << (supported ? "yes" : "fallback_uint8") << "\n";
    out.close();

    std::cout << "Wrote pixel statistics to: " << outFilename << std::endl;
}


void GDCMTests::TestPreviewExport(const std::string& filename, const std::string& outputDir) {
    // Convert the first slice to an 8-bit PGM preview for quick visualization
    std::cout << "--- [GDCM] Preview Export (PGM) ---" << std::endl;

    gdcm::ImageReader reader;
    reader.SetFileName(filename.c_str());
    if (!reader.Read()) {
        std::cerr << "Could not read file for preview export." << std::endl;
        return;
    }

    const gdcm::Image& image = reader.GetImage();
    const unsigned long bufferLength = image.GetBufferLength();
    if (bufferLength == 0) {
        std::cerr << "Image buffer length is zero, cannot create preview." << std::endl;
        return;
    }

    std::vector<char> buffer(bufferLength);
    if (!image.GetBuffer(buffer.data())) {
        std::cerr << "Failed to read pixel buffer for preview." << std::endl;
        return;
    }

    const gdcm::PixelFormat& pf = image.GetPixelFormat();
    std::string outPath = JoinPath(outputDir, "gdcm_preview.pgm");
    bool ok = false;
    switch (pf.GetScalarType()) {
        case gdcm::PixelFormat::UINT8:
            ok = WritePGMPreview<uint8_t>(image, buffer, outPath);
            break;
        case gdcm::PixelFormat::INT8:
            ok = WritePGMPreview<int8_t>(image, buffer, outPath);
            break;
        case gdcm::PixelFormat::UINT16:
            ok = WritePGMPreview<uint16_t>(image, buffer, outPath);
            break;
        case gdcm::PixelFormat::INT16:
            ok = WritePGMPreview<int16_t>(image, buffer, outPath);
            break;
        default:
            ok = WritePGMPreview<uint8_t>(image, buffer, outPath);
            break;
    }

    if (ok) {
        std::cout << "Wrote 8-bit preview to: " << outPath << std::endl;
    } else {
        std::cerr << "Failed to generate preview image." << std::endl;
    }
}
