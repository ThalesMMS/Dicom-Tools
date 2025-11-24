# Build & Tooling Guide

## General Requirements
- Python 3.10+ with `pip`
- Rust stable (1.75+)
- CMake ≥3.15 and C++17 compiler
- .NET SDK 8.0 (tests can roll forward with `DOTNET_ROLL_FORWARD=Major` if only .NET 10 is installed)
- JDK 17 and Maven (downloads dcm4che artifacts from `https://www.dcm4che.org/maven2`)

## Core Commands
- `make python-install` — install Python toolkit editable
- `make python-test` — run Python tests
- `make rust-build` — build Rust release
- `make rust-test` — `cargo test`
- `make cpp-build` — CMake build for `cpp/`
- `make cpp-test` — `ctest` (if configured)
- `make interface-run` — launch Tkinter UI
- `make all` — python-install + rust-build + cpp-build

Helpers:
- Setup: `./scripts/setup_all.sh` (Python editable + Rust/C++ build + symlink `cpp/input -> sample_series`)
- Packaging: `./scripts/package_all.sh` (wheel/sdist + Rust/C++ binaries copied to `artifacts/`)

## Tests (by project)
- Python: `pip install -r python/requirements-dev.txt && pip install -e python && cd python && pytest`
- Rust: `cd rust && cargo test`
- C++: `cd cpp && mkdir -p build && cd build && cmake -DCMAKE_BUILD_TYPE=Release .. && cmake --build . && ctest`
- Interface: `cd interface && pytest`
- Java: `cd java/dcm4che-tests && mvn test`
- C#: `cd cs && dotnet test` (or `DOTNET_ROLL_FORWARD=Major dotnet test` if .NET 8 runtime is missing)
- JS: no workspace cloned; use npm/nx scripts when present

## Contract & Env Vars
- Python CLI: `python -m DICOM_reencoder.cli` (cwd `python/`)
- Rust binary: `rust/target/release/dicom-tools` (fallback `cargo run --release --`)
- C++ binary: `cpp/build/DicomTools`
- Java CLI jar: `java/dcm4che-tests/target/dcm4che-tests.jar` (`JAVA_DICOM_TOOLS_CMD` to override)
- C# CLI: `cs/bin/(Release|Debug)/net8.0/DicomTools.Cli` (`CS_DICOM_TOOLS_CMD` to override)

## Artifacts & Outputs
- Defaults: write to `output/` (backend-specific) when not provided
- Cleaning: remove build/output dirs before release; see `.gitignore`

## CI
- GitHub Actions: `.github/workflows/ci.yml` runs Python, Rust, Java, C#, C++ (configure+build), and JS (build + vitest). Interface/UI not yet automated; add once headless coverage is available.
