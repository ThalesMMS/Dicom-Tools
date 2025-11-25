# Dicom-Tools (multi-language toolkit)

Unified DICOM toolkit with CLIs and utilities implemented in Python, Rust, C++, C#, Java, and JS, plus a shared UI and contract runner. Each folder hosts its own backend; `sample_series/` in the repo root provides the reference datasets used across tests and demos.

## Libraries Covered
- C++: DCMTK, GDCM, ITK, VTK
- Python: pydicom, pynetdicom, python-gdcm, SimpleITK, dicom-numpy
- Rust: dicom-rs stack
- C#: fo-dicom
- Java: dcm4che (dcm4che3)
- JS: Cornerstone3D (gateway) + Node contract shim

## Module Overview
- **python/** — 20+ CLI commands (info, anonymize, to-image, validate, transcode, volume/NIfTI, PACS echo/query/retrieve). Install: `pip install -e python` (or `pip install -r python/requirements.txt`). Tests: `cd python && pytest -q`. Optional extras: `gdcm`, `SimpleITK`, `dicom-numpy`.
- **rust/** — CLI/Web built on `dicom-rs` (inspect, anonymize, multi-frame to-image, JSON round-trip, validate, transcode, histogram, dump, experimental echo/push/find). Commands: `cargo build`, `cargo test`, `cargo fmt --all`, `cargo clippy --all-targets --all-features`. Examples: `cargo run -- info file.dcm`, `cargo run -- to-image file.dcm --format png`, `cargo run -- web --host 127.0.0.1 --port 3000`.
- **cpp/** — `DicomTools` executable with GDCM/DCMTK/ITK/VTK modules (anonymize, J2K/RLE/JPEG-LS transcode, dump, stats, MPR, volume rendering, NIfTI/NRRD, SR/RT). Prereqs: CMake 3.15+, C++17 compiler; optional `./scripts/build_deps.sh` to build DCMTK/GDCM/ITK/VTK locally. Build: `cmake -S . -B build && cmake --build build`. Usage: `./build/DicomTools --modules`, `./build/DicomTools all -i input/dcm_series/IM-0001-0190.dcm -o output`. Tests: `python3 tests/run_all.py`.
- **cs/** — fo-dicom CLI (.NET 8) with info/anonymize/to-image/transcode/validate/echo/dump/stats/histogram; xUnit tests cover networking and codecs. Build: `dotnet build DicomTools.sln` (or only `DicomTools.Cli`). Tests: `dotnet test cs/DicomTools.Tests/DicomTools.Tests.csproj` (set `DOTNET_ROLL_FORWARD=Major` if only .NET 10 is installed). CLI: `dotnet cs/bin/Debug/net8.0/DicomTools.Cli.dll --help`.
- **java/** — `dcm4che-tests` (Java 17, Maven) with CLI and JUnit suite (info, anonymize, to_image, transcode, validate, dump, stats, echo). Commands: `cd java/dcm4che-tests && mvn test` or `mvn package` to create `target/dcm4che-tests.jar` (main `com.dicomtools.cli.DicomToolsCli`). Example: `java -jar dcm4che-tests/target/dcm4che-tests.jar --op info --input ../../sample_series/IM-0001-0001.dcm`.
- **js/** — JS layer with `viewer-gateway/` (Vite + Cornerstone3D, Vitest) and `contract-cli/` (Node shim for the contract; defaults to the Python backend). Prereq: Node 18+. Commands: `cd js/viewer-gateway && npm install && npm run dev|build|test`. Contract CLI: `node js/contract-cli/index.js --op info --input sample_series/IM-0001-0001.dcm --options "{}"` (override `BACKING_CMD` to point elsewhere).
- **interface/** — Tkinter UI and headless contract executor; adapters target every backend. Launch UI: `python -m interface.app`. Headless: `python -m interface.contract_runner --backend python --op info --input sample_series/IM-0001-0001.dcm`. Tests: `cd interface && pytest`.

## Sample Data
- `sample_series/` contains the DICOM files used across tests and quickstarts. Most commands/tests assume paths relative to the repo root.

## One-shot Setup
- Script: `./scripts/setup_all.sh`
- Installs/Builds: Python editable install (with dev requirements), Rust release, C++ build (`cpp/build`), C# solution restore/build, Java Maven package, JS deps (`viewer-gateway`).
- Requires tools on PATH: `python3`, `pip`, `cargo`, `cmake`, `.NET SDK 8+ (dotnet)`, `mvn`, `npm`. Set `BUILD_TYPE=Debug` to change the C++ config.

## Test Shortcuts
- Python: `cd python && pytest -q`
- Rust: `cd rust && cargo test`
- C++: `python3 cpp/tests/run_all.py` (or `ctest` after configuring `cpp/build`)
- C#: `dotnet test cs/DicomTools.Tests/DicomTools.Tests.csproj`
- Java: `cd java/dcm4che-tests && mvn test`
- JS (viewer-gateway): `cd js/viewer-gateway && npm test`
- Interface: `cd interface && pytest`

## CLI Contract
All CLIs follow the shared contract in `interface/CONTRACT.md`. The Node shim (`js/contract-cli`) and the Tkinter adapters point to the corresponding binaries and can be redirected via environment variables.
