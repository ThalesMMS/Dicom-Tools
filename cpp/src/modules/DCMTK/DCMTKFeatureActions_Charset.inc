void DCMTKTests::TestCharacterSetRoundTrip(const std::string& outputDir) {
    // Build a UTF-8 dataset, write it, and confirm values round-trip intact
    std::cout << "--- [DCMTK] Character Set Round Trip ---" << std::endl;
#ifdef USE_DCMTK
    const std::string pnValue = "José da Silva^Têste";
    const std::string institution = "Clínica São Lucas";

    DcmFileFormat fileformat;
    DcmDataset* ds = fileformat.getDataset();
    ds->putAndInsertString(DCM_SpecificCharacterSet, "ISO_IR 192");
    ds->putAndInsertString(DCM_PatientName, pnValue.c_str());
    ds->putAndInsertString(DCM_PatientID, "ÇÃÕ123");
    ds->putAndInsertString(DCM_InstitutionName, institution.c_str());
    ds->putAndInsertString(DCM_Modality, "OT");
    ds->putAndInsertUint16(DCM_Rows, 1);
    ds->putAndInsertUint16(DCM_Columns, 1);
    ds->putAndInsertUint16(DCM_BitsAllocated, 8);
    ds->putAndInsertUint16(DCM_BitsStored, 8);
    ds->putAndInsertUint16(DCM_HighBit, 7);
    ds->putAndInsertUint16(DCM_SamplesPerPixel, 1);
    ds->putAndInsertString(DCM_PhotometricInterpretation, "MONOCHROME2");
    Uint8 pixel = 42;
    ds->putAndInsertUint8Array(DCM_PixelData, &pixel, 1);

    const std::string outPath = JoinPath(outputDir, "dcmtk_charset_utf8.dcm");
    if (fileformat.saveFile(outPath.c_str(), EXS_LittleEndianExplicit).bad()) {
        std::cerr << "Failed to write UTF-8 test dataset to " << outPath << std::endl;
        return;
    }

    DcmFileFormat reload;
    if (reload.loadFile(outPath.c_str()).bad()) {
        std::cerr << "Could not reload written UTF-8 file." << std::endl;
        return;
    }

    OFString roundTripName, roundTripInstitution, roundTripId;
    reload.getDataset()->findAndGetOFString(DCM_PatientName, roundTripName);
    reload.getDataset()->findAndGetOFString(DCM_InstitutionName, roundTripInstitution);
    reload.getDataset()->findAndGetOFString(DCM_PatientID, roundTripId);

    const bool nameOk = pnValue == roundTripName.c_str();
    const bool institutionOk = institution == roundTripInstitution.c_str();
    const bool idOk = TrimSpaces(roundTripId) == "ÇÃÕ123";

    const std::string reportPath = JoinPath(outputDir, "dcmtk_charset_roundtrip.txt");
    std::ofstream report(reportPath, std::ios::out | std::ios::trunc);
    report << "ExpectedPN=" << pnValue << "\n";
    report << "RoundTripPN=" << roundTripName.c_str() << "\n";
    report << "ExpectedInstitution=" << institution << "\n";
    report << "RoundTripInstitution=" << roundTripInstitution.c_str() << "\n";
    report << "ExpectedPatientID=ÇÃÕ123\n";
    report << "RoundTripPatientID=" << roundTripId.c_str() << "\n";
    report << "MatchPN=" << (nameOk ? "yes" : "no") << "\n";
    report << "MatchInstitution=" << (institutionOk ? "yes" : "no") << "\n";
    report << "MatchPatientID=" << (idOk ? "yes" : "no") << "\n";
    report.close();

    std::cout << "Character set round-trip " << ((nameOk && institutionOk && idOk) ? "passed" : "failed")
              << " (artifacts at '" << outPath << "')" << std::endl;
#else
    (void)outputDir;
    std::cout << "DCMTK not enabled." << std::endl;
#endif
}
