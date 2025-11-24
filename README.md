# Dicom-Tools Monorepo

Unified repository for DICOM utilities across multiple languages with a shared contract and a Tkinter UI. Backends: Python, C++, Rust, Java (dcm4chee), C# (fo-dicom); frontend integration planned with JS (Cornerstone).

## Layout
- `python/` — DICOM toolkit & CLI (`DICOM_reencoder`).
- `cpp/` — C++ CLI/tests (GDCM, DCMTK, ITK, VTK).
- `rust/` — Rust CLI/web (`dicom-tools`).
- `interface/` — Tkinter UI + contract adapters (CLI/JSON).
- `java/` — dcm4chee tests/CLI (contract integration pending).
- `cs/` — fo-dicom CLI/tests (contract adapter ready).
- `js/` — Cornerstone integration notes (no repo cloned).
- `sample_series/` — DICOM samples for tests.
- `scripts/` — setup/package helpers.

## Build & Test (short)
- Python: `pip install -r python/requirements-dev.txt && pip install -e python && cd python && pytest`
- Rust: `cd rust && cargo test`
- C++: `cd cpp && mkdir -p build && cd build && cmake -DCMAKE_BUILD_TYPE=Release .. && cmake --build . && ctest`
- Interface: `cd interface && pytest`
- Java: `cd java/dcm4che-tests && mvn test`
- C#: `cd cs && dotnet test`
- One-shot: `./scripts/setup_all.sh` (Python editable + Rust/C++ build)
- Packaging: `./scripts/package_all.sh` (artifacts to `artifacts/`)

## Contract & UI
- Contract spec: `interface/CONTRACT.md` (operations, envelopes, backend mapping).
- Adapters: `interface/adapters/*` (Python, Rust, C++, Java, C#).
- UI: `python -m interface.app` (Tkinter) uses the contract; headless runner: `python -m interface.contract_runner`.

## CI
- GitHub Actions workflow in `.github/workflows/ci.yml` runs Python, Rust, Java, C#, C++ (configure+build), and JS (build + vitest). Interface/UI still omitted from CI because of GUI deps; add when headless coverage is available.

## Notes
- Ignore build artifacts (bin/obj/target/output/node_modules/coverage/artifacts). See `.gitignore`.
- Java/C# CLIs are mapped in adapters; ensure env vars `JAVA_DICOM_TOOLS_CMD` / `CS_DICOM_TOOLS_CMD` point to the built jar/binary.***
- Java build downloads dcm4che artifacts from `https://www.dcm4che.org/maven2`.
- C# targets .NET 8; if only .NET 10 is installed locally, run tests with `DOTNET_ROLL_FORWARD=Major dotnet test`.
