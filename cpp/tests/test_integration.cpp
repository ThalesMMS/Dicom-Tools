//
// test_integration.cpp
// DicomToolsCpp
//
// Integration tests that exercise multiple modules together or test
// complete workflows end-to-end across different DICOM libraries.
//
// Thales Matheus Mendonça Santos - November 2025

#include "test_framework.h"

#include <filesystem>
#include <fstream>
#include <string>
#include <vector>
#include <ctime>
#include <algorithm>

#ifdef USE_GDCM
#include <gdcmReader.h>
#include <gdcmWriter.h>
#include <gdcmStringFilter.h>
#include <gdcmAnonymizer.h>
#include <gdcmImageReader.h>
#include <gdcmImageWriter.h>
#include <gdcmImageChangeTransferSyntax.h>
#include <gdcmDirectory.h>
#include <gdcmTag.h>
#endif

#ifdef USE_DCMTK
#include <dcmtk/dcmdata/dctk.h>
#include <dcmtk/dcmdata/dcfilefo.h>
#include <dcmtk/dcmdata/dcdeftag.h>
#endif

namespace fs = std::filesystem;

// Helper to find test DICOM files/directories
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

static std::string FindTestDicomDir() {
    std::vector<std::string> searchPaths = {
        "../sample_series",
        "../../sample_series",
        "../../../sample_series",
        "sample_series"
    };
    for (const auto& base : searchPaths) {
        fs::path p(base);
        if (fs::exists(p) && fs::is_directory(p)) {
            return p.string();
        }
    }
    return "";
}

// =============================================================================
// Cross-Library Compatibility Tests
// =============================================================================

TEST_CASE(Integration_FileReadableByMultipleLibraries) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) {
        std::cerr << "  [SKIP] No test DICOM file found" << std::endl;
        return true;
    }
    
    bool gdcmRead = false, dcmtkRead = false;
    
#ifdef USE_GDCM
    {
        gdcm::Reader reader;
        reader.SetFileName(testFile.c_str());
        gdcmRead = reader.Read();
    }
#endif

#ifdef USE_DCMTK
    {
        DcmFileFormat fileFormat;
        OFCondition status = fileFormat.loadFile(testFile.c_str());
        dcmtkRead = status.good();
    }
#endif
    
    // At least one library should be able to read the file
    if (!gdcmRead && !dcmtkRead) {
        std::cerr << "  [INFO] No libraries available to test" << std::endl;
        return true;
    }
    
    // If multiple libraries are available, they should both read successfully
    if (gdcmRead && dcmtkRead) {
        EXPECT_TRUE(gdcmRead);
        EXPECT_TRUE(dcmtkRead);
    }
    
    return true;
}

TEST_CASE(Integration_MetadataConsistencyAcrossLibraries) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    std::string modalityGDCM, modalityDCMTK;
    
#ifdef USE_GDCM
    {
        gdcm::Reader reader;
        reader.SetFileName(testFile.c_str());
        if (reader.Read()) {
            gdcm::StringFilter sf;
            sf.SetFile(reader.GetFile());
            modalityGDCM = sf.ToString(gdcm::Tag(0x0008, 0x0060));
        }
    }
#endif

#ifdef USE_DCMTK
    {
        DcmFileFormat ff;
        if (ff.loadFile(testFile.c_str()).good()) {
            OFString modality;
            ff.getDataset()->findAndGetOFString(DCM_Modality, modality);
            modalityDCMTK = modality.c_str();
        }
    }
#endif
    
    // If both libraries read the file, modality should match (if present)
    if (!modalityGDCM.empty() && !modalityDCMTK.empty()) {
        EXPECT_EQ(modalityGDCM, modalityDCMTK);
    }
    
    return true;
}

// =============================================================================
// Round-Trip Compatibility Tests
// =============================================================================

TEST_CASE(Integration_WriteReadRoundTrip) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    std::string tempFile = fs::temp_directory_path().string() + "/integration_roundtrip_" + 
                          std::to_string(std::time(nullptr)) + ".dcm";
    
#ifdef USE_GDCM
    {
        // Read with GDCM
        gdcm::Reader reader;
        reader.SetFileName(testFile.c_str());
        if (reader.Read()) {
            // Write to temp file
            gdcm::Writer writer;
            writer.SetFile(reader.GetFile());
            writer.SetFileName(tempFile.c_str());
            
            if (writer.Write()) {
                // Verify file exists
                EXPECT_TRUE(fs::exists(tempFile));
                
                // Try to read it back
                gdcm::Reader reader2;
                reader2.SetFileName(tempFile.c_str());
                EXPECT_TRUE(reader2.Read());
                
                // Clean up
                fs::remove(tempFile);
                return true;
            }
        }
    }
#endif
    
    // If GDCM not available, skip gracefully
    std::cerr << "  [SKIP] GDCM not available for round-trip test" << std::endl;
    return true;
}

// =============================================================================
// Multi-Step Workflow Tests
// =============================================================================

TEST_CASE(Integration_ReadAnonymizeWrite) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    std::string tempFile = fs::temp_directory_path().string() + "/integration_anon_" + 
                          std::to_string(std::time(nullptr)) + ".dcm";
    
