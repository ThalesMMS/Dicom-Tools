void GDCMTests::TestTagInspection(const std::string& filename, const std::string& outputDir) {
    (void)outputDir;
    // Minimal read + print of a couple of common identifiers
    std::cout << "--- [GDCM] Tag Inspection ---" << std::endl;
    gdcm::Reader reader;
    reader.SetFileName(filename.c_str());
    if (!reader.Read()) {
        std::cerr << "GDCM: Could not read file: " << filename << std::endl;
        return;
    }

    const gdcm::DataSet& ds = reader.GetFile().GetDataSet();
    gdcm::StringFilter sf;
    sf.SetFile(reader.GetFile());

    gdcm::Tag tagPatientName(0x0010, 0x0010);
    if (ds.FindDataElement(tagPatientName)) {
        std::cout << "Patient Name: " << sf.ToString(tagPatientName) << std::endl;
    } else {
        std::cout << "Patient Name: (Not Found)" << std::endl;
    }

    gdcm::Tag tagSOPInstanceUID(0x0008, 0x0018);
    if (ds.FindDataElement(tagSOPInstanceUID)) {
        std::cout << "SOP Instance UID: " << sf.ToString(tagSOPInstanceUID) << std::endl;
    }
}


void GDCMTests::TestAnonymization(const std::string& filename, const std::string& outputDir) {
    // Blanks PHI tags and writes a scrubbed copy
    std::cout << "--- [GDCM] Anonymization ---" << std::endl;
    
    gdcm::Reader reader;
    reader.SetFileName(filename.c_str());
    if (!reader.Read()) {
        std::cerr << "Could not read file for anonymization." << std::endl;
        return;
    }

    gdcm::Anonymizer anon;
    anon.SetFile(reader.GetFile());
    
    anon.Empty(gdcm::Tag(0x0010, 0x0010));
    anon.Empty(gdcm::Tag(0x0010, 0x0020));
    anon.Empty(gdcm::Tag(0x0010, 0x0030));

    gdcm::Writer writer;
    std::string outFilename = JoinPath(outputDir, "gdcm_anon.dcm");
    writer.SetFileName(outFilename.c_str());
    writer.SetFile(anon.GetFile());
    
    if (writer.Write()) {
        std::cout << "Anonymized file saved to: " << outFilename << std::endl;
    } else {
        std::cerr << "Failed to write anonymized file." << std::endl;
    }
}


void GDCMTests::TestDecompression(const std::string& filename, const std::string& outputDir) {
    // Transcodes to an uncompressed transfer syntax to validate decompression
    std::cout << "--- [GDCM] Decompression (Transcoding to Raw) ---" << std::endl;
    
    gdcm::ImageChangeTransferSyntax change;
    change.SetTransferSyntax(gdcm::TransferSyntax::ImplicitVRLittleEndian);
    
    gdcm::ImageReader reader;
    reader.SetFileName(filename.c_str());
    if (!reader.Read()) {
        std::cerr << "Could not read file for decompression." << std::endl;
        return;
    }

    change.SetInput(reader.GetImage());
    if (!change.Change()) {
        std::cerr << "Could not change transfer syntax (decompression failed)." << std::endl;
        return;
    }

    gdcm::ImageWriter writer;
    std::string outFilename = JoinPath(outputDir, "gdcm_raw.dcm");
    writer.SetFileName(outFilename.c_str());
    writer.SetFile(reader.GetFile());
    writer.SetImage(change.GetOutput());
    
    if (writer.Write()) {
        std::cout << "Decompressed file saved to: " << outFilename << std::endl;
    } else {
        std::cerr << "Failed to write decompressed file." << std::endl;
    }
}


void GDCMTests::TestUIDRewrite(const std::string& filename, const std::string& outputDir) {
    // Generates fresh UIDs for study/series/instance to mimic reidentification
    std::cout << "--- [GDCM] UID Regeneration ---" << std::endl;
    gdcm::Reader reader;
    reader.SetFileName(filename.c_str());
    if (!reader.Read()) {
        std::cerr << "Could not read file for UID rewrite." << std::endl;
        return;
    }

    gdcm::UIDGenerator uidGen;
    std::string studyUID = uidGen.Generate();
    std::string seriesUID = uidGen.Generate();
    std::string instanceUID = uidGen.Generate();

    auto setUID = [&](const gdcm::Tag& tag, const std::string& value) {
        gdcm::DataElement elem(tag);
        elem.SetByteValue(value.c_str(), static_cast<uint32_t>(value.size()));
        reader.GetFile().GetDataSet().Replace(elem);
    };

    setUID(gdcm::Tag(0x0020, 0x000D), studyUID);  // StudyInstanceUID
    setUID(gdcm::Tag(0x0020, 0x000E), seriesUID); // SeriesInstanceUID
    setUID(gdcm::Tag(0x0008, 0x0018), instanceUID); // SOPInstanceUID

    gdcm::Writer writer;
    std::string outFilename = JoinPath(outputDir, "gdcm_reuid.dcm");
    writer.SetFileName(outFilename.c_str());
    writer.SetFile(reader.GetFile());
    if (writer.Write()) {
        std::cout << "Assigned new Study/Series/SOP UIDs and saved to: " << outFilename << std::endl;
    } else {
        std::cerr << "Failed to write UID-regenerated file." << std::endl;
    }
}


void GDCMTests::TestDatasetDump(const std::string& filename, const std::string& outputDir) {
    // Writes a verbose text dump for QA or debugging of unusual datasets
    std::cout << "--- [GDCM] Dataset Dump ---" << std::endl;
    gdcm::Reader reader;
    reader.SetFileName(filename.c_str());
    if (!reader.Read()) {
        std::cerr << "Could not read file for dataset dump." << std::endl;
        return;
    }

    std::string outFilename = JoinPath(outputDir, "gdcm_dump.txt");
    std::ofstream out(outFilename, std::ios::out | std::ios::trunc);
    if (!out.is_open()) {
        std::cerr << "Failed to open output for dataset dump: " << outFilename << std::endl;
        return;
    }

    gdcm::Printer printer;
    printer.SetFile(reader.GetFile());
    printer.Print(out);
    std::cout << "Wrote verbose dataset dump to: " << outFilename << std::endl;
}
