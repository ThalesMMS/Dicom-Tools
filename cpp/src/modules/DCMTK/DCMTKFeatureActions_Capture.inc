void DCMTKTests::TestSecondaryCapture(const std::string& sourceForMetadata, const std::string& outputDir) {
    // Create a brand new Secondary Capture instance with synthetic pixels
    std::cout << "--- [DCMTK] Secondary Capture Creation ---" << std::endl;
#ifdef USE_DCMTK
    DcmFileFormat source;
    std::string patientName = "SC^Demo^Patient";
    std::string patientId = "SC-001";
    std::string studyUID;
    std::string seriesUID;

    if (source.loadFile(sourceForMetadata.c_str()).good()) {
        OFString val;
        if (source.getDataset()->findAndGetOFString(DCM_PatientName, val).good()) {
            patientName = val.c_str();
        }
        if (source.getDataset()->findAndGetOFString(DCM_PatientID, val).good()) {
            patientId = val.c_str();
        }
        if (source.getDataset()->findAndGetOFString(DCM_StudyInstanceUID, val).good()) {
            studyUID = val.c_str();
        }
        if (source.getDataset()->findAndGetOFString(DCM_SeriesInstanceUID, val).good()) {
            seriesUID = val.c_str();
        }
    }

    char studyUidBuf[100];
    char seriesUidBuf[100];
    char sopUidBuf[100];
    if (studyUID.empty()) {
        dcmGenerateUniqueIdentifier(studyUidBuf, SITE_STUDY_UID_ROOT);
        studyUID = studyUidBuf;
    }
    if (seriesUID.empty()) {
        dcmGenerateUniqueIdentifier(seriesUidBuf, SITE_SERIES_UID_ROOT);
        seriesUID = seriesUidBuf;
    }
    dcmGenerateUniqueIdentifier(sopUidBuf, SITE_INSTANCE_UID_ROOT);

    DcmFileFormat scFile;
    DcmDataset* ds = scFile.getDataset();
    ds->putAndInsertString(DCM_SpecificCharacterSet, "ISO_IR 100");
    ds->putAndInsertString(DCM_SOPClassUID, UID_SecondaryCaptureImageStorage);
    ds->putAndInsertString(DCM_SOPInstanceUID, sopUidBuf);
    ds->putAndInsertString(DCM_StudyInstanceUID, studyUID.c_str());
    ds->putAndInsertString(DCM_SeriesInstanceUID, seriesUID.c_str());
    ds->putAndInsertString(DCM_PatientName, patientName.c_str());
    ds->putAndInsertString(DCM_PatientID, patientId.c_str());
    ds->putAndInsertString(DCM_Modality, "OT");
    ds->putAndInsertUint16(DCM_InstanceNumber, 1);

    const Uint16 rows = 128;
    const Uint16 cols = 128;
    ds->putAndInsertUint16(DCM_Rows, rows);
    ds->putAndInsertUint16(DCM_Columns, cols);
    ds->putAndInsertUint16(DCM_BitsAllocated, 8);
    ds->putAndInsertUint16(DCM_BitsStored, 8);
    ds->putAndInsertUint16(DCM_HighBit, 7);
    ds->putAndInsertUint16(DCM_SamplesPerPixel, 1);
    ds->putAndInsertUint16(DCM_PixelRepresentation, 0);
    ds->putAndInsertString(DCM_PhotometricInterpretation, "MONOCHROME2");

    std::vector<Uint8> pixels(static_cast<size_t>(rows) * static_cast<size_t>(cols), 0);
    for (Uint16 y = 0; y < rows; ++y) {
        for (Uint16 x = 0; x < cols; ++x) {
            const double normX = static_cast<double>(x) / static_cast<double>(cols);
            const double normY = static_cast<double>(y) / static_cast<double>(rows);
            pixels[y * cols + x] = static_cast<Uint8>(255.0 * (0.5 * normX + 0.5 * normY));
        }
    }
    ds->putAndInsertUint8Array(DCM_PixelData, pixels.data(), static_cast<unsigned long>(pixels.size()));

    const std::string outPath = JoinPath(outputDir, "dcmtk_secondary_capture.dcm");
    if (scFile.saveFile(outPath.c_str(), EXS_LittleEndianExplicit).bad()) {
        std::cerr << "Failed to write secondary capture file." << std::endl;
        return;
    }

    DcmFileFormat verify;
    if (verify.loadFile(outPath.c_str()).bad()) {
        std::cerr << "Could not reload secondary capture for validation." << std::endl;
        return;
    }

    Uint16 outRows = 0, outCols = 0;
    verify.getDataset()->findAndGetUint16(DCM_Rows, outRows);
    verify.getDataset()->findAndGetUint16(DCM_Columns, outCols);
    const Uint8* outPixels = nullptr;
    unsigned long outLen = 0;
    verify.getDataset()->findAndGetUint8Array(DCM_PixelData, outPixels, &outLen);

    const std::string reportPath = JoinPath(outputDir, "dcmtk_secondary_capture.txt");
    std::ofstream report(reportPath, std::ios::out | std::ios::trunc);
    report << "Rows=" << outRows << "\n";
    report << "Columns=" << outCols << "\n";
    report << "PixelBytes=" << outLen << "\n";
    report << "PatientName=" << patientName << "\n";
    report << "PatientID=" << patientId << "\n";
    report.close();

    std::cout << "Wrote secondary capture to '" << outPath << "' (" << outRows << "x" << outCols << ")"
              << std::endl;
#else
    (void)sourceForMetadata;
    (void)outputDir;
    std::cout << "DCMTK not enabled." << std::endl;
#endif
}
