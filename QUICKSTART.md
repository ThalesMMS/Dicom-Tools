# Quickstart — Dicom-Tools

## 1) Clone and prerequisites
- Tools: `python3`/`pip`, `cargo`, `cmake`, `.NET SDK 8+ (dotnet)`, `mvn`, `npm`, C++17 toolchain.
- Clone: `git clone https://github.com/ThalesMMS/Dicom-Tools.git && cd Dicom-Tools`
- Sample data: `sample_series/` should be present (included in the repo).

## 2) One-shot setup
```bash
./scripts/setup_all.sh
```
Uses default Release builds (set `BUILD_TYPE=Debug` for C++) and links `sample_series` into `cpp/input` if missing.

## 3) Smoke tests (quick)
```bash
python3 -m pytest interface/tests               # contract + UI layer
python3 cpp/tests/run_all.py                    # C++ suite (after build)
```

## 4) Run a sample command per backend
- Python: `python -m DICOM_reencoder.cli summary sample_series/IM-0001-0001.dcm --json`
- Rust: `rust/target/release/dicom-tools info sample_series/IM-0001-0001.dcm`
- C++: `cpp/build/DicomTools --modules`
- C#: `dotnet cs/DicomTools.Cli/bin/Debug/net8.0/DicomTools.Cli.dll --help`
- Java: `java -jar java/dcm4che-tests/target/dcm4che-tests.jar --op info --input sample_series/IM-0001-0001.dcm`
- JS shim: `node js/contract-cli/index.js --op info --input sample_series/IM-0001-0001.dcm --options "{}"`

## 5) Full test suites (per language)
- Python: `cd python && pytest -q`
- Rust: `cd rust && cargo test`
- C++: `ctest` from `cpp/build` (or `python3 cpp/tests/run_all.py`)
- C#: `dotnet test cs/DicomTools.Tests/DicomTools.Tests.csproj`
- Java: `cd java/dcm4che-tests && mvn test`
- JS: `cd js/viewer-gateway && npm test`
- Interface: `cd interface && pytest`

## 6) UI
- Tkinter UI: `python -m interface.app`
- Headless runner: `python -m interface.contract_runner --backend python --op info --input sample_series/IM-0001-0001.dcm`
