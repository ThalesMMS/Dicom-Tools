//
// FileSystemUtils.h
// DicomToolsCpp
//
// Declares filesystem helpers used to locate sample DICOM files and prepare output directories.
//
// Thales Matheus Mendonça Santos - November 2025

#pragma once

#include <string>

namespace FileSystemUtils {
    // Locate any DICOM file under the provided root to use as a default input
    std::string FindFirstDicom(const std::string& inputDir);
    // Ensure the destination directory exists and is a folder
    bool EnsureOutputDir(const std::string& path);
}
