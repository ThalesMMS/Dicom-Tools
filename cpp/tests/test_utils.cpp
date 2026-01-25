//
// test_utils.cpp
// DicomToolsCpp
//
// Unit tests for utility functions including filesystem helpers,
// path manipulation, and general C++ utilities used across modules.
//
// Thales Matheus Mendonça Santos - November 2025

#include "test_framework.h"

#include <filesystem>
#include <fstream>
#include <cstdlib>
#include <string>

// Include the utility headers
#include "../src/utils/FileSystemUtils.h"

namespace fs = std::filesystem;

// =============================================================================
// FileSystemUtils Tests
// =============================================================================

TEST_CASE(Utils_FindFirstDicomInExistingDir) {
    std::vector<std::string> searchPaths = {
        "../sample_series",
        "../../sample_series",
        "../../../sample_series",
        "sample_series"
    };
    
    std::string foundFile;
    for (const auto& path : searchPaths) {
        foundFile = FileSystemUtils::FindFirstDicom(path);
        if (!foundFile.empty()) {
            break;
        }
    }
    
    if (foundFile.empty()) {
        std::cerr << "  [SKIP] No test DICOM directory found" << std::endl;
        return true;
    }
    
    EXPECT_FALSE(foundFile.empty());
    EXPECT_TRUE(fs::exists(foundFile));
    EXPECT_EQ(fs::path(foundFile).extension().string(), ".dcm");
    return true;
}

TEST_CASE(Utils_FindFirstDicomInNonExistentDir) {
    std::string result = FileSystemUtils::FindFirstDicom("/nonexistent/path/that/does/not/exist");
    EXPECT_TRUE(result.empty());
    return true;
}

TEST_CASE(Utils_FindFirstDicomInEmptyDir) {
    // Create temporary empty directory
    std::string tempDir = fs::temp_directory_path().string() + "/dicom_test_empty_" + std::to_string(std::time(nullptr));
    fs::create_directories(tempDir);
    
    std::string result = FileSystemUtils::FindFirstDicom(tempDir);
    EXPECT_TRUE(result.empty());
    
    fs::remove(tempDir);
    return true;
}

TEST_CASE(Utils_EnsureOutputDirCreatesNew) {
    std::string tempDir = fs::temp_directory_path().string() + "/dicom_test_output_" + std::to_string(std::time(nullptr));
    
    // Directory shouldn't exist yet
    EXPECT_FALSE(fs::exists(tempDir));
    
    bool result = FileSystemUtils::EnsureOutputDir(tempDir);
    EXPECT_TRUE(result);
    EXPECT_TRUE(fs::exists(tempDir));
    EXPECT_TRUE(fs::is_directory(tempDir));
    
    // Clean up
    fs::remove(tempDir);
    return true;
}

TEST_CASE(Utils_EnsureOutputDirExistingDir) {
    std::string tempDir = fs::temp_directory_path().string() + "/dicom_test_existing_" + std::to_string(std::time(nullptr));
    fs::create_directories(tempDir);
    
    // Directory should already exist
    EXPECT_TRUE(fs::exists(tempDir));
    
    bool result = FileSystemUtils::EnsureOutputDir(tempDir);
    EXPECT_TRUE(result);
    EXPECT_TRUE(fs::exists(tempDir));
    
    // Clean up
    fs::remove(tempDir);
    return true;
}

TEST_CASE(Utils_EnsureOutputDirNestedPath) {
    std::string baseDir = fs::temp_directory_path().string() + "/dicom_test_nested";
    std::string nestedDir = baseDir + "/level1/level2/level3";
    
    bool result = FileSystemUtils::EnsureOutputDir(nestedDir);
    EXPECT_TRUE(result);
    EXPECT_TRUE(fs::exists(nestedDir));
    EXPECT_TRUE(fs::is_directory(nestedDir));
    
    // Clean up
    fs::remove_all(baseDir);
    return true;
}

