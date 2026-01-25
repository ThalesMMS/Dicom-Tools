//
// test_framework.h
// DicomToolsCpp
//
// Lightweight test framework for C++ unit tests with colored output and summary statistics.
//
// Thales Matheus Mendonça Santos - November 2025

#pragma once

#include <iostream>
#include <string>
#include <vector>
#include <functional>
#include <chrono>
#include <sstream>
#include <iomanip>

namespace TestFramework {

// ANSI color codes for terminal output
struct Colors {
    static constexpr const char* Reset   = "\033[0m";
    static constexpr const char* Red     = "\033[31m";
    static constexpr const char* Green   = "\033[32m";
    static constexpr const char* Yellow  = "\033[33m";
    static constexpr const char* Blue    = "\033[34m";
    static constexpr const char* Cyan    = "\033[36m";
    static constexpr const char* Bold    = "\033[1m";
};

struct TestResult {
    std::string name;
    bool passed;
    std::string message;
    double duration_ms;
};

class TestRunner {
public:
    static TestRunner& Instance() {
        static TestRunner instance;
        return instance;
    }

    void RegisterTest(const std::string& name, std::function<bool()> testFn) {
        tests_.push_back({name, testFn});
    }

    int Run(const std::string& suiteName) {
        std::cout << Colors::Bold << Colors::Cyan 
                  << "\n========================================\n"
                  << " Running: " << suiteName
                  << "\n========================================\n"
                  << Colors::Reset << std::endl;

        std::vector<TestResult> results;
        int passed = 0, failed = 0, skipped = 0;

        for (const auto& test : tests_) {
            std::cout << Colors::Blue << "[RUN     ] " << Colors::Reset << test.first << std::flush;
            
            auto start = std::chrono::high_resolution_clock::now();
            bool result = false;
            std::string errorMsg;
            
            try {
                result = test.second();
            } catch (const std::exception& e) {
                errorMsg = e.what();
            } catch (...) {
                errorMsg = "Unknown exception";
            }
            
            auto end = std::chrono::high_resolution_clock::now();
            double duration = std::chrono::duration<double, std::milli>(end - start).count();

            if (result) {
                std::cout << "\r" << Colors::Green << "[  PASS  ] " << Colors::Reset 
                          << test.first << " (" << std::fixed << std::setprecision(1) 
                          << duration << " ms)" << std::endl;
                passed++;
                results.push_back({test.first, true, "", duration});
            } else {
                std::cout << "\r" << Colors::Red << "[  FAIL  ] " << Colors::Reset 
                          << test.first << " (" << std::fixed << std::setprecision(1) 
                          << duration << " ms)";
                if (!errorMsg.empty()) {
                    std::cout << " - " << errorMsg;
                }
                std::cout << std::endl;
                failed++;
                results.push_back({test.first, false, errorMsg, duration});
            }
        }

        // Summary
        std::cout << Colors::Bold << Colors::Cyan 
                  << "\n----------------------------------------\n"
                  << " Summary: " << suiteName
                  << "\n----------------------------------------\n"
                  << Colors::Reset;
        std::cout << Colors::Green << "  Passed:  " << passed << Colors::Reset << std::endl;
        std::cout << Colors::Red << "  Failed:  " << failed << Colors::Reset << std::endl;
        std::cout << "  Total:   " << tests_.size() << std::endl;
        std::cout << Colors::Cyan << "----------------------------------------\n" << Colors::Reset;

        return failed == 0 ? 0 : 1;
    }

    void Clear() { tests_.clear(); }

private:
    std::vector<std::pair<std::string, std::function<bool()>>> tests_;
};

// Macros for test registration and assertions
#define TEST_CASE(name) \
    static bool test_##name(); \
    static struct TestRegistrar_##name { \
        TestRegistrar_##name() { \
            TestFramework::TestRunner::Instance().RegisterTest(#name, test_##name); \
        } \
    } registrar_##name; \
    static bool test_##name()

#define EXPECT_TRUE(expr) \
    do { if (!(expr)) { \
        std::cerr << "  EXPECT_TRUE failed: " << #expr << " at " << __FILE__ << ":" << __LINE__ << std::endl; \
        return false; \
    }} while(0)

#define EXPECT_FALSE(expr) \
    do { if (expr) { \
        std::cerr << "  EXPECT_FALSE failed: " << #expr << " at " << __FILE__ << ":" << __LINE__ << std::endl; \
        return false; \
    }} while(0)

#define EXPECT_EQ(a, b) \
    do { if ((a) != (b)) { \
        std::cerr << "  EXPECT_EQ failed: " << #a << " != " << #b << " at " << __FILE__ << ":" << __LINE__ << std::endl; \
        return false; \
    }} while(0)

#define EXPECT_NE(a, b) \
    do { if ((a) == (b)) { \
        std::cerr << "  EXPECT_NE failed: " << #a << " == " << #b << " at " << __FILE__ << ":" << __LINE__ << std::endl; \
        return false; \
    }} while(0)

#define EXPECT_GT(a, b) \
    do { if (!((a) > (b))) { \
        std::cerr << "  EXPECT_GT failed: " << #a << " <= " << #b << " at " << __FILE__ << ":" << __LINE__ << std::endl; \
        return false; \
    }} while(0)

#define EXPECT_GE(a, b) \
    do { if (!((a) >= (b))) { \
        std::cerr << "  EXPECT_GE failed: " << #a << " < " << #b << " at " << __FILE__ << ":" << __LINE__ << std::endl; \
        return false; \
    }} while(0)

#define EXPECT_LT(a, b) \
    do { if (!((a) < (b))) { \
        std::cerr << "  EXPECT_LT failed: " << #a << " >= " << #b << " at " << __FILE__ << ":" << __LINE__ << std::endl; \
        return false; \
    }} while(0)

#define EXPECT_THROW(expr, exc_type) \
    do { bool caught = false; try { expr; } catch (const exc_type&) { caught = true; } \
    if (!caught) { \
        std::cerr << "  EXPECT_THROW failed: no " << #exc_type << " thrown at " << __FILE__ << ":" << __LINE__ << std::endl; \
        return false; \
    }} while(0)

#define EXPECT_NO_THROW(expr) \
    do { try { expr; } catch (...) { \
        std::cerr << "  EXPECT_NO_THROW failed: exception thrown at " << __FILE__ << ":" << __LINE__ << std::endl; \
        return false; \
    }} while(0)

#define RUN_TESTS(suite_name) \
    TestFramework::TestRunner::Instance().Run(suite_name)

} // namespace TestFramework
