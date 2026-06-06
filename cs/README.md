# Dicom-Tools (C# / fo-dicom)

.NET 8 CLI and tests built with fo-dicom and ImageSharp.

## Structure
- `DicomTools.Cli/` — fo-dicom CLI (`DicomTools.Cli.dll`).
- `DicomTools.Tests/` — xUnit suite covering networking (C-STORE/C-FIND/C-MOVE), codecs, imaging/window-level/LUT, and multi-frame cases.
- `sample_series/` (repo root) — DICOM series used in tests.
- `package_cli.sh` — CLI binary packager.

## Prerequisites
- .NET SDK 8 (or newer with `DOTNET_ROLL_FORWARD=Major`).
- The `sample_series/` folder must be reachable from the base directory used by the tests/CLI.

## Build
```bash
dotnet build DicomTools.sln
# or only the CLI
dotnet build DicomTools.Cli/DicomTools.Cli.csproj
```

## Tests
```bash
# if only .NET 10 is installed:
DOTNET_ROLL_FORWARD=Major dotnet test DicomTools.Tests/DicomTools.Tests.csproj
# with .NET 8 available:
dotnet test DicomTools.Tests/DicomTools.Tests.csproj
# line coverage (coverlet.msbuild):
DOTNET_ROLL_FORWARD=Major dotnet test DicomTools.Tests/DicomTools.Tests.csproj \\
  /p:CollectCoverage=true \\
  /p:CoverletOutputFormat=cobertura \\
  /p:CoverletOutput=coverage.cobertura.xml \\
  /p:Include="[DicomTools*]*" /p:Exclude="[xunit.*]*"
# latest run: ~93% line / ~69% branch coverage in the CLI (see `DicomTools.Tests/coverage.cobertura.xml`).
```
Recent coverage includes:
- In-memory SCPs for C-STORE/C-FIND/C-MOVE and Modality Worklist (SCU↔SCP).
- Validation of color multi-frame (RGB) round-trip compression (RLE) while preserving pixels/frames.
- A stub DICOMweb STOW→DIMSE bridge to validate HTTP ingestion and C-MOVE retrieval.

## CLI
```bash
dotnet cs/bin/Debug/net8.0/DicomTools.Cli.dll --help
```
Supported operations:
- `info <input> [--json]`
- `anonymize <input> --output <path>`
- `to-image <input> --output <path> [--frame N] [--format png|jpeg]`
- `transcode <input> --output <path> --transfer-syntax <syntax>`
- `validate <input>`
- `echo <host:port>`
- `dump <input> [--depth N] [--max-value-length N]`
- `stats <input> [--frame N] [--json]`
- `histogram <input> [--bins N] [--frame N] [--json]`

## Notes
- Networking tests use in-memory SCPs and free ports, so run them in a local environment (without firewalls blocking loopback).
- Advanced codec coverage tries RLE/JPEG2000/JPEG-LS, and the tests return without failure when those codecs are unavailable.
- The CLI code is split into smaller commands/helpers (for example `InfoCommand`, `StatsCommand`) to keep files under 500 lines.
