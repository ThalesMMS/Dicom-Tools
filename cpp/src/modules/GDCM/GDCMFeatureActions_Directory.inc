void GDCMTests::TestDirectoryScan(const std::string& path, const std::string& outputDir) {
    // Recursively index DICOM files and emit a CSV catalog of series
    std::cout << "--- [GDCM] Series Scan ---" << std::endl;

    std::filesystem::path inputPath(path);
    std::string searchRoot = std::filesystem::is_directory(inputPath) ? inputPath.string() : inputPath.parent_path().string();
    if (searchRoot.empty() || !std::filesystem::exists(searchRoot)) {
        std::cerr << "Cannot scan, path not found: " << searchRoot << std::endl;
        return;
    }

    gdcm::Directory dir;
    dir.Load(searchRoot, true);
    std::vector<std::string> dicomFiles;
    for (const auto& file : dir.GetFilenames()) {
        if (std::filesystem::path(file).extension() == ".dcm") {
            dicomFiles.push_back(file);
        }
    }

    if (dicomFiles.empty()) {
        std::cerr << "No DICOM files found under: " << searchRoot << std::endl;
        return;
    }

    gdcm::Scanner scanner;
    std::vector<gdcm::Tag> tags = {
        {0x0010, 0x0010}, // PatientName
        {0x0010, 0x0020}, // PatientID
        {0x0020, 0x000D}, // StudyInstanceUID
        {0x0020, 0x000E}, // SeriesInstanceUID
        {0x0008, 0x0018}, // SOPInstanceUID
        {0x0008, 0x0060}  // Modality
    };
    for (const auto& tag : tags) {
        scanner.AddTag(tag);
    }

    if (!scanner.Scan(dicomFiles)) {
        std::cerr << "Scanner failed to read metadata." << std::endl;
        return;
    }

    std::string outPath = JoinPath(outputDir, "gdcm_series_index.csv");
    std::ofstream out(outPath, std::ios::out | std::ios::trunc);
    if (!out.is_open()) {
        std::cerr << "Failed to open output CSV at: " << outPath << std::endl;
        return;
    }

    out << "File,PatientName,PatientID,StudyInstanceUID,SeriesInstanceUID,SOPInstanceUID,Modality\n";
    std::set<std::string> uniqueSeries;

    for (const std::string& file : dicomFiles) {
        auto fetch = [&](const gdcm::Tag& tag) -> std::string {
            const char* val = scanner.GetValue(file.c_str(), tag);
            return val ? val : "";
        };
        const std::string study = fetch(tags[2]);
        const std::string series = fetch(tags[3]);
        uniqueSeries.insert(study + "|" + series);

        out << file << ",";
        out << fetch(tags[0]) << ",";
        out << fetch(tags[1]) << ",";
        out << study << ",";
        out << series << ",";
        out << fetch(tags[4]) << ",";
        out << fetch(tags[5]) << "\n";
    }
    out.close();

    std::cout << "Indexed " << dicomFiles.size() << " files across " << uniqueSeries.size()
              << " series. CSV saved to: " << outPath << std::endl;
}


void GDCMTests::TestDicomdirRead(const std::string& path, const std::string& outputDir) {
    // Open a DICOMDIR and emit a summary of its records and referenced files
    std::cout << "--- [GDCM] DICOMDIR Read ---" << std::endl;

    std::filesystem::path inputPath(path);
    std::filesystem::path dicomdir = inputPath;
    if (std::filesystem::is_directory(inputPath)) {
        dicomdir /= "DICOMDIR";
    } else if (inputPath.filename() != "DICOMDIR") {
        dicomdir = inputPath.parent_path() / "DICOMDIR";
    }

    if (!std::filesystem::exists(dicomdir)) {
        std::cerr << "DICOMDIR not found near " << inputPath << std::endl;
        return;
    }

    gdcm::Reader reader;
    reader.SetFileName(dicomdir.string().c_str());
    if (!reader.Read()) {
        std::cerr << "Failed to read DICOMDIR at " << dicomdir << std::endl;
        return;
    }

    const gdcm::DataSet& ds = reader.GetFile().GetDataSet();
    const gdcm::Tag recordSeqTag(0x0004, 0x1220);
    size_t patientCount = 0, studyCount = 0, seriesCount = 0, instanceCount = 0;
    std::vector<std::string> refs;

    if (ds.FindDataElement(recordSeqTag)) {
        const gdcm::DataElement& elem = ds.GetDataElement(recordSeqTag);
        auto seq = elem.GetValueAsSQ();
        if (seq) {
            for (auto it = seq->Begin(); it != seq->End(); ++it) {
                const gdcm::DataSet& itemDs = it->GetNestedDataSet();
                if (!itemDs.FindDataElement(gdcm::Tag(0x0004, 0x1430))) {
                    continue;
                }
                gdcm::Attribute<0x0004, 0x1430> recordTypeAttr;
                recordTypeAttr.SetFromDataElement(itemDs.GetDataElement(gdcm::Tag(0x0004, 0x1430)));
                std::string recordType = recordTypeAttr.GetValue();
                while (!recordType.empty() && recordType.back() == ' ') {
                    recordType.pop_back();
                }
                if (recordType == "PATIENT") patientCount++;
                else if (recordType == "STUDY") studyCount++;
                else if (recordType == "SERIES") seriesCount++;
                else if (recordType == "IMAGE") instanceCount++;

                if (itemDs.FindDataElement(gdcm::Tag(0x0004, 0x1500))) {
                    gdcm::Attribute<0x0004, 0x1500> refId;
                    refId.SetFromDataElement(itemDs.GetDataElement(gdcm::Tag(0x0004, 0x1500)));
                    refs.emplace_back(refId.GetValue());
                }
            }
        }
    }

    const std::string outPath = JoinPath(outputDir, "gdcm_dicomdir.txt");
    std::ofstream out(outPath, std::ios::out | std::ios::trunc);
    out << "Patients=" << patientCount << "\n";
    out << "Studies=" << studyCount << "\n";
    out << "Series=" << seriesCount << "\n";
    out << "Instances=" << instanceCount << "\n";
    out << "Refs=" << refs.size() << "\n";
    size_t toPrint = std::min<size_t>(refs.size(), 8);
    for (size_t i = 0; i < toPrint; ++i) {
        out << "- " << refs[i] << "\n";
    }
    out.close();

    std::cout << "Parsed DICOMDIR (" << patientCount << " patients, " << seriesCount
              << " series) -> " << outPath << std::endl;
}
