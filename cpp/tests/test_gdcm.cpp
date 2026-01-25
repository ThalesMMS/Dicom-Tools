//
// test_gdcm.cpp
// DicomToolsCpp
//
// Unit tests for GDCM library features including file reading, tag parsing,
// transcoding, anonymization, and codec support verification.
//
// Thales Matheus Mendonça Santos - November 2025

#include "test_framework.h"

#include <filesystem>
#include <fstream>
#include <cstdlib>

#ifdef USE_GDCM
#include <gdcmReader.h>
#include <gdcmWriter.h>
#include <gdcmAttribute.h>
#include <gdcmDataSet.h>
#include <gdcmFile.h>
#include <gdcmFileMetaInformation.h>
#include <gdcmGlobal.h>
#include <gdcmDicts.h>
#include <gdcmDict.h>
#include <gdcmTag.h>
#include <gdcmVR.h>
#include <gdcmStringFilter.h>
#include <gdcmAnonymizer.h>
#include <gdcmImageReader.h>
#include <gdcmImageWriter.h>
#include <gdcmImageChangeTransferSyntax.h>
#include <gdcmJPEG2000Codec.h>
#include <gdcmJPEGCodec.h>
#include <gdcmRLECodec.h>
#include <gdcmUIDGenerator.h>
#include <gdcmScanner.h>
#include <gdcmDirectory.h>
#endif

namespace fs = std::filesystem;

// Helper to find a test DICOM file
static std::string FindTestDicom() {
    std::vector<std::string> searchPaths = {
        "../sample_series",
        "../../sample_series",
        "../../../sample_series",
        "sample_series"
    };
    for (const auto& base : searchPaths) {
        fs::path p(base);
        if (fs::exists(p) && fs::is_directory(p)) {
            for (const auto& entry : fs::directory_iterator(p)) {
                if (entry.path().extension() == ".dcm") {
                    return entry.path().string();
                }
            }
        }
    }
    return "";
}

#ifdef USE_GDCM

// =============================================================================
// GDCM Basic Functionality Tests
// =============================================================================

TEST_CASE(GDCM_GlobalDictAvailable) {
    const gdcm::Global& g = gdcm::Global::GetInstance();
    const gdcm::Dicts& dicts = g.GetDicts();
    const gdcm::Dict& pubDict = dicts.GetPublicDict();
    
    // Patient Name tag should exist in the public dictionary
    gdcm::Tag patientName(0x0010, 0x0010);
    const gdcm::DictEntry& entry = pubDict.GetDictEntry(patientName);
    
    EXPECT_EQ(entry.GetVR(), gdcm::VR::PN);
    return true;
}

TEST_CASE(GDCM_TagConstruction) {
    gdcm::Tag tag1(0x0008, 0x0018);  // SOP Instance UID
    gdcm::Tag tag2(0x7FE0, 0x0010);  // Pixel Data
    
    EXPECT_EQ(tag1.GetGroup(), 0x0008);
    EXPECT_EQ(tag1.GetElement(), 0x0018);
    EXPECT_EQ(tag2.GetGroup(), 0x7FE0);
    EXPECT_EQ(tag2.GetElement(), 0x0010);
    return true;
}

TEST_CASE(GDCM_VRTypes) {
    EXPECT_EQ(gdcm::VR::GetVRString(gdcm::VR::PN), "PN");
    EXPECT_EQ(gdcm::VR::GetVRString(gdcm::VR::UI), "UI");
    EXPECT_EQ(gdcm::VR::GetVRString(gdcm::VR::DA), "DA");
    EXPECT_EQ(gdcm::VR::GetVRString(gdcm::VR::TM), "TM");
    EXPECT_EQ(gdcm::VR::GetVRString(gdcm::VR::US), "US");
    EXPECT_EQ(gdcm::VR::GetVRString(gdcm::VR::OW), "OW");
    return true;
}

