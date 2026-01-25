void DCMTKTests::TestStructuredReport(const std::string& sourceFile, const std::string& outputDir) {
    // Create a simple SR with a numeric measurement and free-text observation, then read it back
    std::cout << "--- [DCMTK] Structured Report ---" << std::endl;
#ifdef USE_DCMTK
    DSRDocument sr(DSRTypes::DT_EnhancedSR);
    sr.createNewDocument(DSRTypes::DT_EnhancedSR);

    // Seed patient/study from source if available
    DcmFileFormat src;
    if (src.loadFile(sourceFile.c_str()).good()) {
        sr.readPatientData(*src.getDataset());
        sr.readStudyData(*src.getDataset());
    } else {
        sr.setPatientName("SR^Demo");
        sr.setPatientID("SR001");
        sr.createNewStudy();
    }
    OFString studyUID;
    sr.getStudyInstanceUID(studyUID);
    if (studyUID.empty()) {
        sr.createNewStudy();
        sr.getStudyInstanceUID(studyUID);
    }
    sr.createNewSeriesInStudy(studyUID);
    sr.createNewSOPInstance();

    DSRDocumentTree& tree = sr.getTree();
    tree.clear();

    DSRCodedEntryValue reportTitle("126000", "DCM", "Imaging Measurement Report");
    const size_t rootId = tree.addContentItem(DSRTypes::RT_isRoot, DSRTypes::VT_Container);
    if (rootId > 0) {
        tree.getCurrentContentItem().setConceptName(reportTitle, OFTrue);
        OFDateTime now = OFDateTime::getCurrentDateTime();
        OFString nowStr;
        now.getISOFormattedDateTime(nowStr, false, true, true, ".");
        tree.getCurrentContentItem().setObservationDateTime(nowStr);

        DSRCodedEntryValue measCode("121401", "DCM", "Mean");
        DSRNumericMeasurementValue numVal("42", DSRCodedEntryValue("HU", "UCUM", "Hounsfield unit"));
        tree.addChildContentItem(DSRTypes::RT_contains, DSRTypes::VT_Num, measCode);
        tree.getCurrentContentItem().setNumericValue(numVal);

        DSRCodedEntryValue textCode("121106", "DCM", "Finding");
        tree.addChildContentItem(DSRTypes::RT_contains, DSRTypes::VT_Text, textCode);
        tree.getCurrentContentItem().setStringValue("Synthetic ROI measurement for QA.");
    } else {
        std::cerr << "Failed to create SR root container." << std::endl;
        return;
    }

    DcmFileFormat out;
    sr.write(*out.getDataset());
    const std::string path = JoinPath(outputDir, "dcmtk_sr.dcm");
    if (out.saveFile(path.c_str(), EXS_LittleEndianExplicit).bad()) {
        std::cerr << "Failed to write SR file." << std::endl;
        return;
    }

    // Reload and emit a brief tree summary
    DSRDocument srRead;
    const std::string reportTxt = JoinPath(outputDir, "dcmtk_sr_summary.txt");
    std::ofstream report(reportTxt, std::ios::out | std::ios::trunc);
    if (srRead.read(*out.getDataset()).good()) {
        report << "Valid=" << (srRead.isValid() ? "yes" : "no") << "\n";
        report << "DocType=" << srRead.getDocumentType() << "\n";
        report << "PatientName=";
        OFString pn;
        srRead.getPatientName(pn);
        report << pn.c_str() << "\n";
        srRead.getPatientID(pn);
        report << "PatientID=" << pn.c_str() << "\n";
        report << "Tree:\n";
        srRead.getTree().print(report);
    } else {
        report << "Failed to read back SR document.\n";
    }
    report.close();

    std::cout << "Structured Report saved to '" << path << "' (summary: " << reportTxt << ")" << std::endl;
#else
    (void)sourceFile;
    (void)outputDir;
    std::cout << "DCMTK not enabled." << std::endl;
#endif
}


