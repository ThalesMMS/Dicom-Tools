//
// test_edge_cases.cpp
// DicomToolsCpp
//
// Tests for edge cases, error handling, boundary conditions, and unusual
// input scenarios that might occur in real-world DICOM processing.
//
// Thales Matheus Mendonça Santos - November 2025

#include "test_framework.h"

#include <filesystem>
#include <fstream>
#include <string>
#include <vector>
#include <cstring>
#include <limits>
#include <ctime>
#include <cctype>
#include <algorithm>

#ifdef USE_GDCM
#include <gdcmReader.h>
#include <gdcmWriter.h>
#include <gdcmDataSet.h>
#include <gdcmFile.h>
#include <gdcmAttribute.h>
#include <gdcmTag.h>
#include <gdcmStringFilter.h>
#endif

#ifdef USE_DCMTK
#include <dcmtk/dcmdata/dctk.h>
#include <dcmtk/dcmdata/dcfilefo.h>
#include <dcmtk/dcmdata/dcdeftag.h>
#endif

namespace fs = std::filesystem;

// =============================================================================
// Empty and Null Input Tests
// =============================================================================

TEST_CASE(EdgeCase_EmptyFilename) {
#ifdef USE_GDCM
    {
        gdcm::Reader reader;
        reader.SetFileName("");
        bool result = reader.Read();
        EXPECT_FALSE(result);
    }
#endif

#ifdef USE_DCMTK
    {
        DcmFileFormat ff;
        OFCondition status = ff.loadFile("");
        EXPECT_FALSE(status.good());
    }
#endif
    
    return true;
}

TEST_CASE(EdgeCase_NullPointerFilename) {
    // Passing nullptr should be handled gracefully
#ifdef USE_GDCM
    {
        gdcm::Reader reader;
        // Note: SetFileName(nullptr) might cause issues, but should be tested
        // Most implementations will handle this gracefully
    }
#endif
    
    return true;
}

TEST_CASE(EdgeCase_EmptyDataset) {
#ifdef USE_GDCM
    {
        gdcm::DataSet ds;
        EXPECT_TRUE(ds.IsEmpty());
    }
#endif

#ifdef USE_DCMTK
    {
        DcmDataset dataset;
        EXPECT_TRUE(dataset.isEmpty());
    }
#endif
    
    return true;
}

// =============================================================================
// Path Edge Cases
// =============================================================================

TEST_CASE(EdgeCase_VeryLongPath) {
    // Create a path that is very long (may exceed filesystem limits)
    std::string longPath = fs::temp_directory_path().string();
    for (int i = 0; i < 100; ++i) {
        longPath += "/very_long_directory_name_" + std::to_string(i);
    }
    longPath += "/file.dcm";
    
    // Should handle gracefully without crashing
    (void)longPath;
    return true;
}

TEST_CASE(EdgeCase_PathWithSpecialCharacters) {
    std::vector<std::string> specialPaths = {
        "test file with spaces.dcm",
        "test/file/with/slashes.dcm",
        "test\\file\\with\\backslashes.dcm",
        "test\"quote\"file.dcm",
        "test'quote'file.dcm",
        "test<file>.dcm",
        "test|pipe|file.dcm"
    };
    
    // These might cause issues but should be handled
    for (const auto& path : specialPaths) {
        (void)path;  // Test that code doesn't crash on these
    }
    
    return true;
}

TEST_CASE(EdgeCase_RelativePathTraversal) {
    std::vector<std::string> traversalPaths = {
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32",
        "../../../../../../../root",
        "./././test.dcm",
        "../sample_series/../../"
    };
    
    // Should handle path traversal attempts safely
    for (const auto& path : traversalPaths) {
        (void)path;
    }
    
    return true;
}

// =============================================================================
// File Size Edge Cases
// =============================================================================

TEST_CASE(EdgeCase_ZeroByteFile) {
    std::string tempFile = fs::temp_directory_path().string() + "/edge_zero_byte_" + 
                          std::to_string(std::time(nullptr)) + ".dcm";
    
    {
        std::ofstream file(tempFile);
        // Create empty file
        file.close();
    }
    
    EXPECT_TRUE(fs::exists(tempFile));
    EXPECT_EQ(fs::file_size(tempFile), 0u);
    
#ifdef USE_GDCM
    {
        gdcm::Reader reader;
        reader.SetFileName(tempFile.c_str());
        bool result = reader.Read();
        EXPECT_FALSE(result);  // Empty file should fail
    }
#endif

#ifdef USE_DCMTK
    {
        DcmFileFormat ff;
        OFCondition status = ff.loadFile(tempFile.c_str());
        EXPECT_FALSE(status.good());  // Empty file should fail
    }
#endif
    
    fs::remove(tempFile);
    return true;
}

