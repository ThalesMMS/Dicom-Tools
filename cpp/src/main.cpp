//
// main.cpp
// DicomToolsCpp
//
// Entry point that wires CLI parsing, module command registration, and dispatch for all DICOM test suites.
//
// Thales Matheus Mendonça Santos - November 2025

#include <iostream>
#include <iomanip>
#include <string>
#include <vector>

#include "cli/CLIOptions.h"
#include "cli/CLIParser.h"
#include "cli/CommandRegistry.h"
#include "modules/DCMTK/DCMTKTestInterface.h"
#include "modules/GDCM/GDCMTestInterface.h"
#include "modules/ITK/ITKTestInterface.h"
#include "modules/VTK/VTKTestInterface.h"
#include "utils/FileSystemUtils.h"

struct ModuleSummary {
    std::string name;
    bool enabled{false};
    std::vector<std::string> highlights;
};

std::vector<ModuleSummary> BuildModuleSummaries() {
    // High-level snapshot of which optional modules were compiled in
    return {
        {
            "GDCM",
#ifdef USE_GDCM
            true,
#else
            false,
#endif
            {"Anonymization + previews", "Transfer Syntax (RAW/J2K/RLE/JLS)", "Tag scan + pixel QA"}
        },
        {
            "DCMTK",
#ifdef USE_DCMTK
            true,
#else
            false,
#endif
            {"Tag editing + preview", "Pixel export/PPM/BMP", "DICOMDIR + JPEG/RLE codecs"}
        },
        {
            "ITK",
#ifdef USE_ITK
            true,
#else
            false,
#endif
            {"Filters + denoise", "Segmentation/MIP/resample", "NRRD + NIfTI export"}
        },
        {
            "VTK",
#ifdef USE_VTK
            true,
#else
            false,
#endif
            {"VTI/NIfTI export", "Surface/MPR/MIP/Mask", "Metadata + stats/resample"}
        }
    };
}

void PrintModuleSummary(const std::vector<ModuleSummary>& modules) {
    // Lightweight pretty-printer to present module availability and feature teasers
    std::cout << "Module Availability" << std::endl;
    std::cout << "-------------------" << std::endl;
    for (const auto& module : modules) {
        std::cout << "  " << std::left << std::setw(5) << module.name << " : "
                  << (module.enabled ? "ENABLED " : "DISABLED")
                  << " | ";
        for (std::size_t i = 0; i < module.highlights.size(); ++i) {
            std::cout << module.highlights[i];
            if (i + 1 < module.highlights.size()) {
                std::cout << ", ";
            }
        }
        std::cout << std::endl;
    }
    std::cout << std::endl;
}

int main(int argc, char* argv[]) {
    std::cout << "========================================" << std::endl;
    std::cout << "      Dicom-Tools-cpp Command Suite     " << std::endl;
    std::cout << "========================================" << std::endl;

    CommandRegistry registry;
    // Module-specific command injection
    GDCMTests::RegisterCommands(registry);
    DCMTKTests::RegisterCommands(registry);
    ITKTests::RegisterCommands(registry);
    VTKTests::RegisterCommands(registry);
    // Aggregate entry point that runs every available suite
    registry.Register({
        "all",
        "General",
        "Run every module suite",
        [&registry](const CommandContext& ctx) {
            int rc = 0;
            const std::vector<std::string> suites = {"test-gdcm", "test-dcmtk", "test-itk", "test-vtk"};
            for (const auto& suite : suites) {
                if (registry.Exists(suite)) {
                    rc |= registry.Run(suite, ctx);
                } else {
                    std::cout << "Skipping " << suite << " (module not available)" << std::endl;
                }
            }
            return rc;
        }
    });

    CLIOptions options = ParseCLIArgs(argc, argv, registry);

    if (options.modules) {
        PrintModuleSummary(BuildModuleSummaries());
        if (options.command.empty() && !options.list && !options.help) {
            return 0;
        }
    }

    if (options.list) {
        registry.List(std::cout);
        return 0;
    }

    if (options.help || options.command.empty()) {
        PrintUsage(std::cout, registry);
        return options.command.empty() ? 1 : 0;
    }

    if (!registry.Exists(options.command)) {
        std::cerr << "Unknown command: " << options.command << std::endl;
        PrintUsage(std::cout, registry);
        return 1;
    }

    std::string inputPath = options.inputPath;
    if (inputPath.empty()) {
        // Allow running commands without passing -i by grabbing any sample file
        inputPath = FileSystemUtils::FindFirstDicom(INPUT_DIR);
        if (inputPath.empty()) {
            std::cerr << "Error: No .dcm file provided and none found in " << INPUT_DIR << std::endl;
            return 1;
        }
        std::cout << "Auto-detected input file: " << inputPath << std::endl;
    }

    if (!FileSystemUtils::EnsureOutputDir(options.outputDir)) {
        return 1;
    }

    // Execute the selected command in the shared context
    CommandContext ctx{inputPath, options.outputDir, options.verbose};
    int result = registry.Run(options.command, ctx);

    std::cout << "========================================" << std::endl;
    return result;
}