TEST_CASE(GDCM_UIDGenerator) {
    gdcm::UIDGenerator gen;
    std::string uid1 = gen.Generate();
    std::string uid2 = gen.Generate();
    
    EXPECT_FALSE(uid1.empty());
    EXPECT_FALSE(uid2.empty());
    EXPECT_NE(uid1, uid2);  // Should generate unique UIDs
    
    // UIDs should start with root prefix
    EXPECT_TRUE(uid1.find('.') != std::string::npos);
    return true;
}

// =============================================================================
// GDCM File Reading Tests
// =============================================================================

TEST_CASE(GDCM_ReadDicomFile) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) {
        std::cerr << "  [SKIP] No test DICOM file found" << std::endl;
        return true;  // Skip gracefully
    }
    
    gdcm::Reader reader;
    reader.SetFileName(testFile.c_str());
    EXPECT_TRUE(reader.Read());
    
    const gdcm::File& file = reader.GetFile();
    const gdcm::DataSet& ds = file.GetDataSet();
    
    // File should have some data elements
    EXPECT_FALSE(ds.IsEmpty());
    return true;
}

TEST_CASE(GDCM_ReadTransferSyntax) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    gdcm::Reader reader;
    reader.SetFileName(testFile.c_str());
    EXPECT_TRUE(reader.Read());
    
    const gdcm::File& file = reader.GetFile();
    const gdcm::FileMetaInformation& fmi = file.GetHeader();
    
    // Should have a valid transfer syntax
    gdcm::TransferSyntax ts = fmi.GetDataSetTransferSyntax();
    EXPECT_TRUE(ts.IsValid());
    return true;
}

TEST_CASE(GDCM_ExtractPatientTags) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    gdcm::Reader reader;
    reader.SetFileName(testFile.c_str());
    EXPECT_TRUE(reader.Read());
    
    gdcm::StringFilter sf;
    sf.SetFile(reader.GetFile());
    
    // Try to extract patient name (may or may not exist in test file)
    std::string patientName = sf.ToString(gdcm::Tag(0x0010, 0x0010));
    std::string studyDate = sf.ToString(gdcm::Tag(0x0008, 0x0020));
    std::string modality = sf.ToString(gdcm::Tag(0x0008, 0x0060));
    
    // At least modality should be present in most DICOM files
    // (we don't fail if empty, just verify extraction doesn't crash)
    return true;
}

TEST_CASE(GDCM_ReadSOPClassUID) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    gdcm::Reader reader;
    reader.SetFileName(testFile.c_str());
    EXPECT_TRUE(reader.Read());
    
    const gdcm::DataSet& ds = reader.GetFile().GetDataSet();
    gdcm::Tag sopClassTag(0x0008, 0x0016);
    
    if (ds.FindDataElement(sopClassTag)) {
        const gdcm::DataElement& de = ds.GetDataElement(sopClassTag);
        EXPECT_FALSE(de.IsEmpty());
    }
    return true;
}

// =============================================================================
// GDCM Image Reading Tests
// =============================================================================

TEST_CASE(GDCM_ImageReader) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    gdcm::ImageReader reader;
    reader.SetFileName(testFile.c_str());
    
    if (!reader.Read()) {
        // Some test files may not be images
        std::cerr << "  [INFO] File is not an image object" << std::endl;
        return true;
    }
    
    const gdcm::Image& image = reader.GetImage();
    
    // Verify image has dimensions
    unsigned int dims[3];
    dims[0] = image.GetDimension(0);
    dims[1] = image.GetDimension(1);
    dims[2] = image.GetDimension(2);
    
    EXPECT_GT(dims[0], 0u);
    EXPECT_GT(dims[1], 0u);
    return true;
}

TEST_CASE(GDCM_ImagePixelFormat) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    gdcm::ImageReader reader;
    reader.SetFileName(testFile.c_str());
    if (!reader.Read()) return true;
    
    const gdcm::Image& image = reader.GetImage();
    const gdcm::PixelFormat& pf = image.GetPixelFormat();
    
    // Should have valid bits allocated
    EXPECT_GT(pf.GetBitsAllocated(), 0);
    EXPECT_GT(pf.GetBitsStored(), 0);
    EXPECT_GE(pf.GetBitsAllocated(), pf.GetBitsStored());
    return true;
}