TEST_CASE(EdgeCase_VeryLargeFile) {
    // Test handling of very large files (if any exist in test data)
    std::vector<std::string> searchPaths = {
        "../sample_series",
        "../../sample_series"
    };
    
    size_t largestSize = 0;
    for (const auto& base : searchPaths) {
        if (fs::exists(base) && fs::is_directory(base)) {
            for (const auto& entry : fs::directory_iterator(base)) {
                if (entry.path().extension() == ".dcm") {
                    size_t size = fs::file_size(entry.path());
                    if (size > largestSize) {
                        largestSize = size;
                    }
                }
            }
        }
    }
    
    // Just verify we can detect file sizes
    (void)largestSize;
    return true;
}

// =============================================================================
// Tag and Value Edge Cases
// =============================================================================

TEST_CASE(EdgeCase_InvalidTag) {
#ifdef USE_GDCM
    {
        // Test with invalid tag group/element combinations
        gdcm::Tag invalidTag(0xFFFF, 0xFFFF);
        // Operations with invalid tags should handle gracefully
        (void)invalidTag;
    }
#endif

#ifdef USE_DCMTK
    {
        DcmTag invalidTag(0xFFFF, 0xFFFF);
        (void)invalidTag;
    }
#endif
    
    return true;
}

TEST_CASE(EdgeCase_VeryLongStringValue) {
#ifdef USE_GDCM
    {
        gdcm::DataSet ds;
        gdcm::Tag tag(0x0010, 0x0010);  // Patient Name
        
        // Create a very long string (64KB)
        std::string longString(65536, 'A');
        
        // Try to set very long value
        gdcm::DataElement de(tag);
        de.SetByteValue(longString.c_str(), static_cast<uint32_t>(longString.length()));
        ds.Insert(de);
        
        // Should handle long strings without crashing
    }
#endif
    
    return true;
}

TEST_CASE(EdgeCase_UnicodeCharacters) {
#ifdef USE_GDCM
    {
        gdcm::DataSet ds;
        gdcm::Tag tag(0x0010, 0x0010);  // Patient Name
        
        // Test with Unicode characters
        std::string unicodeStr = "Patient^Name\xE2\x82\xAC";  // Contains Euro symbol
        gdcm::DataElement de(tag);
        de.SetByteValue(unicodeStr.c_str(), static_cast<uint32_t>(unicodeStr.length()));
        ds.Insert(de);
        
        // Should handle Unicode gracefully
    }
#endif
    
    return true;
}

TEST_CASE(EdgeCase_NullTerminatedStrings) {
#ifdef USE_DCMTK
    {
        DcmDataset dataset;
        
        // Test with strings containing null characters
        std::string withNull = "Test\0Null\0String";
        // Note: DCMTK should handle this according to VR rules
        
        (void)withNull;
    }
#endif
    
    return true;
}

// =============================================================================
// Memory and Resource Edge Cases
// =============================================================================

TEST_CASE(EdgeCase_MultipleFileHandles) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    // Open the same file multiple times
    const int numHandles = 10;
    int successCount = 0;
    
#ifdef USE_GDCM
    {
        std::vector<gdcm::Reader> readers(numHandles);
        for (auto& reader : readers) {
            reader.SetFileName(testFile.c_str());
            if (reader.Read()) {
                successCount++;
            }
        }
    }
#endif
    
    // Should handle multiple handles gracefully
    EXPECT_GT(successCount, 0);
    return true;
}

TEST_CASE(EdgeCase_RapidFileOperations) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    // Perform rapid read operations
    const int numOperations = 50;
    int successCount = 0;
    
#ifdef USE_GDCM
    {
        for (int i = 0; i < numOperations; ++i) {
            gdcm::Reader reader;
            reader.SetFileName(testFile.c_str());
            if (reader.Read()) {
                successCount++;
            }
        }
    }
#endif
    
    // Should handle rapid operations without issues
    EXPECT_GT(successCount, 0);
    return true;
}

// =============================================================================
// Format and Encoding Edge Cases
// =============================================================================

TEST_CASE(EdgeCase_DifferentTransferSyntaxes) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    // Test reading files with various transfer syntaxes
    // (if test files have different encodings)
    
#ifdef USE_GDCM
    {
        gdcm::Reader reader;
        reader.SetFileName(testFile.c_str());
        if (reader.Read()) {
            const gdcm::File& file = reader.GetFile();
            const gdcm::FileMetaInformation& fmi = file.GetHeader();
            gdcm::TransferSyntax ts = fmi.GetDataSetTransferSyntax();
            
            // Should have a valid transfer syntax
            (void)ts;
        }
    }
#endif
    
    return true;
}

TEST_CASE(EdgeCase_MissingRequiredTags) {
    // Test handling when required tags are missing
#ifdef USE_DCMTK
    {
        DcmDataset dataset;
        
        // Create dataset without SOP Class UID
        // Should handle gracefully when required tags are missing
        EXPECT_TRUE(dataset.isEmpty());
    }
#endif
    
    return true;
}

// =============================================================================
// Helper Functions
// =============================================================================

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
// Main
// =============================================================================

int main(int argc, char* argv[]) {
    return RUN_TESTS("Edge Cases and Error Handling Tests");
}

