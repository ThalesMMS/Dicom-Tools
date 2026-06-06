# Integration Contract (Option A – CLI/JSON)

Goal: provide a single interface (Tkinter) that calls each backend through command-line executables, exchanges JSON (or text) requests/responses, and keeps the same logical signature for C++, Python, Rust (today) and Java/C# (future).

## Request Envelope
```json
{
  "backend": "python | cpp | rust | java | csharp",
  "op": "info | anonymize | to_image | transcode | validate | echo | stats | dump | volume | nifti | split_multiframe | batch_list | batch_decompress | batch_anonymize | batch_convert | batch_validate | to_json | from_json | test_gdcm | test_dcmtk | test_itk | test_vtk_unit | test_utils | test_integration | test_edge_cases | test_validation | run_cpp_tests | test_uid | test_datetime | test_charset | test_workflow | test_validation_java | run_java_tests | test_anonymize_cs | test_uid_cs | test_datetime_cs | test_charset_cs | test_dictionary_cs | test_file_operations_cs | test_sequence_cs | test_value_representation_cs | test_option_parser_cs | test_stats_helpers_cs | run_cs_tests",
  "input": "/path/to/file_or_directory",
  "output": "/path/to/optional_output",
  "options": { "key": "value" }
}
```

## Response Envelope
```json
{
  "ok": true,
  "returncode": 0,
  "stdout": "process text",
  "stderr": "warnings/errors",
  "output_files": ["/list/of/generated/files"],
  "metadata": { "normalized_structure_or_none": "..." }
}
```

## Canonical Operations

