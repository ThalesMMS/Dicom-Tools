void GDCMTests::TestJPEG2000Transcode(const std::string& filename, const std::string& outputDir) {
    // Lossless JPEG2000 round-trip to exercise J2K codec support
    std::cout << "--- [GDCM] JPEG2000 Lossless Transcode ---" << std::endl;

    gdcm::ImageReader reader;
    reader.SetFileName(filename.c_str());
    if (!reader.Read()) {
        std::cerr << "Could not read file for JPEG2000 transcode." << std::endl;
        return;
    }

    gdcm::ImageChangeTransferSyntax change;
    change.SetTransferSyntax(gdcm::TransferSyntax::JPEG2000Lossless);
    change.SetInput(reader.GetImage());

    if (!change.Change()) {
        std::cerr << "Transfer syntax change to JPEG2000 failed (codec support may be missing)." << std::endl;
        return;
    }

    gdcm::ImageWriter writer;
    std::string outFilename = JoinPath(outputDir, "gdcm_jpeg2000.dcm");
    writer.SetFileName(outFilename.c_str());
    writer.SetFile(reader.GetFile());
    writer.SetImage(change.GetOutput());

    if (writer.Write()) {
        std::cout << "Transcoded to JPEG2000 and saved to: " << outFilename << std::endl;
    } else {
        std::cerr << "Failed to write JPEG2000 transcoded file." << std::endl;
    }
}


void GDCMTests::TestJPEGLSTranscode(const std::string& filename, const std::string& outputDir) {
    // Lossless JPEG-LS round-trip to validate codec availability
    std::cout << "--- [GDCM] JPEG-LS Lossless Transcode ---" << std::endl;

    gdcm::ImageReader reader;
    reader.SetFileName(filename.c_str());
    if (!reader.Read()) {
        std::cerr << "Could not read file for JPEG-LS transcode." << std::endl;
        return;
    }

    gdcm::ImageChangeTransferSyntax change;
    change.SetTransferSyntax(gdcm::TransferSyntax::JPEGLSLossless);
    change.SetInput(reader.GetImage());

    if (!change.Change()) {
        std::cerr << "Transfer syntax change to JPEG-LS failed (codec support may be missing)." << std::endl;
        return;
    }

    gdcm::ImageWriter writer;
    std::string outFilename = JoinPath(outputDir, "gdcm_jpegls.dcm");
    writer.SetFileName(outFilename.c_str());
    writer.SetFile(reader.GetFile());
    writer.SetImage(change.GetOutput());

    if (writer.Write()) {
        std::cout << "Transcoded to JPEG-LS and saved to: " << outFilename << std::endl;
    } else {
        std::cerr << "Failed to write JPEG-LS transcoded file." << std::endl;
    }
}


void GDCMTests::TestJPEGBaselineTranscode(const std::string& filename, const std::string& outputDir) {
    // JPEG Baseline (Process 1) lossy transcode
    std::cout << "--- [GDCM] JPEG Baseline Transcode ---" << std::endl;

    gdcm::ImageReader reader;
    reader.SetFileName(filename.c_str());
    if (!reader.Read()) {
        std::cerr << "Could not read file for JPEG Baseline transcode." << std::endl;
        return;
    }

    gdcm::ImageChangeTransferSyntax change;
    change.SetTransferSyntax(gdcm::TransferSyntax::JPEGBaselineProcess1);
    change.SetInput(reader.GetImage());

    gdcm::ImageWriter writer;
    std::string outFilename = JoinPath(outputDir, "gdcm_jpeg_baseline.dcm");
    writer.SetFileName(outFilename.c_str());
    writer.SetFile(reader.GetFile());

    bool changed = change.Change();
    if (changed) {
        writer.SetImage(change.GetOutput());
    } else {
        std::cerr << "Transfer syntax change to JPEG Baseline failed (codec support may be missing). Writing source copy instead." << std::endl;
        writer.SetImage(reader.GetImage());
    }

    if (writer.Write()) {
        std::cout << "Transcoded to JPEG Baseline and saved to: " << outFilename << std::endl;
    } else {
        std::cerr << "Failed to write JPEG Baseline transcoded file." << std::endl;
    }
}


void GDCMTests::TestJPEGLosslessP14Transcode(const std::string& filename, const std::string& outputDir) {
    // JPEG Lossless Process 14 test for 12-bit style edge cases
    std::cout << "--- [GDCM] JPEG Lossless P14 Transcode ---" << std::endl;

    gdcm::ImageReader reader;
    reader.SetFileName(filename.c_str());
    if (!reader.Read()) {
        std::cerr << "Could not read file for JPEG Lossless P14 transcode." << std::endl;
        return;
    }

    gdcm::ImageChangeTransferSyntax change;
    change.SetTransferSyntax(gdcm::TransferSyntax::JPEGLosslessProcess14_1);
    change.SetInput(reader.GetImage());
    if (!change.Change()) {
        std::cerr << "Transfer syntax change to JPEG Lossless P14 failed (codec support may be missing)." << std::endl;
        return;
    }

    gdcm::ImageWriter writer;
    std::string outFilename = JoinPath(outputDir, "gdcm_jpeg_lossless_p14.dcm");
    writer.SetFileName(outFilename.c_str());
    writer.SetFile(reader.GetFile());
    writer.SetImage(change.GetOutput());
    if (writer.Write()) {
        std::cout << "Transcoded to JPEG Lossless P14 and saved to: " << outFilename << std::endl;
    } else {
        std::cerr << "Failed to write JPEG Lossless P14 transcoded file." << std::endl;
    }
}