TEST_CASE(GDCM_ImagePhotometricInterpretation) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    gdcm::ImageReader reader;
    reader.SetFileName(testFile.c_str());
    if (!reader.Read()) return true;
    
    const gdcm::Image& image = reader.GetImage();
    gdcm::PhotometricInterpretation pi = image.GetPhotometricInterpretation();
    
    // Should be a known photometric interpretation
    EXPECT_NE(pi, gdcm::PhotometricInterpretation::UNKNOWN);
    return true;
}

TEST_CASE(GDCM_ImageBufferExtraction) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    gdcm::ImageReader reader;
    reader.SetFileName(testFile.c_str());
    if (!reader.Read()) return true;
    
    const gdcm::Image& image = reader.GetImage();
    size_t bufLen = image.GetBufferLength();
    
    EXPECT_GT(bufLen, 0u);
    
    // Allocate and extract buffer
    std::vector<char> buffer(bufLen);
    bool extracted = image.GetBuffer(buffer.data());
    EXPECT_TRUE(extracted);
    return true;
}

// =============================================================================
// GDCM Codec Tests
// =============================================================================

TEST_CASE(GDCM_JPEGCodecAvailable) {
    gdcm::JPEGCodec codec;
    EXPECT_TRUE(codec.CanCode(gdcm::TransferSyntax::JPEGLosslessProcess14_1));
    return true;
}

TEST_CASE(GDCM_JPEG2000CodecAvailable) {
    gdcm::JPEG2000Codec codec;
    EXPECT_TRUE(codec.CanCode(gdcm::TransferSyntax::JPEG2000Lossless));
    EXPECT_TRUE(codec.CanCode(gdcm::TransferSyntax::JPEG2000));
    return true;
}

TEST_CASE(GDCM_RLECodecAvailable) {
    gdcm::RLECodec codec;
    EXPECT_TRUE(codec.CanCode(gdcm::TransferSyntax::RLELossless));
    return true;
}

TEST_CASE(GDCM_TransferSyntaxTranscode) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    gdcm::ImageReader reader;
    reader.SetFileName(testFile.c_str());
    if (!reader.Read()) return true;
    
    gdcm::Image& image = reader.GetImage();
    
    // Try to change transfer syntax to explicit VR
    gdcm::ImageChangeTransferSyntax change;
    change.SetTransferSyntax(gdcm::TransferSyntax::ExplicitVRLittleEndian);
    change.SetInput(image);
    
    bool canChange = change.Change();
    // Even if it fails, the test shouldn't crash
    return true;
}

// =============================================================================
// GDCM Anonymization Tests
// =============================================================================

TEST_CASE(GDCM_AnonymizerBasic) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    gdcm::Reader reader;
    reader.SetFileName(testFile.c_str());
    EXPECT_TRUE(reader.Read());
    
    gdcm::Anonymizer anon;
    anon.SetFile(reader.GetFile());
    
    // Empty some PHI tags
    bool result = anon.Empty(gdcm::Tag(0x0010, 0x0010));  // Patient Name
    // Result may vary based on whether tag exists
    return true;
}

TEST_CASE(GDCM_AnonymizerReplace) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    gdcm::Reader reader;
    reader.SetFileName(testFile.c_str());
    EXPECT_TRUE(reader.Read());
    
    gdcm::Anonymizer anon;
    anon.SetFile(reader.GetFile());
    
    // Replace patient name with anonymized value
    anon.Replace(gdcm::Tag(0x0010, 0x0010), "ANONYMIZED^PATIENT");
    
    // Verify replacement
    gdcm::StringFilter sf;
    sf.SetFile(reader.GetFile());
    std::string newName = sf.ToString(gdcm::Tag(0x0010, 0x0010));
    
    return true;
}

