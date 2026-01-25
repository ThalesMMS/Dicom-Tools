void GDCMTests::TestSequenceEditing(const std::string& filename, const std::string& outputDir) {
    // Create or extend a ReferencedSeriesSequence item and persist the changes
    std::cout << "--- [GDCM] Sequence Editing ---" << std::endl;

    gdcm::Reader reader;
    reader.SetFileName(filename.c_str());
    if (!reader.Read()) {
        std::cerr << "Could not read file for sequence editing." << std::endl;
        return;
    }

    gdcm::DataSet& ds = reader.GetFile().GetDataSet();
    const gdcm::Tag refSeriesSeq(0x0008, 0x1115);
    gdcm::SmartPointer<gdcm::SequenceOfItems> seq;
    if (ds.FindDataElement(refSeriesSeq)) {
        seq = ds.GetDataElement(refSeriesSeq).GetValueAsSQ();
    }
    if (!seq) {
        seq = new gdcm::SequenceOfItems();
    }

    gdcm::Item item;
    item.SetVLToUndefined();
    gdcm::DataSet& nested = item.GetNestedDataSet();

    gdcm::UIDGenerator uidGen;
    const std::string seriesUID = uidGen.Generate();
    const std::string sopUID = uidGen.Generate();

    gdcm::Attribute<0x0020, 0x000E> seriesAttr;
    seriesAttr.SetValue(seriesUID.c_str());
    gdcm::Attribute<0x0008, 0x1155> sopAttr;
    sopAttr.SetValue(sopUID.c_str());
    nested.Insert(seriesAttr.GetAsDataElement());
    nested.Insert(sopAttr.GetAsDataElement());

    seq->AddItem(item);

    gdcm::DataElement seqElement(refSeriesSeq);
    seqElement.SetVR(gdcm::VR::SQ);
    seqElement.SetValue(*seq);
    seqElement.SetVLToUndefined();
    ds.Replace(seqElement);

    const std::string outPath = JoinPath(outputDir, "gdcm_sequence.dcm");
    gdcm::Writer writer;
    writer.SetFileName(outPath.c_str());
    writer.SetFile(reader.GetFile());
    if (!writer.Write()) {
        std::cerr << "Failed to write updated sequence file." << std::endl;
        return;
    }

    size_t itemCount = seq->GetNumberOfItems();
    gdcm::Reader verify;
    verify.SetFileName(outPath.c_str());
    if (verify.Read() && verify.GetFile().GetDataSet().FindDataElement(refSeriesSeq)) {
        auto seqCheck = verify.GetFile().GetDataSet().GetDataElement(refSeriesSeq).GetValueAsSQ();
        if (seqCheck) {
            itemCount = seqCheck->GetNumberOfItems();
        }
    }

    const std::string summaryPath = JoinPath(outputDir, "gdcm_sequence.txt");
    std::ofstream summary(summaryPath, std::ios::out | std::ios::trunc);
    summary << "Items=" << itemCount << "\n";
    summary << "LastSeriesInstanceUID=" << seriesUID << "\n";
    summary << "LastReferencedSOPInstanceUID=" << sopUID << "\n";
    summary.close();

    std::cout << "Inserted sequence item (total " << itemCount << ") into '" << outPath << "'" << std::endl;
}


void GDCMTests::TestStringFilterCharsets(const std::string& filename, const std::string& outputDir) {
    // Exercise gdcm::StringFilter on UTF-8 fields
    std::cout << "--- [GDCM] StringFilter Character Sets ---" << std::endl;

    gdcm::Reader reader;
    reader.SetFileName(filename.c_str());
    if (!reader.Read()) {
        std::cerr << "Could not read file for charset test." << std::endl;
        return;
    }

    gdcm::File& file = reader.GetFile();
    gdcm::DataSet& ds = file.GetDataSet();
    const std::string charset = "ISO_IR 192";
    const std::string pnValue = "André Gödel^Teste";
    const std::string institution = "Clínica São Paulo";

    gdcm::DataElement charsetElem(gdcm::Tag(0x0008, 0x0005));
    charsetElem.SetVR(gdcm::VR::CS);
    charsetElem.SetByteValue(charset.c_str(), static_cast<uint32_t>(charset.size()));
    ds.Replace(charsetElem);

    gdcm::DataElement pnElem(gdcm::Tag(0x0010, 0x0010));
    pnElem.SetVR(gdcm::VR::PN);
    pnElem.SetByteValue(pnValue.c_str(), static_cast<uint32_t>(pnValue.size()));
    ds.Replace(pnElem);

    gdcm::DataElement instElem(gdcm::Tag(0x0008, 0x0080));
    instElem.SetVR(gdcm::VR::LO);
    instElem.SetByteValue(institution.c_str(), static_cast<uint32_t>(institution.size()));
    ds.Replace(instElem);

    const std::string outPath = JoinPath(outputDir, "gdcm_charset.dcm");
    gdcm::Writer writer;
    writer.SetFileName(outPath.c_str());
    writer.SetFile(file);
    if (!writer.Write()) {
        std::cerr << "Failed to write charset test file." << std::endl;
        return;
    }

    gdcm::Reader reload;
    reload.SetFileName(outPath.c_str());
    if (!reload.Read()) {
        std::cerr << "Could not reload charset test file." << std::endl;
        return;
    }

    gdcm::StringFilter sf;
    sf.SetFile(reload.GetFile());
    const std::string decodedPN = sf.ToString(gdcm::Tag(0x0010, 0x0010));
    const std::string decodedInst = sf.ToString(gdcm::Tag(0x0008, 0x0080));

    const std::string reportPath = JoinPath(outputDir, "gdcm_charset.txt");
    std::ofstream report(reportPath, std::ios::out | std::ios::trunc);
    report << "ExpectedPN=" << pnValue << "\n";
    report << "DecodedPN=" << decodedPN << "\n";
    report << "ExpectedInstitution=" << institution << "\n";
    report << "DecodedInstitution=" << decodedInst << "\n";
    report << "PNMatch=" << (decodedPN == pnValue ? "yes" : "no") << "\n";
    report << "InstitutionMatch=" << (decodedInst == institution ? "yes" : "no") << "\n";
    report.close();

    std::cout << "StringFilter decoded PN=" << decodedPN << " (report: " << reportPath << ")" << std::endl;
}


