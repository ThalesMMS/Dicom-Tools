#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON=${PYTHON:-python3}
BUILD_TYPE=${BUILD_TYPE:-Release}
ARTIFACTS="${ROOT}/artifacts"

mkdir -p "$ARTIFACTS"

echo "== Packaging Python (sdist + wheel) =="
(cd "$ROOT/python" && "$PYTHON" -m build)
cp "$ROOT"/python/dist/* "$ARTIFACTS"/ 2>/dev/null || true

echo "== Packaging Rust (release binary) =="
(cd "$ROOT/rust" && cargo build --release)
cp "$ROOT/rust/target/release/dicom-tools" "$ARTIFACTS/" 2>/dev/null || true

echo "== Packaging C++ (release binary) =="
if [ ! -d "$ROOT/cpp/build" ]; then
  mkdir -p "$ROOT/cpp/build"
  (cd "$ROOT/cpp/build" && cmake -DCMAKE_BUILD_TYPE="$BUILD_TYPE" ..)
fi
(cd "$ROOT/cpp/build" && cmake --build .)
cp "$ROOT/cpp/build/DicomTools" "$ARTIFACTS/" 2>/dev/null || true

echo "Artifacts copied to $ARTIFACTS"
