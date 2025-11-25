//
// GDCMFeatureActions.cpp
// DicomToolsCpp
//
// Implements GDCM-driven feature demos like anonymization, UID rewrites, codec transcodes, previews, and directory scans.
//
// Thales Matheus Mendonça Santos - November 2025

#include "GDCMFeatureActions.h"

#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <vector>
#include <set>
#include <sstream>

#ifdef USE_GDCM
#include "gdcmAnonymizer.h"
#include "gdcmAttribute.h"
#include "gdcmDataElement.h"
#include "gdcmDirectory.h"
#include "gdcmDefs.h"
#include "gdcmGlobal.h"
#include "gdcmImageChangeTransferSyntax.h"
#include "gdcmImageReader.h"
#include "gdcmImageWriter.h"
#include "gdcmReader.h"
#include "gdcmSequenceOfItems.h"
#include "gdcmScanner.h"
#include "gdcmStringFilter.h"
#include "gdcmUIDs.h"
#include "gdcmUIDGenerator.h"
#include "gdcmWriter.h"
#include "gdcmPrinter.h"

namespace {
// Tiny helper to keep file paths readable
std::string JoinPath(const std::string& base, const std::string& name) {
    return (std::filesystem::path(base) / name).string();
}

struct PixelStats {
    // Minimal statistics used for QA when exporting numeric reports
    double min{0.0};
    double max{0.0};
    double mean{0.0};
    std::size_t count{0};
};

template <typename T>
PixelStats CalculateStats(const std::vector<char>& buffer) {
    // Interpret the buffer as type T and compute min/max/mean
    PixelStats stats;
    const auto* data = reinterpret_cast<const T*>(buffer.data());
    const std::size_t count = buffer.size() / sizeof(T);
    if (count == 0) {
        return stats;
    }

    T minVal = std::numeric_limits<T>::max();
    T maxVal = std::numeric_limits<T>::lowest();
    long double sum = 0.0;
    for (std::size_t i = 0; i < count; ++i) {
        T value = data[i];
        minVal = std::min(minVal, value);
        maxVal = std::max(maxVal, value);
        sum += value;
    }

    stats.count = count;
    stats.min = static_cast<double>(minVal);
    stats.max = static_cast<double>(maxVal);
    stats.mean = static_cast<double>(sum / static_cast<long double>(count));
    return stats;
}

template <typename T>
bool WritePGMPreview(const gdcm::Image& image, const std::vector<char>& buffer, const std::string& outPath) {
    // Create a simple 8-bit preview from the first channel of the volume
    const unsigned int width = image.GetDimension(0);
    const unsigned int height = image.GetDimension(1);
    const unsigned int samplesPerPixel = image.GetPixelFormat().GetSamplesPerPixel();
    const std::size_t pixelsPerSlice = static_cast<std::size_t>(width) * static_cast<std::size_t>(height);
    const std::size_t valuesPerSlice = pixelsPerSlice * static_cast<std::size_t>(samplesPerPixel);

    if (buffer.size() < valuesPerSlice * sizeof(T) || width == 0 || height == 0) {
        return false;
    }

    const T* data = reinterpret_cast<const T*>(buffer.data());
    double minVal = std::numeric_limits<double>::max();
    double maxVal = std::numeric_limits<double>::lowest();
    for (std::size_t i = 0; i < valuesPerSlice; i += samplesPerPixel) {
        const double value = static_cast<double>(data[i]); // take first channel if RGB
        minVal = std::min(minVal, value);
        maxVal = std::max(maxVal, value);
    }

    if (maxVal <= minVal) {
        maxVal = minVal + 1.0;
    }

    std::vector<uint8_t> preview(pixelsPerSlice, 0);
    for (std::size_t i = 0; i < valuesPerSlice; i += samplesPerPixel) {
        const double value = static_cast<double>(data[i]);
        const double normalized = (value - minVal) / (maxVal - minVal);
        preview[i / samplesPerPixel] = static_cast<uint8_t>(std::clamp(normalized, 0.0, 1.0) * 255.0);
    }

    std::ofstream out(outPath, std::ios::binary | std::ios::out | std::ios::trunc);
    if (!out.is_open()) {
        return false;
    }

    out << "P5\n" << width << " " << height << "\n255\n";
    out.write(reinterpret_cast<const char*>(preview.data()), static_cast<std::streamsize>(preview.size()));
    return out.good();
}
}

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

#else
namespace GDCMTests {
void TestTagInspection(const std::string&, const std::string&) { std::cout << "GDCM not enabled." << std::endl; }
void TestAnonymization(const std::string&, const std::string&) {}
void TestDecompression(const std::string&, const std::string&) {}
void TestUIDRewrite(const std::string&, const std::string&) {}
void TestDatasetDump(const std::string&, const std::string&) {}
void TestJPEG2000Transcode(const std::string&, const std::string&) {}
void TestRLETranscode(const std::string&, const std::string&) {}
void TestPixelStatistics(const std::string&, const std::string&) {}
void TestJPEGLSTranscode(const std::string&, const std::string&) {}
void TestDirectoryScan(const std::string&, const std::string&) {}
void TestPreviewExport(const std::string&, const std::string&) {}
void TestSequenceEditing(const std::string&, const std::string&) {}
void TestDicomdirRead(const std::string&, const std::string&) {}
void TestStringFilterCharsets(const std::string&, const std::string&) {}
void TestRTStructRead(const std::string&, const std::string&) {}
void TestJPEG2000Lossy(const std::string&, const std::string&) {}
void TestRLEPlanarConfiguration(const std::string&, const std::string&) {}
} // namespace GDCMTests
#endif
