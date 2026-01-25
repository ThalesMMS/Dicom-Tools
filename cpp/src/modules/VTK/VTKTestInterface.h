//
// VTKTestInterface.h
// DicomToolsCpp
//
// Declares the function that registers VTK feature commands with the CLI registry.
//
// Thales Matheus Mendonça Santos - November 2025

#pragma once
#include <string>

class CommandRegistry;

namespace VTKTests {
    // Registers VTK utility commands for the CLI application
    void RegisterCommands(CommandRegistry& registry);
}