void DCMTKTests::TestRTStructRead(const std::string& filename, const std::string& outputDir) {
    // Read RTSTRUCT and count ROIs + contour points
    std::cout << "--- [DCMTK] RTSTRUCT Read ---" << std::endl;
#ifdef USE_DCMTK
    DcmFileFormat file;
    std::ofstream out;
    const std::string outPath = JoinPath(outputDir, "dcmtk_rtstruct.txt");
    out.open(outPath, std::ios::out | std::ios::trunc);

    if (file.loadFile(filename.c_str()).bad()) {
        out << "Error=load_failed\n";
        std::cerr << "Failed to load RTSTRUCT." << std::endl;
        std::cout << "RTSTRUCT summary written to '" << outPath << "'" << std::endl;
        return;
    }

    DRTStructureSetIOD rt;
    if (rt.read(*file.getDataset()).bad()) {
        out << "Error=parse_failed\n";
        out.close();
        std::cerr << "Could not parse RTSTRUCT IOD." << std::endl;
        std::cout << "RTSTRUCT summary written to '" << outPath << "'" << std::endl;
        return;
    }

    DRTStructureSetROISequence& roiSeq = rt.getStructureSetROISequence();
    const size_t roiCount = roiSeq.getNumberOfItems();
    std::vector<std::string> roiNames;

    OFCondition status;
    for (size_t i = 1; i <= roiCount; ++i) {
        DRTStructureSetROISequence::Item& item = roiSeq.getItem(i);
        OFString name;
        item.getROIName(name);
        roiNames.emplace_back(name.empty() ? "(none)" : name.c_str());
    }

    DRTROIContourSequence& contourSeq = rt.getROIContourSequence();
    size_t contourFrames = 0;
    for (size_t i = 1; i <= contourSeq.getNumberOfItems(); ++i) {
        DRTROIContourSequence::Item& item = contourSeq.getItem(i);
        DRTContourSequence& cs = item.getContourSequence();
        contourFrames += cs.getNumberOfItems();
    }

    out << "ROIs=" << roiCount << "\n";
    size_t toList = std::min<size_t>(roiNames.size(), 5);
    for (size_t i = 0; i < toList; ++i) {
        out << "- ROI[" << i + 1 << "]=" << roiNames[i] << "\n";
    }
    out << "ContourFrames=" << contourFrames << "\n";
    out.close();

    std::cout << "RTSTRUCT summary written to '" << outPath << "'" << std::endl;
#else
    (void)filename;
    (void)outputDir;
    std::cout << "DCMTK not enabled." << std::endl;
#endif
}


void DCMTKTests::TestFunctionalGroupRead(const std::string& filename, const std::string& outputDir) {
    // Inspect per-frame functional groups from a multi-frame image
    std::cout << "--- [DCMTK] Functional Groups ---" << std::endl;
#ifdef USE_DCMTK
    DcmFileFormat file;
    const std::string reportPath = JoinPath(outputDir, "dcmtk_functional_groups.txt");
    std::ofstream report(reportPath, std::ios::out | std::ios::trunc);

    if (file.loadFile(filename.c_str()).bad()) {
        report << "Error=load_failed\n";
        std::cerr << "Failed to load multi-frame DICOM." << std::endl;
        std::cout << "Functional group summary written to '" << reportPath << "'" << std::endl;
        return;
    }

    DcmDataset* dataset = file.getDataset();
    Sint32 frames = 0;
    dataset->findAndGetSint32(DCM_NumberOfFrames, frames);
    report << "NumberOfFrames=" << frames << "\n";

    FGInterface fg;
    if (fg.read(*dataset).bad()) {
        report << "Error=no_functional_groups\n";
        report.close();
        std::cerr << "No functional group data found." << std::endl;
        return;
    }

    FGBase* sharedPosBase = fg.get(0, DcmFGTypes::EFG_PLANEPOSPATIENT);
    if (sharedPosBase) {
        if (auto* planePos = dynamic_cast<FGPlanePosPatient*>(sharedPosBase)) {
            Float64 x = 0, y = 0, z = 0;
            if (planePos->getImagePositionPatient(x, y, z).good()) {
                report << "SharedPlanePos=" << x << "\\" << y << "\\" << z << "\n";
            }
        }
    }

    const size_t framesToInspect = std::min<Sint32>(frames > 0 ? frames : 1, 3);
    for (size_t idx = 0; idx < framesToInspect; ++idx) {
        report << "Frame[" << idx + 1 << "]\n";
        if (auto* pmBase = fg.get(static_cast<Uint32>(idx), DcmFGTypes::EFG_PIXELMEASURES)) {
            if (auto* pm = dynamic_cast<FGPixelMeasures*>(pmBase)) {
                Float64 spacingX = 0, spacingY = 0;
                pm->getPixelSpacing(spacingX, 0);
                pm->getPixelSpacing(spacingY, 1);
                report << "  PixelSpacing=" << spacingX << "\\" << spacingY << "\n";
            }
        }
        if (auto* pfBase = fg.get(static_cast<Uint32>(idx), DcmFGTypes::EFG_PLANEPOSPATIENT)) {
            if (auto* pf = dynamic_cast<FGPlanePosPatient*>(pfBase)) {
                Float64 x = 0, y = 0, z = 0;
                if (pf->getImagePositionPatient(x, y, z).good()) {
                    report << "  Position=" << x << "\\" << y << "\\" << z << "\n";
                }
            }
        }
        if (auto* poBase = fg.get(static_cast<Uint32>(idx), DcmFGTypes::EFG_PLANEORIENTPATIENT)) {
            if (auto* po = dynamic_cast<FGPlaneOrientationPatient*>(poBase)) {
                Float64 ix = 0, iy = 0, iz = 0, jx = 0, jy = 0, jz = 0;
                if (po->getImageOrientationPatient(ix, iy, iz, jx, jy, jz).good()) {
                    report << "  Orientation=" << ix << "\\" << iy << "\\" << iz
                           << "\\" << jx << "\\" << jy << "\\" << jz << "\n";
                }
            }
        }
    }
    report.close();

    // Export first frame preview if multi-frame
    if (frames > 0) {
        DicomImage image(filename.c_str());
        if (image.getStatus() == EIS_Normal) {
            image.writePPM(JoinPath(outputDir, "dcmtk_multiframe_frame0.ppm").c_str(), 0);
        }
    }

    std::cout << "Functional group summary written to '" << reportPath << "'" << std::endl;
#else
    (void)filename;
    (void)outputDir;
    std::cout << "DCMTK not enabled." << std::endl;
#endif
}


