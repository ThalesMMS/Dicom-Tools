# Repository Structure

- `cpp/`: C++ CLI and modules (GDCM, DCMTK, ITK, VTK). Build: `cpp/build/DicomTools`.
- `rust/`: Rust CLI/web (`dicom-tools`). Build: `rust/target/release/dicom-tools`.
- `python/`: Python toolkit (`DICOM_reencoder`), CLI `python -m DICOM_reencoder.cli`.
- `interface/`: Tkinter UI and contract adapters (CLI/JSON).
- `cs/`: fo-dicom CLI/tests.
- `java/`: dcm4chee tests/CLI.
- `js/`: Cornerstone integration (`viewer-gateway`) and contract CLI shim (`contract-cli`).
- `sample_series/`: DICOM samples for tests.
- `plano.md`: Integration plan with status.
- `scripts/`: setup/package utilities.
