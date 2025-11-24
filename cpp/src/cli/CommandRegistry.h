//
// CommandRegistry.h
// DicomToolsCpp
//
// Declares the registry that stores commands, groups them, and executes callbacks with shared context.
//
// Thales Matheus Mendonça Santos - November 2025

#pragma once

#include <functional>
#include <map>
#include <ostream>
#include <string>
#include <vector>

struct CommandContext {
    // Shared execution context propagated to every command handler
    std::string inputPath;
    std::string outputDir;
    bool verbose{false};
};

struct Command {
    // Metadata and callback for a single CLI command
    std::string name;
    std::string module;
    std::string description;
    std::function<int(const CommandContext&)> action;
};

class CommandRegistry {
public:
    // Register a command; duplicates are ignored with a warning
    void Register(const Command& command);
    // Check if a command exists without running it
    bool Exists(const std::string& name) const;
    // Execute a registered command by name
    int Run(const std::string& name, const CommandContext& context) const;
    // Emit a grouped list of commands to a stream
    void List(std::ostream& os) const;
    // Copy of registered commands in insertion order (for tests/UI)
    std::vector<Command> GetCommands() const;

private:
    std::vector<Command> ordered_;
    std::map<std::string, std::size_t> index_;
};