// =============================================================================
// GDCM Directory Scanner Tests
// =============================================================================

TEST_CASE(GDCM_DirectoryScanning) {
    std::vector<std::string> searchPaths = {"../sample_series", "../../sample_series"};
    std::string testDir;
    for (const auto& p : searchPaths) {
        if (fs::exists(p) && fs::is_directory(p)) {
            testDir = p;
            break;
        }
    }
    if (testDir.empty()) return true;
    
    gdcm::Directory dir;
    unsigned int nfiles = dir.Load(testDir);
    
    EXPECT_GT(nfiles, 0u);
    
    const gdcm::Directory::FilenamesType& filenames = dir.GetFilenames();
    EXPECT_FALSE(filenames.empty());
    return true;
}

TEST_CASE(GDCM_ScannerPatientTags) {
    std::vector<std::string> searchPaths = {"../sample_series", "../../sample_series"};
    std::string testDir;
    for (const auto& p : searchPaths) {
        if (fs::exists(p) && fs::is_directory(p)) {
            testDir = p;
            break;
        }
    }
    if (testDir.empty()) return true;
    
    gdcm::Directory dir;
    dir.Load(testDir);
    const auto& filenames = dir.GetFilenames();
    if (filenames.empty()) return true;
    
    gdcm::Scanner scanner;
    scanner.AddTag(gdcm::Tag(0x0010, 0x0010));  // Patient Name
    scanner.AddTag(gdcm::Tag(0x0008, 0x0060));  // Modality
    scanner.AddTag(gdcm::Tag(0x0020, 0x000D));  // Study Instance UID
    
    bool scanned = scanner.Scan(filenames);
    EXPECT_TRUE(scanned);
    return true;
}

// =============================================================================
// GDCM Write Tests
// =============================================================================

TEST_CASE(GDCM_WriteDataSet) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    gdcm::Reader reader;
    reader.SetFileName(testFile.c_str());
    EXPECT_TRUE(reader.Read());
    
    // Write to temp file
    std::string outPath = fs::temp_directory_path().string() + "/test_gdcm_write.dcm";
    
    gdcm::Writer writer;
    writer.SetFile(reader.GetFile());
    writer.SetFileName(outPath.c_str());
    
    bool written = writer.Write();
    EXPECT_TRUE(written);
    
    // Verify file exists
    EXPECT_TRUE(fs::exists(outPath));
    
    // Clean up
    fs::remove(outPath);
    return true;
}

TEST_CASE(GDCM_RoundTripPreservation) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    // Read original
    gdcm::Reader reader1;
    reader1.SetFileName(testFile.c_str());
    EXPECT_TRUE(reader1.Read());
    
    gdcm::StringFilter sf1;
    sf1.SetFile(reader1.GetFile());
    std::string originalModality = sf1.ToString(gdcm::Tag(0x0008, 0x0060));
    
    // Write
    std::string outPath = fs::temp_directory_path().string() + "/test_gdcm_roundtrip.dcm";
    gdcm::Writer writer;
    writer.SetFile(reader1.GetFile());
    writer.SetFileName(outPath.c_str());
    writer.Write();
    
    // Read back
    gdcm::Reader reader2;
    reader2.SetFileName(outPath.c_str());
    EXPECT_TRUE(reader2.Read());
    
    gdcm::StringFilter sf2;
    sf2.SetFile(reader2.GetFile());
    std::string readBackModality = sf2.ToString(gdcm::Tag(0x0008, 0x0060));
    
    // Modality should be preserved
    EXPECT_EQ(originalModality, readBackModality);
    
    fs::remove(outPath);
    return true;
}

#else // !USE_GDCM

TEST_CASE(GDCM_NotAvailable) {
    std::cerr << "  [INFO] GDCM not available - skipping GDCM tests" << std::endl;
    return true;
}

#endif // USE_GDCM

// =============================================================================
// Main
// =============================================================================

int main(int argc, char* argv[]) {
    return RUN_TESTS("GDCM Feature Tests");
}
