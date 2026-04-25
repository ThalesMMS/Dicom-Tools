# Interface Tests

This directory contains integration tests for the CLI/JSON contract. They require:
- `sample_series/` with a test DICOM file, such as `IM-0001-0147.dcm`.
- Built backends: `python -m DICOM_reencoder.cli`, `rust/target/release/dicom-tools` (or `cargo run --release --`), and `cpp/build/DicomTools`.

Run:
```bash
cd interface
pytest
```

Optional configuration:
- Override binaries with environment variables: `PYTHON_DICOM_TOOLS_CMD`, `RUST_DICOM_TOOLS_BIN`, `CPP_DICOM_TOOLS_BIN`.
