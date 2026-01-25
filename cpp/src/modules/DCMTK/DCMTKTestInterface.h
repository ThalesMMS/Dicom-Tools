//
// DCMTKTestInterface.h
// DicomToolsCpp
//
// Exposes registration of DCMTK feature commands into the shared CLI registry.
//
// Thales Matheus Mendonça Santos - November 2025

#pragma once
#include <string>

class CommandRegistry;

namespace DCMTKTests {
    // Registers DCMTK-backed commands with the shared registry
    void RegisterCommands(CommandRegistry& registry);
}
