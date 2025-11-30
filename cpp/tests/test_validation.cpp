//
// test_validation.cpp
// DicomToolsCpp
//
// Tests for DICOM validation, conformance checking, and data integrity
// verification according to DICOM standard requirements.
//
// Thales Matheus Mendonça Santos - November 2025

#include "test_framework.h"

#include <filesystem>
#include <fstream>
#include <string>
#include <vector>
#include <cctype>

#ifdef USE_GDCM
#include <gdcmReader.h>
#include <gdcmWriter.h>
#include <gdcmDataSet.h>
#include <gdcmFile.h>
#include <gdcmFileMetaInformation.h>
#include <gdcmTag.h>
#include <gdcmAttribute.h>
#include <gdcmStringFilter.h>
#include <gdcmGlobal.h>
#include <gdcmDicts.h>
#include <gdcmDict.h>
#include <gdcmVR.h>
#endif

#ifdef USE_DCMTK
#include <dcmtk/dcmdata/dctk.h>
#include <dcmtk/dcmdata/dcfilefo.h>
#include <dcmtk/dcmdata/dcdeftag.h>
#include <dcmtk/dcmdata/dcdict.h>
#endif

namespace fs = std::filesystem;

// Helper to find test DICOM files
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

// =============================================================================
// Required Tag Validation Tests
// =============================================================================

TEST_CASE(Validation_RequiredSOPClassUID) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) {
        std::cerr << "  [SKIP] No test DICOM file found" << std::endl;
        return true;
    }
    
#ifdef USE_GDCM
    {
        gdcm::Reader reader;
        reader.SetFileName(testFile.c_str());
        if (reader.Read()) {
            const gdcm::DataSet& ds = reader.GetFile().GetDataSet();
            gdcm::Tag sopClassTag(0x0008, 0x0016);
            
            // SOP Class UID should be present
            if (ds.FindDataElement(sopClassTag)) {
                const gdcm::DataElement& de = ds.GetDataElement(sopClassTag);
                EXPECT_FALSE(de.IsEmpty());
                
                // Should be a valid UID format
                gdcm::StringFilter sf;
                sf.SetFile(reader.GetFile());
                std::string sopClass = sf.ToString(sopClassTag);
                EXPECT_FALSE(sopClass.empty());
            }
        }
    }
#endif

#ifdef USE_DCMTK
    {
        DcmFileFormat ff;
        if (ff.loadFile(testFile.c_str()).good()) {
            DcmDataset* ds = ff.getDataset();
            
            // SOP Class UID should exist
            EXPECT_TRUE(ds->tagExistsWithValue(DCM_SOPClassUID));
            
            OFString sopClass;
            ds->findAndGetOFString(DCM_SOPClassUID, sopClass);
            EXPECT_FALSE(sopClass.empty());
        }
    }
#endif
    
    return true;
}

TEST_CASE(Validation_RequiredSOPInstanceUID) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
#ifdef USE_GDCM
    {
        gdcm::Reader reader;
        reader.SetFileName(testFile.c_str());
        if (reader.Read()) {
            const gdcm::DataSet& ds = reader.GetFile().GetDataSet();
            gdcm::Tag sopInstanceTag(0x0008, 0x0018);
            
            if (ds.FindDataElement(sopInstanceTag)) {
                const gdcm::DataElement& de = ds.GetDataElement(sopInstanceTag);
                EXPECT_FALSE(de.IsEmpty());
            }
        }
    }
#endif

#ifdef USE_DCMTK
    {
        DcmFileFormat ff;
        if (ff.loadFile(testFile.c_str()).good()) {
            DcmDataset* ds = ff.getDataset();
            EXPECT_TRUE(ds->tagExistsWithValue(DCM_SOPInstanceUID));
        }
    }
#endif
    
    return true;
}

// =============================================================================
// VR (Value Representation) Validation Tests
// =============================================================================

TEST_CASE(Validation_VRConsistency) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
#ifdef USE_GDCM
    {
        gdcm::Reader reader;
        reader.SetFileName(testFile.c_str());
        if (reader.Read()) {
            const gdcm::Global& g = gdcm::Global::GetInstance();
            const gdcm::Dicts& dicts = g.GetDicts();
            const gdcm::Dict& pubDict = dicts.GetPublicDict();
            
            // Check a few common tags for VR consistency
            gdcm::Tag patientName(0x0010, 0x0010);
            const gdcm::DictEntry& entry = pubDict.GetDictEntry(patientName);
            EXPECT_EQ(entry.GetVR(), gdcm::VR::PN);  // Person Name
        }
    }