TEST_CASE(Utils_EnsureOutputDirWithFile) {
    // Create a file (not a directory)
    std::string tempFile = fs::temp_directory_path().string() + "/dicom_test_file_" + std::to_string(std::time(nullptr));
    {
        std::ofstream file(tempFile);
        file << "test content";
    }
    
    EXPECT_TRUE(fs::exists(tempFile));
    EXPECT_FALSE(fs::is_directory(tempFile));
    
    bool result = FileSystemUtils::EnsureOutputDir(tempFile);
    EXPECT_FALSE(result);  // Should fail because it's a file, not a dir
    
    // Clean up
    fs::remove(tempFile);
    return true;
}

// =============================================================================
// Path Manipulation Tests
// =============================================================================

TEST_CASE(Utils_PathExtensionCheck) {
    fs::path path1("test.dcm");
    fs::path path2("test.DCM");
    fs::path path3("test.dicom");
    fs::path path4("test");
    
    EXPECT_EQ(path1.extension().string(), ".dcm");
    
    // Extension comparison should be case-sensitive or handled appropriately
    std::string ext2 = path2.extension().string();
    EXPECT_TRUE(ext2 == ".DCM" || ext2 == ".dcm");
    
    EXPECT_NE(path3.extension().string(), ".dcm");
    EXPECT_TRUE(path4.extension().string().empty());
    return true;
}

TEST_CASE(Utils_PathResolution) {
    fs::path relative("../../sample_series");
    fs::path absolute = fs::absolute(relative);
    
    // Absolute path should not be empty
    EXPECT_FALSE(absolute.empty());
    
    // Absolute path should start with /
    std::string absStr = absolute.string();
    EXPECT_TRUE(absStr[0] == '/' || absStr[1] == ':');  // Unix or Windows root
    return true;
}

TEST_CASE(Utils_RecursiveDirectoryIteration) {
    std::vector<std::string> searchPaths = {
        "../sample_series",
        "../../sample_series",
        "../../../sample_series"
    };
    
    bool foundAny = false;
    for (const auto& base : searchPaths) {
        if (fs::exists(base) && fs::is_directory(base)) {
            int dcmCount = 0;
            for (const auto& entry : fs::recursive_directory_iterator(base)) {
                if (entry.path().extension() == ".dcm") {
                    dcmCount++;
                    foundAny = true;
                }
            }
            if (foundAny) {
                EXPECT_GT(dcmCount, 0);
                break;
            }
        }
    }
    
    // This test passes even if no DICOM files are found (graceful skip)
    return true;
}

// =============================================================================
// Filesystem Error Handling Tests
// =============================================================================

TEST_CASE(Utils_HandleInvalidPaths) {
    // Test with various invalid paths
    std::vector<std::string> invalidPaths = {
        "",
        ".",
        "..",
        "/",
        "//invalid//path//",
        "\0invalid\0"  // Null bytes (may cause issues)
    };
    
    for (const auto& path : invalidPaths) {
        if (path.empty() || path == "\0invalid\0") {
            // Skip truly problematic paths that might crash
            continue;
        }
        
        std::string result = FileSystemUtils::FindFirstDicom(path);
        // Should handle gracefully without crashing
        (void)result;  // Use result to avoid unused variable warning
    }
    
    return true;
}

TEST_CASE(Utils_PermissionsHandling) {
    // Test that EnsureOutputDir handles permission issues gracefully
    // (on Unix systems, /root might be unwritable; on Windows, C:\ might need admin)
    std::string readOnlyPath = "/";
    
    // This might fail, but shouldn't crash
    bool result = FileSystemUtils::EnsureOutputDir(readOnlyPath);
    // Result may be true or false depending on permissions
    // Just verify it doesn't crash
    return true;
}

// =============================================================================
// String and Conversion Tests
// =============================================================================

TEST_CASE(Utils_StringToPathConversion) {
    std::string pathStr = "../sample_series";
    fs::path path(pathStr);
    
    EXPECT_EQ(path.string(), pathStr);
    return true;
}

TEST_CASE(Utils_PathToStringConversion) {
    fs::path path("../sample_series");
    std::string pathStr = path.string();
    
    EXPECT_FALSE(pathStr.empty());
    return true;
}

// =============================================================================
// Main
// =============================================================================

int main(int argc, char* argv[]) {
    return RUN_TESTS("Utility Functions Tests");
}