void DCMTKTests::TestWaveformAndPSReport(const std::string& filename, const std::string& outputDir) {
    // Inspect waveform and presentation state metadata and emit a text summary
    std::cout << "--- [DCMTK] Waveform / Presentation State ---" << std::endl;
#ifdef USE_DCMTK
    DcmFileFormat file;
    const std::string reportPath = JoinPath(outputDir, "dcmtk_waveform.txt");
    std::ofstream report(reportPath, std::ios::out | std::ios::trunc);
    if (!report.is_open()) {
        std::cerr << "Could not open waveform report at " << reportPath << std::endl;
        return;
    }

    if (file.loadFile(filename.c_str()).bad()) {
        report << "Error=load_failed\n";
        report.close();
        std::cerr << "Failed to load file for waveform inspection." << std::endl;
        return;
    }

    DcmDataset* ds = file.getDataset();
    OFString sopClass;
    ds->findAndGetOFString(DCM_SOPClassUID, sopClass);
    const bool isPS = (sopClass == UID_GrayscaleSoftcopyPresentationStateStorage);

    report << "SOPClass=" << sopClass.c_str() << "\n";
    report << "IsPresentationState=" << (isPS ? "yes" : "no") << "\n";

    DcmSequenceOfItems* wfSeq = nullptr;
    if (ds->findAndGetSequence(DCM_WaveformSequence, wfSeq).good() && wfSeq && wfSeq->card() > 0) {
        const size_t items = static_cast<size_t>(wfSeq->card());
        report << "WaveformSequenceItems=" << items << "\n";
        for (size_t i = 0; i < items; ++i) {
            DcmItem* item = wfSeq->getItem(static_cast<unsigned long>(i));
            if (!item) {
                continue;
            }
            OFString channels, samples, sampleRate;
            item->findAndGetOFString(DCM_NumberOfWaveformChannels, channels);
            item->findAndGetOFString(DCM_NumberOfWaveformSamples, samples);
            item->findAndGetOFString(DCM_SamplingFrequency, sampleRate);

            report << "Item[" << (i + 1) << "]Channels=" << channels.c_str() << "\n";
            report << "Item[" << (i + 1) << "]Samples=" << samples.c_str() << "\n";
            report << "Item[" << (i + 1) << "]SampleRate=" << sampleRate.c_str() << "\n";

            DcmElement* dataElem = nullptr;
            if (item->findAndGetElement(DCM_WaveformData, dataElem).good() && dataElem) {
                report << "Item[" << (i + 1) << "]DataLength=" << dataElem->getLength() << "\n";
            }
        }
    } else {
        report << "WaveformSequence=absent\n";
    }

    if (isPS) {
        // Log a few optional PS attributes without attempting full rendering
        OFString label, description, creator;
        ds->findAndGetOFString(DCM_ContentLabel, label);
        ds->findAndGetOFString(DCM_ContentDescription, description);
        ds->findAndGetOFString(DCM_ContentCreatorName, creator);
        report << "PS_Label=" << label.c_str() << "\n";
        report << "PS_Description=" << description.c_str() << "\n";
        report << "PS_Creator=" << creator.c_str() << "\n";
    }

    report.close();
    std::cout << "Waveform/PS summary written to '" << reportPath << "'" << std::endl;
#else
    (void)filename;
    (void)outputDir;
    std::cout << "DCMTK not enabled." << std::endl;
#endif
}
