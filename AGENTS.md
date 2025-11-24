# Repository Guidelines

## Project Structure & Modules
- `python/`: DICOM toolkit & CLI (`DICOM_reencoder`), tests in `python/tests/`.
- `cpp/`: C++ CLI/tests (GDCM, DCMTK, ITK, VTK); build in `cpp/build/`.
- `rust/`: Rust CLI/web (`dicom-tools`); tests in `rust/tests/`.
- `interface/`: Tkinter UI + contract adapters (CLI/JSON).
- `cs/`: fo-dicom CLI/tests.
- `java/`: dcm4chee CLI/tests.
- `js/`: Cornerstone integration notes (no repo cloned).
- `sample_series/`: DICOM samples for local tests.
- `scripts/`: setup/package helpers (`setup_all.sh`, `package_all.sh`).
- `plano.md`, `STRUCTURE.md`: planning/layout docs.

## Build, Test, Development
- Python: `pip install -r python/requirements-dev.txt && pip install -e python && cd python && pytest`.
- Rust: `cd rust && cargo test`.
- C++: `cd cpp && mkdir -p build && cd build && cmake -DCMAKE_BUILD_TYPE=Release .. && cmake --build . && ctest`.
- Interface: `cd interface && pytest`; UI: `python -m interface.app`.
- Java: `cd java/dcm4che-tests && mvn test`.
- C#: `cd cs && dotnet test`.
- JS: no workspace; use npm/nx scripts when added.
- One-shot setup: `./scripts/setup_all.sh`; packaging: `./scripts/package_all.sh`.
- CI: `.github/workflows/ci.yml` runs Python/Rust/Java/C# tests.

## Coding Style & Naming
- Python: PEP 8, type hints; keep CLI flags consistent with `CONTRACT.md`.
- Rust: Rust 2021; run `cargo fmt` and `cargo clippy --all-targets --all-features`.
- C++: C++17; follow module naming (`gdcm:`, `dcmtk:`, `itk:`, `vtk:`).
- C#: .NET conventions; PascalCase for public types/members.
- Java: standard Maven/Gradle conventions.
- JS: follow project scripts when added.
- Modularization: keep logic small and reusable; provide clear adapter/interfaces for new backends.
- Cross-project communication: changes to contract/ops/options must sync `interface/CONTRACT.md`, adapters, CLIs, and tests.

## Testing Guidelines
- Prioritize deterministic tests using `sample_series`.
- Backend suites: Python `pytest`; Rust `cargo test`; C++ `ctest` or `python cpp/tests/run_all.py`; Interface `pytest`; Java `mvn test`; C# `dotnet test`.
- Contract tests: `interface/tests/test_contract_runner.py` (backends required).
- Add JSON/CLI coverage when adding operations.

## Commit & PR Guidelines
- Small, descriptive commits (e.g., `interface: add csharp adapter json mapping`).
- PRs: explain what/why/how to test; link issues; screenshots/gifs only for UI changes.
- Respect non-owned workspaces: coordinate before touching shared planning docs or external integrations.