| op | Description | Expected parameters | Expected outputs |
| --- | --- | --- | --- |
| info | Read basic metadata | `input`, `options.verbose?` | `metadata` + `stdout` |
| anonymize | Anonymize a file | `input`, `output?` | anonymized file in `output_files` |
| to_image | Export image/frame | `input`, `output`, `options.format? (png/jpeg)`, `options.frame?` | image in `output_files` |
| transcode | Change syntax/decode | `input`, `output`, `options.syntax` | transcoded DICOM in `output_files` |
| validate | Basic validation | `input` | `stdout` with result |
| echo | C-ECHO | `options.host`, `options.port` | `stdout` with status |
| stats | Pixel statistics/histogram | `input`, `options.bins?` | `stdout` (and `metadata` if the backend supports it) |
| dump | Full dataset dump | `input`, `options.depth?`, `options.max_value_len?`, `options.json?` | text or JSON in `stdout` |
| volume | Build 3D volume | `input` (directory), `output?`, `options.preview?` | `.npy` and metadata |
| nifti | Export series to NIfTI | `input` (directory), `output?`, `options.series_uid?` | `.nii/.nii.gz` + metadata |
| split_multiframe | Split multi-frame file into individual frames | `input` (file), `output?` (directory), `options.prefix?`, `options.frames?`, `options.info?` | multiple `.dcm` files or text info |
| batch_list | List DICOMs in a directory | `input` (directory), `options.recursive?` | `stdout` |
| batch_decompress | Decompress a DICOM series | `input` (directory), `output?` (directory), `options.recursive?` | decompressed files |
| batch_anonymize | Anonymize a DICOM series | `input` (directory), `output?` (directory), `options.recursive?` | anonymized files |
| batch_convert | Convert a series to images | `input` (directory), `output?` (directory), `options.format? (png/jpeg)`, `options.recursive?` | images |
| batch_validate | Validate a DICOM series | `input` (directory), `options.recursive?` | `stdout` with status |
| to_json | Export to DICOM JSON | `input`, `output?` | JSON in a file/`stdout` |
| from_json | Convert from DICOM JSON to DICOM | `input` (JSON), `output` (DICOM) | DICOM file |
| test_gdcm | Run the GDCM unit test binary (C++) | `input?` (ignored) | `stdout` with result |
| test_dcmtk | Run the DCMTK unit test binary (C++) | `input?` (ignored) | `stdout` with result |
| test_itk | Run the ITK unit test binary (C++) | `input?` (ignored) | `stdout` with result |
| test_vtk_unit | Run the VTK unit test binary (C++) | `input?` (ignored) | `stdout` with result |
| test_utils | Run the C++ utility test binary | `input?` (ignored) | `stdout` with result |
| test_integration | Run C++ integration tests (GDCM/DCMTK) | `input?` (ignored) | `stdout` |
| test_edge_cases | Run C++ edge case tests | `input?` (ignored) | `stdout` |
| test_validation | Run C++ validation tests | `input?` (ignored) | `stdout` |
| run_cpp_tests | Run all C++ tests (`run_cpp_tests` target) | `input?` (ignored) | `stdout` |
| test_uid | Run dcm4che UID tests (Java) | `input?` (ignored) | `stdout` |
| test_datetime | Run dcm4che date/time tests (Java) | `input?` (ignored) | `stdout` |
| test_charset | Run dcm4che charset tests (Java) | `input?` (ignored) | `stdout` |
| test_workflow | Run dcm4che workflow/end-to-end tests (Java) | `input?` (ignored) | `stdout` |
| test_validation_java | Run dcm4che validation tests (Java) | `input?` (ignored) | `stdout` |
| run_java_tests | Run all dcm4che Java tests | `input?` (ignored) | `stdout` |
| test_anonymize_cs | Run fo-dicom anonymization tests (C#) | `input?` (ignored) | `stdout` |
| test_uid_cs | Run fo-dicom UID tests (C#) | `input?` (ignored) | `stdout` |
| test_datetime_cs | Run fo-dicom date/time tests (C#) | `input?` (ignored) | `stdout` |
| test_charset_cs | Run fo-dicom charset tests (C#) | `input?` (ignored) | `stdout` |
| test_dictionary_cs | Run fo-dicom dictionary tests (C#) | `input?` (ignored) | `stdout` |
| test_file_operations_cs | Run fo-dicom file operation tests (C#) | `input?` (ignored) | `stdout` |
| test_sequence_cs | Run fo-dicom sequence tests (C#) | `input?` (ignored) | `stdout` |
| test_value_representation_cs | Run fo-dicom VR tests (C#) | `input?` (ignored) | `stdout` |
| test_option_parser_cs | Run fo-dicom option parsing tests (C#) | `input?` (ignored) | `stdout` |
| test_stats_helpers_cs | Run fo-dicom statistics helper tests (C#) | `input?` (ignored) | `stdout` |
| run_cs_tests | Run all fo-dicom C# tests | `input?` (ignored) | `stdout` |

## Mapping
- **Python** (`python -m DICOM_reencoder.cli`): `info -> summary --json`, `anonymize -> anonymize`, `to_image -> png`, `transcode -> transcode`, `validate -> python -m DICOM_reencoder.validate_dicom`, `echo -> dicom_echo`, `volume -> volume`, `nifti -> nifti`, `split_multiframe -> python -m DICOM_reencoder.split_multiframe`, batch helpers via `python -m DICOM_reencoder.batch_process -o {list|decompress|anonymize|convert|validate}`.
- **Rust** (`rust/target/release/dicom-tools` or `cargo run --release -- ...`): `info [--json]`, `anonymize`, `to_image` (`to-image`), `transcode`, `validate` (`validate`), `echo` (`echo`), `dump [--json]` (`dump`), `stats` (`stats`/`histogram`), `to_json` (`to-json`), `from_json` (`from-json`).
- **C++** (`cpp/build/DicomTools`): `info/dump -> gdcm:dump`, `anonymize -> gdcm:anonymize`, `to_image -> gdcm:preview`, `stats -> gdcm:stats`, `transcode -> gdcm:transcode-j2k|gdcm:transcode-rle|gdcm:jpegls` (mapped by `options.syntax`), `validate -> gdcm:dump` (minimal proxy), VTK demos (`vtk_*`), unit/integration tests (`test_gdcm`, `test_dcmtk`, `test_itk`, `test_vtk_unit`, `test_utils`, `test_integration`, `test_edge_cases`, `test_validation`, `run_cpp_tests`).
- **Java (dcm4chee)**: CLI in `java/dcm4che-tests/target/dcm4che-tests.jar` (`java -jar ...`): `info --json`, `anonymize --output`, `to-image --output [--format] [--frame]`, `transcode --output --syntax`, `validate`, `dump [--max-width]`, `stats --bins [--json|--pretty]`, `echo host:port [--timeout --calling --called]`.
- **C# (fo-dicom)**: CLI in `cs/bin/(Release|Debug)/net8.0/DicomTools.Cli`: `info --json`, `anonymize --output`, `to-image --output [--frame] [--format]`, `transcode --output --transfer-syntax`, `validate`, `echo host:port`, `dump [--depth --max-value-length]`, `stats --json [--frame]`, `histogram --json [--bins] [--frame]`, tests via `dotnet test DicomTools.Tests` (`test_anonymize_cs`, `test_uid_cs`, `test_datetime_cs`, `test_charset_cs`, `test_dictionary_cs`, `test_file_operations_cs`, `test_sequence_cs`, `test_value_representation_cs`, `test_option_parser_cs`, `test_stats_helpers_cs`, `run_cs_tests`).
- **JavaScript (shim)**: CLI in `js/contract-cli/index.js` (env `JS_DICOM_TOOLS_CMD` to override). Implements the contract by delegating to the Python backend: `info/anonymize/to_image/transcode/validate/stats/dump/volume/nifti/echo`.

## Binaries and Environment Variables
- `PYTHON_DICOM_TOOLS_CMD` (default: `python -m DICOM_reencoder.cli`, cwd=`python/`)
- `RUST_DICOM_TOOLS_BIN` (default: `rust/target/release/dicom-tools`; fallback `cargo run --release --`)
- `CPP_DICOM_TOOLS_BIN` (default: `cpp/build/DicomTools`)
- `JS_DICOM_TOOLS_CMD` (default: `node js/contract-cli/index.js`)

## Request Example
```json
{
  "backend": "rust",
  "op": "to_image",
  "input": "samples/ct.dcm",
  "output": "output/ct.png",
  "options": { "format": "png", "frame": 0, "window_center": -600, "window_width": 1600 }
}
```

## Response Example
```json
{
  "ok": true,
  "returncode": 0,
  "stdout": "Saved output/ct.png",
  "stderr": "",
  "output_files": ["output/ct.png"],
  "metadata": null
}
```
