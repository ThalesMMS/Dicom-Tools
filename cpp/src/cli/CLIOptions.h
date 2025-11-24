//
// CLIOptions.h
// DicomToolsCpp
//
// Defines the structure that stores parsed command-line flags and defaults for the CLI frontend.
//
// Thales Matheus Mendonça Santos - November 2025

#pragma once

#include <string>

struct CLIOptions {
    // Parsed command-line options captured by CLIParser
    std::string command;
    std::string inputPath;
    std::string outputDir{"output"};
    bool list{false};
    bool modules{false};
    bool help{false};
    bool verbose{false};
};