void GDCMTests::TestRTStructRead(const std::string& filename, const std::string& outputDir) {
    // Parse a RTSTRUCT/SEG and emit basic ROI/contour summaries
    std::cout << "--- [GDCM] RTSTRUCT/SEG Inspection ---" << std::endl;

    gdcm::Reader reader;
    reader.SetFileName(filename.c_str());
    if (!reader.Read()) {
        std::cerr << "Could not read file for RTSTRUCT inspection." << std::endl;
        return;
    }

    const gdcm::DataSet& ds = reader.GetFile().GetDataSet();
    const gdcm::Tag modalityTag(0x0008, 0x0060);
    std::string modality;
    if (ds.FindDataElement(modalityTag)) {
        gdcm::Attribute<0x0008, 0x0060> attr;
        attr.SetFromDataElement(ds.GetDataElement(modalityTag));
        modality = attr.GetValue();
    }

    const gdcm::Tag ssRoiSeq(0x3006, 0x0020);
    const gdcm::Tag roiNameTag(0x3006, 0x0026);
    const gdcm::Tag roiContourSeq(0x3006, 0x0039);
    const gdcm::Tag contourSeq(0x3006, 0x0040);
    const gdcm::Tag contourDataTag(0x3006, 0x0050);

    size_t roiCount = 0;
    std::vector<std::string> roiNames;

    if (ds.FindDataElement(ssRoiSeq)) {
        const gdcm::DataElement& elem = ds.GetDataElement(ssRoiSeq);
        auto seq = elem.GetValueAsSQ();
        if (seq) {
            roiCount = seq->GetNumberOfItems();
            for (auto it = seq->Begin(); it != seq->End(); ++it) {
                const gdcm::DataSet& itemDs = it->GetNestedDataSet();
                if (itemDs.FindDataElement(roiNameTag)) {
                    gdcm::Attribute<0x3006, 0x0026> nameAttr;
                    nameAttr.SetFromDataElement(itemDs.GetDataElement(roiNameTag));
                    roiNames.emplace_back(nameAttr.GetValue());
                }
            }
        }
    }

    size_t contourFrames = 0;
    if (ds.FindDataElement(roiContourSeq)) {
        const gdcm::DataElement& elem = ds.GetDataElement(roiContourSeq);
        auto seq = elem.GetValueAsSQ();
        if (seq) {
            for (auto it = seq->Begin(); it != seq->End(); ++it) {
                const gdcm::DataSet& roiItem = it->GetNestedDataSet();
                if (roiItem.FindDataElement(contourSeq)) {
                    auto contourItems = roiItem.GetDataElement(contourSeq).GetValueAsSQ();
                    if (contourItems) {
                        for (auto cit = contourItems->Begin(); cit != contourItems->End(); ++cit) {
                            const gdcm::DataSet& contourDS = cit->GetNestedDataSet();
                            if (contourDS.FindDataElement(contourDataTag)) {
                                contourFrames++;
                            }
                        }
                    }
                }
            }
        }
    }

    const std::string outPath = JoinPath(outputDir, "gdcm_rtstruct.txt");
    std::ofstream out(outPath, std::ios::out | std::ios::trunc);
    out << "Modality=" << modality << "\n";
    out << "ROIs=" << roiCount << "\n";
    size_t toList = std::min<size_t>(roiNames.size(), 5);
    for (size_t i = 0; i < toList; ++i) {
        out << "- ROI[" << i + 1 << "]=" << roiNames[i] << "\n";
    }
    out << "ContourFrames=" << contourFrames << "\n";
    out.close();

    std::cout << "Wrote RTSTRUCT summary to '" << outPath << "'" << std::endl;
}