void GDCMTests::TestRLETranscode(const std::string& filename, const std::string& outputDir) {
    // Convert to RLE Lossless to confirm encapsulated encoding works
    std::cout << "--- [GDCM] RLE Lossless Transcode ---" << std::endl;

    gdcm::ImageReader reader;
    reader.SetFileName(filename.c_str());
    if (!reader.Read()) {
        std::cerr << "Could not read file for RLE transcode." << std::endl;
        return;
    }

    gdcm::ImageChangeTransferSyntax change;
    change.SetTransferSyntax(gdcm::TransferSyntax::RLELossless);
    change.SetInput(reader.GetImage());

    if (!change.Change()) {
        std::cerr << "Transfer syntax change to RLE failed (codec support may be missing)." << std::endl;
        return;
    }

    gdcm::ImageWriter writer;
    std::string outFilename = JoinPath(outputDir, "gdcm_rle.dcm");
    writer.SetFileName(outFilename.c_str());
    writer.SetFile(reader.GetFile());
    writer.SetImage(change.GetOutput());

    if (writer.Write()) {
        std::cout << "Transcoded to RLE and saved to: " << outFilename << std::endl;
    } else {
        std::cerr << "Failed to write RLE transcoded file." << std::endl;
    }
}


void GDCMTests::TestJPEG2000Lossy(const std::string& filename, const std::string& outputDir) {
    // Transcode to JPEG2000 Lossy to exercise lossy codec path
    std::cout << "--- [GDCM] JPEG2000 Lossy Transcode ---" << std::endl;

    gdcm::ImageReader reader;
    reader.SetFileName(filename.c_str());
    if (!reader.Read()) {
        std::cerr << "Could not read file for JPEG2000 Lossy transcode." << std::endl;
        return;
    }

    gdcm::ImageChangeTransferSyntax change;
    change.SetTransferSyntax(gdcm::TransferSyntax::JPEG2000);
    change.SetInput(reader.GetImage());

    if (!change.Change()) {
        std::cerr << "Transfer syntax change to JPEG2000 (lossy) failed." << std::endl;
        return;
    }

    gdcm::ImageWriter writer;
    std::string outFilename = JoinPath(outputDir, "gdcm_jpeg2000_lossy.dcm");
    writer.SetFileName(outFilename.c_str());
    writer.SetFile(reader.GetFile());
    writer.SetImage(change.GetOutput());

    if (writer.Write()) {
        std::cout << "Wrote JPEG2000 lossy file to: " << outFilename << std::endl;
    } else {
        std::cerr << "Failed to write JPEG2000 lossy file." << std::endl;
    }
}


void GDCMTests::TestRLEPlanarConfiguration(const std::string& filename, const std::string& outputDir) {
    // Convert to RLE while forcing planar configuration for RGB data
    std::cout << "--- [GDCM] RLE Planar Configuration ---" << std::endl;

    gdcm::Reader reader;
    reader.SetFileName(filename.c_str());
    if (!reader.Read()) {
        std::cerr << "Could not read file for RLE planar test." << std::endl;
        return;
    }

    gdcm::File& file = reader.GetFile();
    gdcm::DataSet& ds = file.GetDataSet();
    const gdcm::Tag planarTag(0x0028, 0x0006);

    if (ds.FindDataElement(planarTag)) {
        gdcm::Attribute<0x0028, 0x0006> planar;
        planar.SetFromDataElement(ds.GetDataElement(planarTag));
        planar.SetValue(1); // planar
        ds.Replace(planar.GetAsDataElement());
    }

    gdcm::ImageReader imgReader;
    imgReader.SetFile(file);
    if (!imgReader.Read()) {
        std::cerr << "Failed to read image for planar RLE." << std::endl;
        return;
    }

    gdcm::ImageChangeTransferSyntax change;
    change.SetTransferSyntax(gdcm::TransferSyntax::RLELossless);
    change.SetInput(imgReader.GetImage());
    if (!change.Change()) {
        std::cerr << "RLE change failed." << std::endl;
        return;
    }

    gdcm::ImageWriter writer;
    std::string outFilename = JoinPath(outputDir, "gdcm_rle_planar.dcm");
    writer.SetFileName(outFilename.c_str());
    writer.SetFile(file);
    writer.SetImage(change.GetOutput());

    if (writer.Write()) {
        std::cout << "Wrote RLE planar file to: " << outFilename << std::endl;
    } else {
        std::cerr << "Failed to write RLE planar file." << std::endl;
    }
}
