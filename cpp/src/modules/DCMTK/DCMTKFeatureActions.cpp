//
// DCMTKFeatureActions.cpp
// DicomToolsCpp
//
// Provides DCMTK-backed examples for tag editing, pixel export, transcoding, metadata reporting, and DICOMDIR creation.
//
// Thales Matheus Mendonça Santos - November 2025

#include "DCMTKFeatureActions.h"

#include <cctype>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <chrono>
#include <thread>
#include <sstream>
#include <vector>

#ifdef USE_DCMTK
#include "dcmtk/config/osconfig.h"
#include "dcmtk/dcmdata/dcdicdir.h"
#include "dcmtk/dcmdata/dcddirif.h"
#include "dcmtk/dcmdata/dctk.h"
#include "dcmtk/dcmdata/dcuid.h"
#include "dcmtk/dcmdata/dcsequen.h"
#include "dcmtk/dcmimgle/dcmimage.h"
#include "dcmtk/dcmdata/dcrledrg.h"
#include "dcmtk/dcmdata/dcrleerg.h"
#include "dcmtk/dcmdata/dcxfer.h"
#include "dcmtk/dcmrt/drtstrct.h"
#include "dcmtk/dcmnet/scp.h"
#include "dcmtk/dcmnet/scu.h"
#include "dcmtk/dcmjpeg/djdecode.h"
#include "dcmtk/dcmjpeg/djencode.h"
#include "dcmtk/dcmfg/fgbase.h"
#include "dcmtk/dcmfg/fgpixmsr.h"
#include "dcmtk/dcmfg/fgplanpo.h"
#include "dcmtk/dcmfg/fgplanor.h"
#include "dcmtk/dcmfg/fginterface.h"
#include "dcmtk/dcmiod/iodmacro.h"
#include "dcmtk/dcmiod/modequipment.h"
#include "dcmtk/dcmseg/segment.h"
#include "dcmtk/dcmseg/segdoc.h"
#include "dcmtk/dcmseg/segtypes.h"
#include "dcmtk/dcmsr/dsrdoc.h"
#include "dcmtk/dcmsr/dsrdocst.h"
#include "dcmtk/dcmsr/dsrcodvl.h"
#include "dcmtk/dcmsr/dsrnumtn.h"
#include "dcmtk/dcmsr/dsrtextn.h"
#include "dcmtk/ofstd/oflist.h"
#include "dcmtk/ofstd/ofdatime.h"

namespace fs = std::filesystem;

