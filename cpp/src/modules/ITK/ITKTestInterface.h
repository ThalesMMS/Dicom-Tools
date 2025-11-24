//
// ITKTestInterface.h
// DicomToolsCpp
//
// Declares the registration hook for ITK feature commands used by the CLI.
//
// Thales Matheus Mendonça Santos - November 2025

#pragma once
#include <string>

class CommandRegistry;

namespace ITKTests {
    // Registers ITK feature demos with the CLI registry
    void RegisterCommands(CommandRegistry& registry);
}
