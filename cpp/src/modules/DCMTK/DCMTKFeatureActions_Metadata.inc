void DCMTKTests::TestMetadataReport(const std::string& filename, const std::string& outputDir, bool jsonOutput) {
    // Export common identifying fields and transfer syntax for quick inspection
    std::cout << "--- [DCMTK] Metadata Report ---" << std::endl;
    DcmFileFormat fileformat;
    OFCondition status = fileformat.loadFile(filename.c_str());
    if (!status.good()) {
        std::cerr << "Error reading file for metadata report: " << status.text() << std::endl;
        return;
    }

    DcmDataset* dataset = fileformat.getDataset();
    std::map<std::string, std::string> fields;

    std::string outFile = JoinPath(outputDir, "dcmtk_metadata.txt");
    std::ofstream out(outFile, std::ios::out | std::ios::trunc);
    if (!out.is_open()) {
        std::cerr << "Failed to open metadata output: " << outFile << std::endl;
        return;
    }

    auto writeString = [&](const DcmTagKey& tag, const std::string& label) {
        OFString value;
        if (dataset->findAndGetOFString(tag, value).good()) {
            out << label << ": " << value << "\n";
            fields[label] = value.c_str();
        } else {
            out << label << ": (missing)\n";
        }
    };

    writeString(DCM_PatientName, "PatientName");
    writeString(DCM_PatientID, "PatientID");
    writeString(DCM_StudyInstanceUID, "StudyInstanceUID");
    writeString(DCM_SeriesInstanceUID, "SeriesInstanceUID");
    writeString(DCM_SOPInstanceUID, "SOPInstanceUID");
    writeString(DCM_Modality, "Modality");

    Uint16 rows = 0, cols = 0;
    if (dataset->findAndGetUint16(DCM_Rows, rows).good() && dataset->findAndGetUint16(DCM_Columns, cols).good()) {
        out << "Dimensions: " << cols << " x " << rows << "\n";
        fields["Rows"] = std::to_string(rows);
        fields["Columns"] = std::to_string(cols);
    }

    Sint32 frames = 0;
    if (dataset->findAndGetSint32(DCM_NumberOfFrames, frames).good()) {
        out << "NumberOfFrames: " << frames << "\n";
        fields["NumberOfFrames"] = std::to_string(frames);
    }

    const E_TransferSyntax originalXfer = dataset->getCurrentXfer();
    DcmXfer xfer(originalXfer);
    out << "TransferSyntax: " << xfer.getXferName() << " (" << xfer.getXferID() << ")\n";
    fields["TransferSyntaxUID"] = xfer.getXferID();
    fields["TransferSyntaxName"] = xfer.getXferName();

    out.close();
    std::cout << "Wrote metadata summary to '" << outFile << "'" << std::endl;

    if (jsonOutput) {
        const std::string jsonPath = JoinPath(outputDir, "dcmtk_metadata.json");
        std::ofstream jout(jsonPath, std::ios::out | std::ios::trunc);
        if (jout.is_open()) {
            jout << "{\n";
            size_t count = 0;
            for (const auto& kv : fields) {
                jout << "  \"" << EscapeJson(kv.first) << "\": \"" << EscapeJson(kv.second) << "\"";
                if (++count < fields.size()) {
                    jout << ",";
                }
                jout << "\n";
            }
            jout << "}\n";
            std::cout << "Wrote metadata JSON to '" << jsonPath << "'" << std::endl;
        } else {
            std::cerr << "Failed to open metadata JSON output: " << jsonPath << std::endl;
        }
    }
}


void DCMTKTests::TestRLEReencode(const std::string& filename, const std::string& outputDir) {
    // Attempt a lossless RLE transcode to exercise encapsulated pixel data handling
    std::cout << "--- [DCMTK] RLE Lossless Transcode ---" << std::endl;
    DcmRLEDecoderRegistration::registerCodecs();
    DcmRLEEncoderRegistration::registerCodecs();

    DcmFileFormat fileformat;
    OFCondition status = fileformat.loadFile(filename.c_str());
    if (!status.good()) {
        std::cerr << "Error reading file for RLE transcode: " << status.text() << std::endl;
        DcmRLEDecoderRegistration::cleanup();
        DcmRLEEncoderRegistration::cleanup();
        return;
    }

    const E_TransferSyntax targetXfer = EXS_RLELossless;
    if (fileformat.getDataset()->chooseRepresentation(targetXfer, nullptr).good() &&
        fileformat.getDataset()->canWriteXfer(targetXfer)) {
        std::string outFile = JoinPath(outputDir, "dcmtk_rle.dcm");
        status = fileformat.saveFile(outFile.c_str(), targetXfer);
        if (status.good()) {
            std::cout << "Saved RLE Lossless file to '" << outFile << "'" << std::endl;
        } else {
            std::cerr << "RLE save failed: " << status.text() << std::endl;
        }
    } else {
        std::cerr << "RLE representation not supported for this dataset." << std::endl;
    }

    DcmRLEDecoderRegistration::cleanup();
    DcmRLEEncoderRegistration::cleanup();
}