namespace {
// Tiny helper to keep path concatenation readable in stream-heavy code
std::string JoinPath(const std::string& base, const std::string& filename) {
    return (fs::path(base) / filename).string();
}

std::string EscapeJson(const std::string& value) {
    std::string out;
    out.reserve(value.size());
    for (char ch : value) {
        switch (ch) {
            case '"': out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default: out += ch; break;
        }
    }
    return out;
}

OFList<OFString> DefaultTransferSyntaxes() {
    OFList<OFString> syntaxes;
    syntaxes.push_back(UID_LittleEndianExplicitTransferSyntax);
    syntaxes.push_back(UID_BigEndianExplicitTransferSyntax);
    syntaxes.push_back(UID_LittleEndianImplicitTransferSyntax);
    return syntaxes;
}

std::string TrimSpaces(const OFString& value) {
    std::string result = value.c_str();
    while (!result.empty() && std::isspace(static_cast<unsigned char>(result.back()))) {
        result.pop_back();
    }
    while (!result.empty() && std::isspace(static_cast<unsigned char>(result.front()))) {
        result.erase(result.begin());
    }
    return result;
}

struct ValidationResult {
    bool ok{true};
    std::vector<std::string> errors;
    std::vector<std::string> warnings;
    std::map<std::string, std::string> tags;
};

ValidationResult ValidateDataset(DcmDataset* dataset) {
    ValidationResult result;
    if (dataset == nullptr) {
        result.ok = false;
        result.errors.push_back("No dataset loaded");
        return result;
    }

    auto requireTag = [&](const DcmTagKey& tag, const std::string& label, bool required) {
        OFString value;
        if (dataset->findAndGetOFString(tag, value).good() && !value.empty()) {
            result.tags[label] = value.c_str();
        } else if (required) {
            result.errors.push_back(label + " missing");
        } else {
            result.warnings.push_back(label + " missing");
        }
    };

    requireTag(DCM_PatientName, "PatientName", false);
    requireTag(DCM_PatientID, "PatientID", false);
    requireTag(DCM_StudyInstanceUID, "StudyInstanceUID", true);
    requireTag(DCM_SeriesInstanceUID, "SeriesInstanceUID", true);
    requireTag(DCM_SOPInstanceUID, "SOPInstanceUID", true);
    requireTag(DCM_Modality, "Modality", true);

    Uint16 rows = 0, cols = 0;
    if (dataset->findAndGetUint16(DCM_Rows, rows).good() && dataset->findAndGetUint16(DCM_Columns, cols).good()) {
        result.tags["Rows"] = std::to_string(rows);
        result.tags["Columns"] = std::to_string(cols);
    } else {
        result.warnings.push_back("Rows/Columns missing");
    }

    Sint32 frames = 0;
    if (dataset->findAndGetSint32(DCM_NumberOfFrames, frames).good()) {
        result.tags["NumberOfFrames"] = std::to_string(frames);
    }

    const E_TransferSyntax xfer = dataset->getCurrentXfer();
    DcmXfer x(xfer);
    result.tags["TransferSyntax"] = x.getXferID();

    if (!dataset->tagExistsWithValue(DCM_PixelData)) {
        result.warnings.push_back("PixelData missing or empty");
    }

    result.ok = result.errors.empty();
    return result;
}

bool WriteValidationReport(const ValidationResult& result, const std::string& outputDir, bool jsonOutput) {
    const std::string textPath = JoinPath(outputDir, "validate.txt");
    std::ofstream out(textPath, std::ios::out | std::ios::trunc);
    if (!out.is_open()) {
        std::cerr << "Failed to open validation report at: " << textPath << std::endl;
        return false;
    }

    out << "Status=" << (result.ok ? "PASS" : "FAIL") << "\n";
    out << "Errors=" << result.errors.size() << "\n";
    for (const auto& err : result.errors) {
        out << "- " << err << "\n";
    }
    out << "Warnings=" << result.warnings.size() << "\n";
    for (const auto& warn : result.warnings) {
        out << "- " << warn << "\n";
    }
    out << "Tags" << "\n";
    for (const auto& kv : result.tags) {
        out << kv.first << "=" << kv.second << "\n";
    }
    out.close();

    if (jsonOutput) {
        const std::string jsonPath = JoinPath(outputDir, "validate.json");
        std::ofstream jout(jsonPath, std::ios::out | std::ios::trunc);
        if (jout.is_open()) {
            jout << "{\n";
            jout << "  \"status\": \"" << (result.ok ? "PASS" : "FAIL") << "\",\n";
            jout << "  \"errors\": [";
            for (size_t i = 0; i < result.errors.size(); ++i) {
                jout << "\"" << EscapeJson(result.errors[i]) << "\"";
                if (i + 1 < result.errors.size()) jout << ",";
            }
            jout << "],\n";
            jout << "  \"warnings\": [";
            for (size_t i = 0; i < result.warnings.size(); ++i) {
                jout << "\"" << EscapeJson(result.warnings[i]) << "\"";
                if (i + 1 < result.warnings.size()) jout << ",";
            }
            jout << "],\n";
            jout << "  \"tags\": {";
            size_t count = 0;
            for (const auto& kv : result.tags) {
                jout << "\n    \"" << EscapeJson(kv.first) << "\": \"" << EscapeJson(kv.second) << "\"";
                if (++count < result.tags.size()) jout << ",";
            }
            if (!result.tags.empty()) jout << "\n  ";
            jout << "}\n";
            jout << "}\n";
        } else {
            std::cerr << "Failed to open JSON validation report at: " << jsonPath << std::endl;
        }
    }

    return true;
}
} // namespace

#include "DCMTKFeatureActions_Basic.inc"
#include "DCMTKFeatureActions_Metadata.inc"
#include "DCMTKFeatureActions_Network.inc"
#include "DCMTKFeatureActions_Charset.inc"
#include "DCMTKFeatureActions_Capture.inc"
#include "DCMTKFeatureActions_Reports.inc"
#include "DCMTKFeatureActions_Segmentation.inc"

#else
namespace DCMTKTests {
void TestTagModification(const std::string&, const std::string&) { std::cout << "DCMTK not enabled." << std::endl; }
void TestPixelDataExtraction(const std::string&, const std::string&) {}
void TestDICOMDIRGeneration(const std::string&, const std::string&) {}
void TestLosslessJPEGReencode(const std::string&, const std::string&) {}
void TestRawDump(const std::string&, const std::string&) {}
void TestExplicitVRRewrite(const std::string&, const std::string&) {}
void TestMetadataReport(const std::string&, const std::string&, bool) {}
void TestRLEReencode(const std::string&, const std::string&) {}
void TestJPEGBaseline(const std::string&, const std::string&) {}
void TestBMPPreview(const std::string&, const std::string&) {}
void TestSegmentationExport(const std::string&, const std::string&) {}
void TestNetworkEchoAndStore(const std::string&, const std::string&) {}
void TestCharacterSetRoundTrip(const std::string&) {}
void TestSecondaryCapture(const std::string&, const std::string&) {}
void TestStructuredReport(const std::string&, const std::string&) {}
void TestRTStructRead(const std::string&, const std::string&) {}
void TestFunctionalGroupRead(const std::string&, const std::string&) {}
void TestWaveformAndPSReport(const std::string&, const std::string&) {}
int ValidateDicomFile(const std::string&, const std::string&, bool) { std::cout << "DCMTK not enabled." << std::endl; return 1; }
} // namespace DCMTKTests
#endif
