# Overview

> **Relevant source files**
> * [BUILD.md](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/BUILD.md)
> * [README.md](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/README.md)
> * [scripts/setup_all.sh](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/scripts/setup_all.sh)

This document introduces the Dicom-Tools repository, a multi-language DICOM processing toolkit that provides unified interfaces across six programming language implementations. It covers the repository structure, core architectural patterns, and the key components that enable cross-language interoperability.

For step-by-step installation instructions, see [Installation and Setup](#1.2). For hands-on usage examples, see [Quick Start Guide](#1.3). For detailed information about individual language backends, see [Language Implementations](#4).

## Purpose and Scope

Dicom-Tools is a unified DICOM processing toolkit with command-line interfaces and utilities implemented in Python, Rust, C++, C#, Java, and JavaScript. The repository provides:

* **Six complete language backends** for DICOM file processing, network operations, and visualization
* **Unified CLI contract** that enables cross-language interoperability through a standardized request/response format
* **Multiple user interfaces**: Tkinter desktop GUI, headless contract runner, and web-based medical image viewer
* **Shared test data** in `sample_series/` used across all backends and tests
* **Adapter pattern** that isolates UI components from backend implementation details

Each language implementation leverages ecosystem-specific DICOM libraries while conforming to the same interface contract defined in `interface/CONTRACT.md`.

**Sources:** [README.md L1-L43](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/README.md#L1-L43)

## Repository Structure

The repository is organized with each language backend in its own top-level directory, plus shared components for interfaces and sample data:

```mermaid
flowchart TD

SampleData["sample_series/ Shared DICOM test files"]
Output["output/ Generated outputs"]
Scripts["scripts/ setup_all.sh package_all.sh"]
Python["python/ DICOM_reencoder/ CLI + 20+ commands"]
Rust["rust/ src/main.rs CLI + web server"]
Cpp["cpp/ DicomTools.cpp VTK/ITK integration"]
CSharp["cs/ DicomTools.Cli/ fo-dicom wrapper"]
Java["java/dcm4che-tests/ CLI + JUnit tests"]
JS["js/ viewer-gateway/ contract-cli/"]
TkApp["interface/app.py Tkinter GUI"]
ContractRunner["interface/contract_runner.py Headless executor"]
Adapters["interface/adapters/ *_adapter.py"]
Contract["interface/CONTRACT.md Specification"]

Contract -.->|"Implemented by"| Python
Contract -.->|"Implemented by"| Rust
Contract -.-> Cpp
Contract -.->|"Implemented by"| CSharp
Contract -.->|"Builds"| Java
Contract -.->|"Builds"| JS
Python -.-> SampleData
Rust -.-> SampleData
Cpp -.->|"Builds"| SampleData
CSharp -.->|"Builds"| SampleData
Java -.->|"Builds"| SampleData
Scripts -.-> Python
Scripts -.-> Rust
Scripts -.->|"Builds"| Cpp
Scripts -.-> CSharp
Scripts -.-> Java
Scripts -.-> JS

subgraph Interface ["Interface Layer"]
    TkApp
    ContractRunner
    Adapters
    Contract
    TkApp -.->|"Implemented by"| Adapters
    ContractRunner -.->|"Implemented by"| Adapters
    Adapters -.->|"Implemented by"| Contract
end

subgraph Backends ["Language Backends"]
    Python
    Rust
    Cpp
    CSharp
    Java
    JS
end

subgraph Root ["Repository Root"]
    SampleData
    Output
    Scripts
end
```

**Sources:** [README.md L1-L43](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/README.md#L1-L43)

 [scripts/setup_all.sh L1-L60](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/scripts/setup_all.sh#L1-L60)

### Directory Layout

| Directory | Purpose | Key Files |
| --- | --- | --- |
| `python/` | Python backend with pydicom, pynetdicom, GDCM, SimpleITK | `DICOM_reencoder/cli.py`, `DICOM_reencoder/commands/` |
| `rust/` | Rust backend with dicom-rs stack | `src/main.rs`, `src/cli/`, `src/web/` |
| `cpp/` | C++ backend with DCMTK, GDCM, ITK, VTK | `DicomTools.cpp`, `modules/` |
| `cs/` | C# backend with fo-dicom (.NET 8) | `DicomTools.Cli/Program.cs`, `DicomTools.Tests/` |
| `java/dcm4che-tests/` | Java backend with dcm4che3 | `src/main/java/com/dicomtools/cli/DicomToolsCli.java` |
| `js/viewer-gateway/` | Web viewer with Cornerstone3D | `src/main.ts`, `src/viewerGateway.ts` |
| `js/contract-cli/` | Node.js contract shim | `index.js` (delegates to Python) |
| `interface/` | Unified UI and adapter layer | `app.py`, `contract_runner.py`, `adapters/` |
| `sample_series/` | Shared DICOM test files | `IM-0001-0001.dcm` through `IM-0001-0190.dcm` |
| `scripts/` | Build and setup automation | `setup_all.sh`, `package_all.sh` |

**Sources:** [README.md L15-L22](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/README.md#L15-L22)

 [BUILD.md L1-L48](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/BUILD.md#L1-L48)

## Core Architecture Concepts

### CLI Contract System

The CLI contract is the central abstraction that enables cross-language interoperability. It defines a standardized JSON request/response format that all backends must implement.

```mermaid
flowchart TD

RequestFormat["Request Format {op, input, output, options}"]
ResponseFormat["Response Format {ok, returncode, output_files, metadata}"]
Operations["Canonical Operations info, anonymize, validate, etc."]
TkAppPy["interface/app.py TkApp class"]
ContractRunnerPy["interface/contract_runner.py main()"]
GetAdapter["interface/adapters/init.py get_adapter()"]
PythonAdapter["interface/adapters/python_adapter.py PythonCliAdapter"]
RustAdapter["interface/adapters/rust_adapter.py RustCliAdapter"]
CppAdapter["interface/adapters/cpp_adapter.py CppCliAdapter"]
CSharpAdapter["interface/adapters/csharp_adapter.py CSharpCliAdapter"]
JavaAdapter["interface/adapters/java_adapter.py JavaCliAdapter"]
JsAdapter["interface/adapters/js_adapter.py JsCliAdapter"]
PyCLI["python -m DICOM_reencoder.cli"]
RustCLI["rust/target/release/dicom-tools"]
CppCLI["cpp/build/DicomTools"]
CSharpCLI["dotnet DicomTools.Cli.dll"]
JavaCLI["java -jar dcm4che-tests.jar"]
JsCLI["node js/contract-cli/index.js"]

TkAppPy -.->|"Defines"| GetAdapter
ContractRunnerPy -.-> GetAdapter
PythonAdapter -.->|"handle(request)"| PyCLI
RustAdapter -.->|"handle(request)"| RustCLI
CppAdapter -.-> CppCLI
CSharpAdapter -.-> CSharpCLI
JavaAdapter -.-> JavaCLI
JsAdapter -.-> JsCLI
RequestFormat -.-> GetAdapter
ResponseFormat -.-> PythonAdapter

subgraph BackendCLIs ["Backend CLIs"]
    PyCLI
    RustCLI
    CppCLI
    CSharpCLI
    JavaCLI
    JsCLI
end

subgraph AdapterLayer ["Adapter Layer"]
    GetAdapter
    PythonAdapter
    RustAdapter
    CppAdapter
    CSharpAdapter
    JavaAdapter
    JsAdapter
    GetAdapter -.->|"Parsed by"| PythonAdapter
    GetAdapter -.->|"handle(request)"| RustAdapter
    GetAdapter -.->|"handle(request)"| CppAdapter
    GetAdapter -.->|"handle(request)"| CSharpAdapter
    GetAdapter -.->|"handle(request)"| JavaAdapter
    GetAdapter -.-> JsAdapter
end

subgraph UserLayer ["User Layer"]
    TkAppPy
    ContractRunnerPy
end

subgraph ContractSpec ["interface/CONTRACT.md"]
    RequestFormat
    ResponseFormat
    Operations
end
```

The contract defines operations like `info`, `anonymize`, `validate`, `transcode`, `to_image`, `echo`, `store_scu`, and many others. Each backend CLI receives JSON-formatted requests and returns JSON responses conforming to the specification.

For complete contract details, see [CLI Contract System](#3) and [Contract Specification](#3.1).

**Sources:** [README.md L41-L42](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/README.md#L41-L42)

 [BUILD.md L34-L41](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/BUILD.md#L34-L41)

### Adapter Pattern Implementation

The adapter pattern isolates user interfaces from backend-specific CLI invocations. Each adapter translates generic contract requests into language-specific command-line arguments.

```mermaid
sequenceDiagram
  participant p1 as User
  participant p2 as interface/app.py TkApp._handle_run()
  participant p3 as get_adapter(backend)
  participant p4 as RustCliAdapter
  participant p5 as rust/target/release/ dicom-tools

  p1->>p2: "Select backend='rust' op='info' input='sample.dcm'"
  p2->>p2: "_require_input() _normalize_output()"
  p2->>p3: "get_adapter('rust')"
  p3-->>p2: "RustCliAdapter instance"
  p2->>p4: "handle(request_dict)"
  p4->>p4: "_build_cmd() Translate to CLI args"
  p4->>p5: "subprocess.run([   'dicom-tools' |   'info' |   'sample.dcm' ])"
  p5-->>p4: "stdout, stderr, returncode"
  p4->>p4: "parse_json_maybe(stdout)"
  p4-->>p2: "RunResult{   ok=True,   output_files=[...],   metadata={...} }"
  p2->>p2: "_render_result()"
  p2-->>p1: "Display results in GUI"
```

Each adapter class implements a `handle(request: dict) -> RunResult` method and manages environment variable resolution for CLI paths.

For adapter implementation details, see [Adapter Pattern](#3.2).

**Sources:** [README.md L22](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/README.md#L22-L22)

 [BUILD.md L34-L41](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/BUILD.md#L34-L41)

## Language Backend Capabilities

The following table summarizes the capabilities and unique strengths of each language backend:

| Backend | Primary Libraries | CLI Commands | Unique Capabilities | Build Output |
| --- | --- | --- | --- | --- |
| **Python** | pydicom, pynetdicom, GDCM, SimpleITK, dicom-numpy | 20+ | Most comprehensive, network operations (echo/query/retrieve), NIfTI export, batch processing | Editable install via pip |
| **Rust** | dicom-rs | 15+ | JSON round-trip, web server mode, modern async networking, histogram analysis | `rust/target/release/dicom-tools` |
| **C++** | DCMTK, GDCM, ITK, VTK | 12+ | Advanced visualization (MPR, volume rendering), SR/RT support, VTK integration | `cpp/build/DicomTools` |
| **C#** | fo-dicom | 10+ | .NET ecosystem, DICOMweb (QIDO/STOW/WADO), network services, xUnit test suite | `cs/bin/Release/net8.0/DicomTools.Cli.dll` |
| **Java** | dcm4che3 | 9+ | Enterprise Java, Maven integration, DICOM conformance testing | `java/dcm4che-tests/target/dcm4che-tests.jar` |
| **JavaScript** | contract-cli shim → Python | Delegates to Python | Node.js compatibility, web viewer (Cornerstone3D), browser-based visualization | `js/contract-cli/index.js` |

### Operation Support Matrix

| Operation | Python | Rust | C++ | C# | Java | JS |
| --- | --- | --- | --- | --- | --- | --- |
| `info` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (via Python) |
| `anonymize` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (via Python) |
| `validate` | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ (via Python) |
| `transcode` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (via Python) |
| `to_image` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (via Python) |
| `volume`/`nifti` | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ |
| `echo` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| `store_scu` | ✓ | ✗ | ✗ | ✓ | ✓ | ✗ |
| `qido`/`stow`/`wado` | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ |
| VTK operations | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ |
| Web server | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |

For detailed information on each backend, see [Language Implementations](#4).

**Sources:** [README.md L7-L22](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/README.md#L7-L22)

## Key Components

### User Interfaces

Dicom-Tools provides three primary user interfaces:

1. **TkApp Desktop GUI** (`interface/app.py`) - Tkinter-based graphical interface for interactive DICOM processing. Provides backend selection, operation configuration, and result visualization. See [TkApp Desktop GUI](#2.1).
2. **Contract Runner** (`interface/contract_runner.py`) - Headless command-line executor for automated, scriptable DICOM processing. Accepts JSON request files or command-line arguments. See [Contract Runner (Headless CLI)](#2.2).
3. **Web Viewer** (`js/viewer-gateway/`) - Browser-based medical image viewer built on Cornerstone3D. Supports 2D stack viewing, 3D volume rendering, and DICOMweb integration. See [Web Viewer (JavaScript)](#2.3).

**Sources:** [README.md L22](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/README.md#L22-L22)

### Build System

The `scripts/setup_all.sh` script provides one-command setup for all language backends:

```mermaid
flowchart TD

SetupScript["scripts/setup_all.sh"]
Python["Python editable install pip install -e python"]
Rust["Rust release build cargo build --release"]
Cpp["C++ CMake build cmake -B cpp/build && cmake --build"]
CSharp["C# solution build dotnet build DicomTools.sln"]
Java["Java Maven package mvn package (skip tests)"]
JS["JS deps install npm ci (viewer-gateway)"]
PyPkg["Python package (installed in venv)"]
RustBin["rust/target/release/ dicom-tools"]
CppBin["cpp/build/ DicomTools"]
CSharpBin["cs/bin/Release/net8.0/ DicomTools.Cli.dll"]
JavaJar["java/dcm4che-tests/target/ dcm4che-tests.jar"]
JSNode["js/viewer-gateway/ node_modules/"]

SetupScript -.-> Python
SetupScript -.-> Rust
SetupScript -.-> Cpp
SetupScript -.-> CSharp
SetupScript -.-> Java
SetupScript -.-> JS
Python -.-> PyPkg
Rust -.-> RustBin
Cpp -.-> CppBin
CSharp -.-> CSharpBin
Java -.-> JavaJar
JS -.-> JSNode

subgraph Artifacts ["Build Artifacts"]
    PyPkg
    RustBin
    CppBin
    CSharpBin
    JavaJar
    JSNode
end

subgraph BuildSteps ["Build Steps"]
    Python
    Rust
    Cpp
    CSharp
    Java
    JS
end
```

Environment variables can override default CLI paths:

* `PYTHON_DICOM_TOOLS_CMD` - Python CLI path
* `RUST_DICOM_TOOLS_BIN` - Rust binary path
* `CPP_DICOM_TOOLS_BIN` - C++ binary path
* `CS_DICOM_TOOLS_CMD` - C# CLI command
* `JAVA_DICOM_TOOLS_CMD` - Java CLI command
* `JS_DICOM_TOOLS_CMD` - JavaScript CLI path
* `BACKING_CMD` - Backend command for JS contract-cli shim

For complete build system details, see [Build System](#8.1).

**Sources:** [scripts/setup_all.sh L1-L60](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/scripts/setup_all.sh#L1-L60)

 [BUILD.md L1-L48](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/BUILD.md#L1-L48)

### Testing Infrastructure

Testing follows a two-tier strategy:

1. **Language-specific tests** - Unit and integration tests within each backend directory using language-native frameworks (pytest, cargo test, ctest, xUnit, JUnit, Vitest)
2. **Interface/contract tests** - Cross-language integration tests in `interface/tests/` that validate contract compliance and ensure all backends produce equivalent results

```mermaid
flowchart TD

Trigger["Push/PR Events"]
PytestPy["pytest python/tests/"]
CargoTest["cargo test rust/"]
Ctest["ctest cpp/tests/"]
XUnit["dotnet test cs/DicomTools.Tests/"]
JUnit["mvn test java/dcm4che-tests/"]
Vitest["npm test js/viewer-gateway/"]
ContractTests["test_adapters.py test_contract_compliance.py"]
SampleData["sample_series/ Shared test DICOM files"]

Trigger -.->|"Validates"| PytestPy
Trigger -.->|"Validates"| CargoTest
Trigger -.->|"Validates"| Ctest
Trigger -.->|"Validates"| XUnit
Trigger -.->|"Validates"| JUnit
Trigger -.-> Vitest
Trigger -.-> ContractTests
PytestPy -.-> SampleData
CargoTest -.-> SampleData
Ctest -.-> SampleData
XUnit -.-> SampleData
JUnit -.-> SampleData
ContractTests -.-> SampleData
ContractTests -.-> PytestPy
ContractTests -.-> CargoTest
ContractTests -.-> Ctest
ContractTests -.-> XUnit
ContractTests -.-> JUnit

subgraph InterfaceTests ["interface/tests/"]
    ContractTests
end

subgraph LangTests ["Language-Specific Tests"]
    PytestPy
    CargoTest
    Ctest
    XUnit
    JUnit
    Vitest
end

subgraph CI ["CI Pipeline .github/workflows/ci.yml"]
    Trigger
end
```

All tests use the shared `sample_series/` directory for consistent test data across languages.

For detailed testing information, see [Testing](#7) and [Testing Strategy](#7.1).

**Sources:** [README.md L32-L40](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/README.md#L32-L40)

 [BUILD.md L24-L32](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/BUILD.md#L24-L32)

## Getting Started

### Prerequisites

To use Dicom-Tools, you need:

* Python 3.10+ with pip
* Rust stable (1.75+) with cargo
* CMake ≥3.15 and C++17 compiler
* .NET SDK 8.0+
* JDK 17+ and Maven
* Node.js 18+

### Quick Setup

```
# Clone repositorygit clone https://github.com/ThalesMMS/Dicom-Tools.gitcd Dicom-Tools# One-command setup (builds all backends)./scripts/setup_all.sh# Launch GUIpython -m interface.app# Or use headless contract runnerpython -m interface.contract_runner --backend python --op info --input sample_series/IM-0001-0001.dcm
```

For detailed setup instructions, see [Installation and Setup](#1.2). For usage examples, see [Quick Start Guide](#1.3).

**Sources:** [README.md L27-L31](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/README.md#L27-L31)

 [scripts/setup_all.sh L1-L60](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/scripts/setup_all.sh#L1-L60)

 [BUILD.md L1-L48](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/BUILD.md#L1-L48)

Refresh this wiki

Last indexed: 5 January 2026 ([c7b4cb](https://github.com/ThalesMMS/Dicom-Tools/commit/c7b4cbd8))

### On this page

* [Overview](#1-overview)
* [Purpose and Scope](#1-purpose-and-scope)
* [Repository Structure](#1-repository-structure)
* [Directory Layout](#1-directory-layout)
* [Core Architecture Concepts](#1-core-architecture-concepts)
* [CLI Contract System](#1-cli-contract-system)
* [Adapter Pattern Implementation](#1-adapter-pattern-implementation)
* [Language Backend Capabilities](#1-language-backend-capabilities)
* [Operation Support Matrix](#1-operation-support-matrix)
* [Key Components](#1-key-components)
* [User Interfaces](#1-user-interfaces)
* [Build System](#1-build-system)
* [Testing Infrastructure](#1-testing-infrastructure)
* [Getting Started](#1-getting-started)
* [Prerequisites](#1-prerequisites)
* [Quick Setup](#1-quick-setup)

Ask Devin about Dicom-Tools