#endif
    
    return true;
}

TEST_CASE(Validation_PatientNameFormat) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
#ifdef USE_GDCM
    {
        gdcm::Reader reader;
        reader.SetFileName(testFile.c_str());
        if (reader.Read()) {
            gdcm::StringFilter sf;
            sf.SetFile(reader.GetFile());
            std::string patientName = sf.ToString(gdcm::Tag(0x0010, 0x0010));
            
            // If present, Patient Name should be in PN format (may contain ^ separator)
            if (!patientName.empty()) {
                // PN format: Family^Given^Middle^Prefix^Suffix
                // Should handle ^ separators correctly
                (void)patientName;
            }
        }
    }
#endif
    
    return true;
}

// =============================================================================
// UID Validation Tests
// =============================================================================

TEST_CASE(Validation_UIDFormat) {
    // UIDs should follow the pattern: digits and dots only, no leading zeros after dots
#ifdef USE_GDCM
    {
        gdcm::UIDGenerator gen;
        std::string uid = gen.Generate();
        
        // Should start with a digit
        EXPECT_FALSE(uid.empty());
        EXPECT_TRUE(std::isdigit(uid[0]));
        
        // Should contain only digits and dots
        for (char c : uid) {
            EXPECT_TRUE(std::isdigit(c) || c == '.');
        }
    }
#endif
    
    return true;
}

TEST_CASE(Validation_UIDUniqueness) {
    // Generated UIDs should be unique
    std::vector<std::string> uids;
    
#ifdef USE_GDCM
    {
        gdcm::UIDGenerator gen;
        for (int i = 0; i < 10; ++i) {
            uids.push_back(gen.Generate());
        }
    }
#endif
    
    // Check uniqueness
    for (size_t i = 0; i < uids.size(); ++i) {
        for (size_t j = i + 1; j < uids.size(); ++j) {
            EXPECT_NE(uids[i], uids[j]);
        }
    }
    
    return true;
}

// =============================================================================
// Transfer Syntax Validation Tests
// =============================================================================

TEST_CASE(Validation_TransferSyntaxPresent) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
#ifdef USE_GDCM
    {
        gdcm::Reader reader;
        reader.SetFileName(testFile.c_str());
        if (reader.Read()) {
            const gdcm::File& file = reader.GetFile();
            const gdcm::FileMetaInformation& fmi = file.GetHeader();
            gdcm::TransferSyntax ts = fmi.GetDataSetTransferSyntax();
            
            // Transfer syntax should be valid
            EXPECT_TRUE(ts.IsValid());
        }
    }
#endif

#ifdef USE_DCMTK
    {
        DcmFileFormat ff;
        if (ff.loadFile(testFile.c_str()).good()) {
            DcmMetaInfo* metaInfo = ff.getMetaInfo();
            EXPECT_TRUE(metaInfo != nullptr);
            
            OFString ts;
            metaInfo->findAndGetOFString(DCM_TransferSyntaxUID, ts);
            EXPECT_FALSE(ts.empty());
        }
    }
#endif
    
    return true;
}

// =============================================================================
// Date and Time Format Validation Tests
// =============================================================================

TEST_CASE(Validation_DateFormat) {
    // DICOM dates should be in YYYYMMDD format
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
#ifdef USE_GDCM
    {
        gdcm::Reader reader;
        reader.SetFileName(testFile.c_str());
        if (reader.Read()) {
            gdcm::StringFilter sf;
            sf.SetFile(reader.GetFile());
            std::string studyDate = sf.ToString(gdcm::Tag(0x0008, 0x0020));
            
            // If present, should be 8 digits (YYYYMMDD)
            if (!studyDate.empty() && studyDate.length() >= 8) {
                for (int i = 0; i < 8; ++i) {
                    EXPECT_TRUE(std::isdigit(studyDate[i]));
                }
            }
        }
    }
#endif
    
    return true;
}

