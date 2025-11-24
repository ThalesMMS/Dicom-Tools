#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PYTHON=${PYTHON:-python3}
BUILD_TYPE=${BUILD_TYPE:-Release}

echo "== Dicom-Tools setup (Python/Rust/C++) =="

echo "-- Python install (editable) --"
(cd "$ROOT/python" && "$PYTHON" -m pip install -e .)

echo "-- Rust build (--release) --"
(cd "$ROOT/rust" && cargo build --release)

echo "-- C++ configure/build --"
mkdir -p "$ROOT/cpp/build"
(cd "$ROOT/cpp/build" && cmake -DCMAKE_BUILD_TYPE="$BUILD_TYPE" .. && cmake --build .)

# Helper: link sample_series to cpp/input if missing
if [ ! -e "$ROOT/cpp/input" ] && [ -d "$ROOT/sample_series" ]; then
  ln -s ../sample_series "$ROOT/cpp/input"
  echo "Linked sample_series -> cpp/input"
fi

echo "Done. Binaries:"
echo "  Rust:   $ROOT/rust/target/release/dicom-tools"
echo "  C++:    $ROOT/cpp/build/DicomTools"
echo "  Python: installed editable package dicom-tools"
