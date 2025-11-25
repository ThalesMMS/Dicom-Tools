# DICOM Tools (Rust)

A robust command-line interface (CLI) and web utility for processing DICOM medical imaging files. Built with Rust, it leverages the `dicom-rs` ecosystem for core operations, offering high performance, type safety, and modern tooling integration.

## Project Overview

This project provides a suite of tools to:
- **Inspect:** Extract and view DICOM metadata tags in detail.
- **Anonymize:** Smart redaction of Patient Information (PII) based on Value Representations (VR). Automatically masks Names (`PN`), Dates (`DA`), and Times (`TM`) while hashing `PatientID`.
- **Convert:** Transform DICOM pixel data into standard image formats (PNG/JPG). Fully supports **multi-frame** images (videos/volumes) by extracting all frames.
- **Window/Level:** Override or normalize VOI LUTs, force 8-bit/16-bit output, and target a specific frame when exporting images. Per-frame VOI from functional groups is preserved so multi-frame series render correctly.
- **JSON:** Bi-directional conversion between DICOM files and DICOM JSON representations for interoperability.
- **Structured Data:** Navigate nested sequences (SR-like) via path segments to read deep content safely.
- **Validate:** Deep inspection of DICOM files, checking for critical attributes (SOP Class, Patient Info, Pixel Data) and standard compliance.
- **Transcode:** Re-encode to uncompressed syntaxes (Explicit/Implicit VR Little Endian) while keeping pixel data intact.
- **Histogram & Pixel Format:** Generate intensity histograms and summarize pixel layout (bits, samples per pixel, photometric interpretation, rescale/window info).
- **Networking (Experimental):** Basic DICOM SCU capabilities (`echo`, `push`, simple `find`) with pending/final C-FIND response handling for quick PACS checks.
- **Serve:** A lightweight web server (`Axum`) for demonstrating these capabilities via a browser.
- **Dataset Dump:** Print every element with dictionary names, sequence items, and encapsulated pixel data summaries.

### Newer capabilities
- Per-frame functional group parsing (positions, orientations, pixel spacing) with affine reconstruction.
- Lazy frame reads to avoid loading entire multi-frame pixel data into memory.
- Deep SR/structured navigation helper for sequence-heavy datasets.
- In-memory fake C-FIND workflow covered by integration tests.

### Key Technologies
- **Language:** Rust (Edition 2021)
- **CLI:** `clap` (v4)
- **DICOM:** `dicom-rs` ecosystem (`dicom-core`, `dicom-object`, `dicom-pixeldata`, `dicom-ul`, `dicom-json`)
- **Web:** `axum` (v0.7), `tokio` (v1)
- **Concurrency:** `rayon` (v1.8)

## Architecture

The project is structured as a single binary with modularized functionality:

- **`src/main.rs`**: Application entry point and CLI dispatch.
- **`src/anonymize.rs`**: Generic VR-based anonymization logic.
- **`src/image.rs`**: Pixel data extraction and multi-frame image conversion.
- **`src/dump.rs`**: Dataset walker used by the `dump` CLI command.
- **`src/json.rs`**: DICOM <-> JSON conversion utilities.
- **`src/validate.rs`**: Deep validation of DICOM attributes and structure.
- **`src/scu.rs`**: Experimental DICOM networking (C-ECHO, C-STORE).
- **`src/web.rs`**: Axum web server implementation.
- **`src/batch.rs`**: Parallel directory processing.
- **`src/metadata.rs`**: Metadata extraction utilities.
- **`src/stats.rs`**: Pixel statistics helpers used by CLI and web.
- **`src/storage.rs`**: Sandboxed upload store for the web UI.
- **`src/templates/index.html`**: Single-page UI for uploads, previews, JSON/metadata views.

## Building and Running

### Prerequisites
- **Rust Toolchain:** Stable Rust version installed (1.75+ recommended).

### Development Commands

| Action | Command | Description |
| :--- | :--- | :--- |
| **Build** | `cargo build` | Compiles the project in debug mode. |
| **Check** | `cargo check` | Fast compilation check. |
| **Test** | `cargo test` | Runs unit and integration tests. |
| **Format** | `cargo fmt --all` | Formats code to Rust standards. |
| **Lint** | `cargo clippy --all-targets --all-features` | Runs the linter. |

### Usage Examples

**CLI Mode:**

```bash
# Extract metadata
cargo run -- info path/to/image.dcm --verbose

# Anonymize a file (Smart VR-based)
cargo run -- anonymize path/to/image.dcm --output output/clean.dcm

# Convert to PNG (Extracts all frames for multi-frame files)
cargo run -- to-image path/to/image.dcm --format png

# Convert a single frame with a custom window/level and force 16-bit output
cargo run -- to-image path/to/image.dcm --frame 2 --window-center -600 --window-width 1600 --force-16bit

# Convert to JSON
cargo run -- to-json path/to/image.dcm --output metadata.json

# Create DICOM from JSON
cargo run -- from-json metadata.json --output restored.dcm

# Validate a file (Deep check)
cargo run -- validate path/to/image.dcm

# Transcode to implicit VR little endian
cargo run -- transcode path/to/image.dcm --output output/clean.dcm --transfer-syntax implicit-vr-little-endian

# Print full dataset with dictionary names
cargo run -- dump path/to/image.dcm --max-depth 3

# Generate an intensity histogram (256 bins by default)
cargo run -- histogram path/to/image.dcm --bins 128

# Network Echo (Experimental)
cargo run -- echo 127.0.0.1:104

# Batch anonymize a directory
cargo run -- batch --directory ./data/patients --operation anonymize
```

**Web Mode:**

```bash
# Start the server on localhost:3000
cargo run -- web --host 127.0.0.1 --port 3000
```

## Development Conventions

- **Code Style:** Adhere strictly to `rustfmt` and `clippy` defaults.
- **Error Handling:** Use `anyhow` for top-level error reporting.
- **Safety:** Do not commit real Protected Health Information (PHI). Use synthetic or anonymized DICOM data for testing.

## Release Packaging

- Release profile enforces `codegen-units = 1` and disables incremental builds for reproducibility.
- Build release binary with locked dependencies: `cargo build --release --locked`.
- For deterministic outputs, set `SOURCE_DATE_EPOCH` and disable incremental builds: `CARGO_PROFILE_RELEASE_INCREMENTAL=false cargo build --release --locked`.
- Optionally strip symbols after the build to shrink the artifact: `strip target/release/dicom-tools` (or `llvm-strip` on macOS).
- Package the binary with a normalized timestamp to keep archives reproducible: `tar --owner=0 --group=0 --mtime="@${SOURCE_DATE_EPOCH:-$(date +%s)}" -czf dicom-tools-${VERSION:-local}-$(uname -m).tar.gz -C target/release dicom-tools`.
