//
// CLIParser.cpp
// DicomToolsCpp
//
// Implements a lightweight argument parser and usage printer for the command suite without extra dependencies.
//
// Thales Matheus Mendonça Santos - November 2025

#include "CLIParser.h"

#include <iostream>
#include <string>
#include <vector>

namespace {
// Add a tiny helper so we do not repeat short/long comparisons everywhere
bool IsFlag(const std::string& arg, const std::string& shortFlag, const std::string& longFlag) {
    return arg == shortFlag || arg == longFlag;
}
}

CLIOptions ParseCLIArgs(int argc, char* argv[], const CommandRegistry& registry) {
    CLIOptions opts;

    // Classic hand-rolled parser keeps dependencies minimal and readable
    for (int i = 1; i < argc; ++i) {
        std::string arg(argv[i]);
        if (IsFlag(arg, "-h", "--help")) {
            opts.help = true;
        } else if (IsFlag(arg, "-l", "--list")) {
            opts.list = true;
        } else if (IsFlag(arg, "-m", "--modules")) {
            opts.modules = true;
        } else if (IsFlag(arg, "-v", "--verbose")) {
            opts.verbose = true;
        } else if (IsFlag(arg, "-i", "--input")) {
            if (i + 1 < argc) {
                opts.inputPath = argv[++i];
            } else {
                std::cerr << "Missing value for --input" << std::endl;
            }
        } else if (IsFlag(arg, "-o", "--output")) {
            if (i + 1 < argc) {
                opts.outputDir = argv[++i];
            } else {
                std::cerr << "Missing value for --output" << std::endl;
            }
        } else if (opts.command.empty()) {
            opts.command = arg;
        } else {
            std::cerr << "Unrecognized argument: " << arg << std::endl;
        }
    }

    if (opts.command.empty() && !opts.list && !opts.modules) {
        opts.help = true;
    }

    // When showing help with no command, suggest running "all" if available
    if (opts.help && opts.command.empty() && !opts.list && !opts.modules) {
        // Favor the "all" command when nothing was provided and we showed help
        if (registry.Exists("all")) {
            opts.command = "all";
        }
    }

    return opts;
}

void PrintUsage(std::ostream& os, const CommandRegistry& registry) {
    os << "Usage: ./DicomTools <command> [options]" << std::endl;
    os << "Options:" << std::endl;
    os << "  -h, --help           Show this help text" << std::endl;
    os << "  -l, --list           List available commands" << std::endl;
    os << "  -m, --modules        Show module availability and feature coverage" << std::endl;
    os << "  -i, --input <path>   Specify DICOM file or directory" << std::endl;
    os << "  -o, --output <dir>   Output directory (default: output)" << std::endl;
    os << "  -v, --verbose        Print extra details for commands" << std::endl;
    os << std::endl;
    os << "Commands:" << std::endl;
    // Leverage registry for up-to-date list so usage always matches capabilities
    registry.List(os);
}