void DCMTKTests::TestJPEGBaseline(const std::string& filename, const std::string& outputDir) {
    // Save a JPEG Baseline (lossy) copy to check encoder/decoder availability
    std::cout << "--- [DCMTK] JPEG Baseline (Process 1) ---" << std::endl;
    DJDecoderRegistration::registerCodecs();
    DJEncoderRegistration::registerCodecs();

    DcmFileFormat fileformat;
    OFCondition status = fileformat.loadFile(filename.c_str());
    if (!status.good()) {
        std::cerr << "Error reading file for JPEG Baseline: " << status.text() << std::endl;
        DJDecoderRegistration::cleanup();
        DJEncoderRegistration::cleanup();
        return;
    }

    std::string outFile = JoinPath(outputDir, "dcmtk_jpeg_baseline.dcm");
    status = fileformat.saveFile(outFile.c_str(), EXS_JPEGProcess1);
    if (status.good()) {
        std::cout << "Saved JPEG Baseline copy to '" << outFile << "'" << std::endl;
    } else {
        std::cerr << "JPEG Baseline transcode failed: " << status.text() << std::endl;
    }

    DJDecoderRegistration::cleanup();
    DJEncoderRegistration::cleanup();
}


void DCMTKTests::TestBMPPreview(const std::string& filename, const std::string& outputDir) {
    // Produce an 8-bit BMP preview with simple windowing for monochrome images
    std::cout << "--- [DCMTK] BMP Preview ---" << std::endl;

    DicomImage image(filename.c_str());
    if (image.getStatus() != EIS_Normal) {
        std::cerr << "Could not load image for BMP export: " << DicomImage::getString(image.getStatus()) << std::endl;
        return;
    }

    if (image.isMonochrome()) {
        image.setMinMaxWindow();
    }

    std::string outFile = JoinPath(outputDir, "dcmtk_preview.bmp");
    if (image.writeBMP(outFile.c_str())) {
        std::cout << "Saved BMP preview to '" << outFile << "'" << std::endl;
    } else {
        std::cerr << "Failed to write BMP preview." << std::endl;
    }
}


void DCMTKTests::TestRawDump(const std::string& filename, const std::string& outputDir) {
    // Dump raw pixel buffer bytes for quick regression comparisons
    std::cout << "--- [DCMTK] Raw Pixel Dump ---" << std::endl;
    DicomImage image(filename.c_str());
    if (image.getStatus() != EIS_Normal) {
        std::cerr << "Could not load image for raw dump: " << DicomImage::getString(image.getStatus()) << std::endl;
        return;
    }

    const int bits = image.isMonochrome() ? 16 : 24;
    const unsigned long count = image.getOutputDataSize(bits);
    if (count == 0) {
        std::cerr << "No pixel data available for raw dump." << std::endl;
        return;
    }

    std::vector<char> buffer(count);
    if (!image.getOutputData(buffer.data(), count, bits)) {
        std::cerr << "Failed to extract output data buffer." << std::endl;
        return;
    }

    std::string outFile = JoinPath(outputDir, "dcmtk_raw_dump.bin");
    std::ofstream out(outFile, std::ios::binary | std::ios::out | std::ios::trunc);
    out.write(buffer.data(), static_cast<std::streamsize>(count));
    if (out.good()) {
        std::cout << "Wrote raw buffer (" << count << " bytes) to " << outFile << std::endl;
    } else {
        std::cerr << "Failed writing raw buffer." << std::endl;
    }
}


int DCMTKTests::ValidateDicomFile(const std::string& filename, const std::string& outputDir, bool jsonOutput) {
    std::cout << "--- [DCMTK] Validate DICOM ---" << std::endl;
#ifdef USE_DCMTK
    DcmFileFormat fileformat;
    ValidationResult result;
    OFCondition status = fileformat.loadFile(filename.c_str());
    if (status.bad()) {
        result.ok = false;
        result.errors.push_back(status.text());
    } else {
        result = ValidateDataset(fileformat.getDataset());
    }

    if (!WriteValidationReport(result, outputDir, jsonOutput)) {
        return 1;
    }

    std::cout << "Validation " << (result.ok ? "PASSED" : "FAILED")
              << " (reports: " << JoinPath(outputDir, "validate.txt") << ")" << std::endl;
    if (!result.ok) {
        for (const auto& err : result.errors) {
            std::cerr << "  - " << err << std::endl;
        }
    }
    return result.ok ? 0 : 1;
#else
    (void)filename;
    (void)outputDir;
    (void)jsonOutput;
    std::cerr << "DCMTK not enabled; validation unavailable." << std::endl;
    return 1;
#endif
}
