//
// FileSystemUtils.cpp
// DicomToolsCpp
//
// Implements simple filesystem utilities for locating DICOM inputs and ensuring writable output destinations.
//
// Thales Matheus Mendonça Santos - November 2025

#include "FileSystemUtils.h"

#include <filesystem>
#include <iostream>

namespace fs = std::filesystem;

namespace FileSystemUtils {

std::string FindFirstDicom(const std::string& inputDir) {
    // Walk the directory tree and return the first .dcm file found (depth-first)
    if (fs::exists(inputDir) && fs::is_directory(inputDir)) {
        for (const auto& entry : fs::recursive_directory_iterator(inputDir)) {
            if (entry.path().extension() == ".dcm") {
                return entry.path().string();
            }
        }
    }
    return "";
}

bool EnsureOutputDir(const std::string& path) {
    // Make sure the output folder exists; create it if needed
    std::error_code ec;
    if (fs::exists(path, ec)) {
        if (!fs::is_directory(path, ec)) {
            std::cerr << "Output path exists but is not a directory: " << path << std::endl;
            return false;
        }
        return true;
    }

    if (!fs::create_directories(path, ec)) {
        std::cerr << "Failed to create output directory: " << path << " (" << ec.message() << ")" << std::endl;
        return false;
    }
    return true;
}

} // namespace FileSystemUtils