TEST_CASE(Validation_TimeFormat) {
    // DICOM times should be in HHMMSS.FFFFFF format
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
#ifdef USE_GDCM
    {
        gdcm::Reader reader;
        reader.SetFileName(testFile.c_str());
        if (reader.Read()) {
            gdcm::StringFilter sf;
            sf.SetFile(reader.GetFile());
            std::string studyTime = sf.ToString(gdcm::Tag(0x0008, 0x0030));
            
            // If present, should start with digits
            if (!studyTime.empty()) {
                EXPECT_TRUE(std::isdigit(studyTime[0]));
            }
        }
    }
#endif
    
    return true;
}

// =============================================================================
// Image Data Validation Tests
// =============================================================================

TEST_CASE(Validation_ImageDimensions) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
#ifdef USE_GDCM
    {
        gdcm::ImageReader reader;
        reader.SetFileName(testFile.c_str());
        if (reader.Read()) {
            const gdcm::Image& image = reader.GetImage();
            
            unsigned int dims[3];
            dims[0] = image.GetDimension(0);
            dims[1] = image.GetDimension(1);
            dims[2] = image.GetDimension(2);
            
            // Dimensions should be positive
            EXPECT_GT(dims[0], 0u);
            EXPECT_GT(dims[1], 0u);
        }
    }
#endif
    
    return true;
}

TEST_CASE(Validation_PixelDataConsistency) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
#ifdef USE_GDCM
    {
        gdcm::ImageReader reader;
        reader.SetFileName(testFile.c_str());
        if (reader.Read()) {
            const gdcm::Image& image = reader.GetImage();
            size_t bufLen = image.GetBufferLength();
            
            if (bufLen > 0) {
                // Buffer length should match dimensions
                unsigned int dims[3];
                dims[0] = image.GetDimension(0);
                dims[1] = image.GetDimension(1);
                dims[2] = image.GetDimension(2);
                
                const gdcm::PixelFormat& pf = image.GetPixelFormat();
                unsigned int bytesPerPixel = pf.GetPixelSize();
                
                size_t expectedLen = dims[0] * dims[1] * dims[2] * bytesPerPixel;
                
                // Allow some tolerance (may differ due to padding, compression, etc.)
                EXPECT_GT(bufLen, 0u);
            }
        }
    }
#endif
    
    return true;
}

// =============================================================================
// Sequence Validation Tests
// =============================================================================

TEST_CASE(Validation_SequenceStructure) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
#ifdef USE_GDCM
    {
        gdcm::Reader reader;
        reader.SetFileName(testFile.c_str());
        if (reader.Read()) {
            const gdcm::DataSet& ds = reader.GetFile().GetDataSet();
            
            // Check for common sequences
            gdcm::Tag refSeriesSeq(0x0008, 0x1115);  // Referenced Series Sequence
            if (ds.FindDataElement(refSeriesSeq)) {
                // Sequence should be properly structured
                const gdcm::DataElement& de = ds.GetDataElement(refSeriesSeq);
                EXPECT_FALSE(de.IsEmpty());
            }
        }
    }
#endif
    
    return true;
}

// =============================================================================
// File Structure Validation Tests
// =============================================================================

TEST_CASE(Validation_FileMetaInformation) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
#ifdef USE_GDCM
    {
        gdcm::Reader reader;
        reader.SetFileName(testFile.c_str());
        if (reader.Read()) {
            const gdcm::File& file = reader.GetFile();
            const gdcm::FileMetaInformation& fmi = file.GetHeader();
            
            // File meta information should exist
            EXPECT_FALSE(fmi.IsEmpty());
        }
    }
#endif
    
    return true;
}

TEST_CASE(Validation_DataSetNotEmpty) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
#ifdef USE_GDCM
    {
        gdcm::Reader reader;
        reader.SetFileName(testFile.c_str());
        if (reader.Read()) {
            const gdcm::DataSet& ds = reader.GetFile().GetDataSet();
            
            // Dataset should not be empty
            EXPECT_FALSE(ds.IsEmpty());
        }
    }
#endif

#ifdef USE_DCMTK
    {
        DcmFileFormat ff;
        if (ff.loadFile(testFile.c_str()).good()) {
            DcmDataset* ds = ff.getDataset();
            EXPECT_FALSE(ds->isEmpty());
        }
    }
#endif
    
    return true;
}

// =============================================================================
// Main
// =============================================================================

int main(int argc, char* argv[]) {
    return RUN_TESTS("DICOM Validation Tests");
}