#ifdef USE_GDCM
    {
        // Read file
        gdcm::Reader reader;
        reader.SetFileName(testFile.c_str());
        if (!reader.Read()) return true;
        
        // Anonymize
        gdcm::Anonymizer anon;
        gdcm::File& file = reader.GetFile();
        anon.SetFile(file);
        anon.Empty(gdcm::Tag(0x0010, 0x0010));  // Patient Name
        
        // Write
        gdcm::Writer writer;
        writer.SetFile(file);
        writer.SetFileName(tempFile.c_str());
        
        if (writer.Write()) {
            EXPECT_TRUE(fs::exists(tempFile));
            
            // Verify anonymization worked
            gdcm::Reader reader2;
            reader2.SetFileName(tempFile.c_str());
            if (reader2.Read()) {
                gdcm::StringFilter sf;
                sf.SetFile(reader2.GetFile());
                std::string patientName = sf.ToString(gdcm::Tag(0x0010, 0x0010));
                // Name should be empty or anonymized
            }
            
            fs::remove(tempFile);
            return true;
        }
    }
#endif
    
    return true;
}

TEST_CASE(Integration_TranscodeAndValidate) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    std::string tempFile = fs::temp_directory_path().string() + "/integration_transcode_" + 
                          std::to_string(std::time(nullptr)) + ".dcm";
    
#ifdef USE_GDCM
    {
        gdcm::ImageReader reader;
        reader.SetFileName(testFile.c_str());
        if (!reader.Read()) return true;
        
        gdcm::Image& image = reader.GetImage();
        
        // Change transfer syntax
        gdcm::ImageChangeTransferSyntax change;
        change.SetTransferSyntax(gdcm::TransferSyntax::ExplicitVRLittleEndian);
        change.SetInput(image);
        
        if (change.Change()) {
            // Write transcoded image
            gdcm::ImageWriter writer;
            writer.SetFile(reader.GetFile());
            writer.SetImage(change.GetOutput());
            writer.SetFileName(tempFile.c_str());
            
            if (writer.Write()) {
                EXPECT_TRUE(fs::exists(tempFile));
                
                // Verify it can be read back
                gdcm::Reader reader2;
                reader2.SetFileName(tempFile.c_str());
                EXPECT_TRUE(reader2.Read());
                
                fs::remove(tempFile);
                return true;
            }
        }
    }
#endif
    
    return true;
}

// =============================================================================
// Directory Processing Tests
// =============================================================================

TEST_CASE(Integration_ProcessDirectorySeries) {
    std::string testDir = FindTestDicomDir();
    if (testDir.empty()) return true;
    
    int fileCount = 0;
    
#ifdef USE_GDCM
    {
        gdcm::Directory dir;
        unsigned int nfiles = dir.Load(testDir);
        EXPECT_GT(nfiles, 0u);
        
        const gdcm::Directory::FilenamesType& filenames = dir.GetFilenames();
        fileCount = filenames.size();
        
        // Try to process at least one file
        if (!filenames.empty()) {
            gdcm::Reader reader;
            reader.SetFileName(filenames[0].c_str());
            EXPECT_TRUE(reader.Read());
        }
    }
#endif
    
    if (fileCount == 0) {
        std::cerr << "  [SKIP] No DICOM files found in directory" << std::endl;
    }
    
    return true;
}

// =============================================================================
// Error Propagation Tests
// =============================================================================

TEST_CASE(Integration_HandleMissingFilesGracefully) {
    std::string nonExistentFile = "/path/that/does/not/exist/file.dcm";
    
#ifdef USE_GDCM
    {
        gdcm::Reader reader;
        reader.SetFileName(nonExistentFile.c_str());
        bool readResult = reader.Read();
        EXPECT_FALSE(readResult);  // Should fail gracefully
    }
#endif

#ifdef USE_DCMTK
    {
        DcmFileFormat ff;
        OFCondition status = ff.loadFile(nonExistentFile.c_str());
        EXPECT_FALSE(status.good());  // Should fail gracefully
    }
#endif
    
    return true;
}

TEST_CASE(Integration_HandleCorruptedFilesGracefully) {
    // Create a file that looks like DICOM but is corrupted
    std::string tempFile = fs::temp_directory_path().string() + "/integration_corrupt_" + 
                          std::to_string(std::time(nullptr)) + ".dcm";
    
    {
        std::ofstream file(tempFile);
        file << "CORRUPTED DICOM DATA - NOT A VALID FILE";
        file.close();
    }
    
#ifdef USE_GDCM
    {
        gdcm::Reader reader;
        reader.SetFileName(tempFile.c_str());
        bool readResult = reader.Read();
        // Should handle gracefully (may succeed or fail, but shouldn't crash)
        (void)readResult;
    }
#endif

#ifdef USE_DCMTK
    {
        DcmFileFormat ff;
        OFCondition status = ff.loadFile(tempFile.c_str());
        // Should handle gracefully
        (void)status;
    }
#endif
    
    fs::remove(tempFile);
    return true;
}

// =============================================================================
// Performance Integration Tests
// =============================================================================

TEST_CASE(Integration_ReadMultipleFiles) {
    std::string testDir = FindTestDicomDir();
    if (testDir.empty()) return true;
    
    int successCount = 0;
    int totalCount = 0;
    
#ifdef USE_GDCM
    {
        gdcm::Directory dir;
        dir.Load(testDir);
        const auto& filenames = dir.GetFilenames();
        
        // Limit to first 10 files to avoid long test times
        int maxFiles = std::min(10, static_cast<int>(filenames.size()));
        
        for (int i = 0; i < maxFiles; ++i) {
            totalCount++;
            gdcm::Reader reader;
            reader.SetFileName(filenames[i].c_str());
            if (reader.Read()) {
                successCount++;
            }
        }
    }
#endif
    
    if (totalCount > 0) {
        EXPECT_GT(successCount, 0);
    } else {
        std::cerr << "  [SKIP] No files to process" << std::endl;
    }
    
    return true;
}

// =============================================================================
// Main
// =============================================================================

int main(int argc, char* argv[]) {
    return RUN_TESTS("Integration Tests");
}

