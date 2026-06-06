# Artifacts and Output Conventions

Goal: keep backend outputs predictable to make debugging, cleanup, and CLI/JSON contract integration easier.

## General Conventions
- Use a backend-specific `output/` path when the request does not provide an explicit path.
- Derive names from the input: `<stem>_<op>.<ext>` or `<stem>.<ext>` when that is appropriate, such as PNG output.
- Log errors to stderr; stdout should be short and readable, or JSON when `--json` is enabled.

## Python (`python/`)
- Prefer `output/` at the repository root when no output is specified; current scripts already infer names such as `<stem>_anonymized.dcm` and `<stem>.png`.
- Logs: short messages in stdout; errors/exceptions in stderr.
- Mapped operations:
  - anonymize -> `<stem>_anonymized.dcm`
  - to_image -> `<stem>.png`
  - transcode -> `<stem>_explicit.dcm`
  - volume -> `volume.npy` (+ metadata JSON)
  - nifti -> `<stem>.nii.gz`

## Rust (`rust/`)
- Binary `dicom-tools`: follow the standard stdout output; write files to provided paths. For operations without an explicit output, use `output/` at the repository root.
- Detailed logs: keep them in stderr (tracing); keep summaries in stdout.
- Mapped operations (default): anonymize (`*_anonymized.dcm`), to_image (`*.png`), transcode (`*_explicit.dcm`); volume/nifti use caller-provided paths.

## C++ (`cpp/`)
- Executable `DicomTools`: already uses `-o` for the output directory; keep the default `cpp/output/` when no output is specified.
- Common files:
  - Dump: `dump.txt`
  - Preview: `preview.pgm`
  - Stats: `pixel_stats.txt`
  - Transcodes: preserve the input name inside `-o`.

## Interface/Contract (`interface/`)
- Adapters infer `output` when it is empty:
  - Python: uses name heuristics such as `_anonymized`, `.png`, `.nii.gz`.
  - Rust: `_anonymized.dcm`, `.png`, `_explicit.dcm`.
  - C++: `cpp/output/` directory with the default names listed above.
- When adding new backends (Java/C#), use the same convention: accept an explicit `output`; otherwise write to `output/<backend>/`.

## Cleanup
- `make clean` removes Python/C++/interface artifacts and `rust/target/`.
- Avoid writing outside `output/` or paths passed explicitly by the caller.
