//
// CLIParser.h
// DicomToolsCpp
//
// Declares utilities to parse CLI arguments into options and render usage text based on registered commands.
//
// Thales Matheus Mendonça Santos - November 2025

#pragma once

#include <ostream>

#include "CLIOptions.h"
#include "CommandRegistry.h"

// Parse argv into a CLIOptions struct using available commands for defaults
CLIOptions ParseCLIArgs(int argc, char* argv[], const CommandRegistry& registry);
// Print commands and flags in a consistent order
void PrintUsage(std::ostream& os, const CommandRegistry& registry);
