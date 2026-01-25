//
// GDCMTestInterface.h
// DicomToolsCpp
//
// Declares the function that registers GDCM feature commands into the CLI registry.
//
// Thales Matheus Mendonça Santos - November 2025

#pragma once
#include <string>

class CommandRegistry;

namespace GDCMTests {
    // Registers GDCM-related CLI commands
    void RegisterCommands(CommandRegistry& registry);
}
