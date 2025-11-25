#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PYTHON=${PYTHON:-python3}
BUILD_TYPE=${BUILD_TYPE:-Release}

echo "== Dicom-Tools setup (Python/Rust/C++/C#/Java/JS) =="

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

echo "-- Python install (editable) --"
require_cmd "$PYTHON"
if [ -f "$ROOT/python/requirements-dev.txt" ]; then
  (cd "$ROOT/python" && "$PYTHON" -m pip install -r requirements-dev.txt)
fi
(cd "$ROOT/python" && "$PYTHON" -m pip install -e .)

echo "-- Rust build (--release) --"
require_cmd cargo
(cd "$ROOT/rust" && cargo build --release)

echo "-- C++ configure/build --"
require_cmd cmake
mkdir -p "$ROOT/cpp/build"
(cd "$ROOT/cpp/build" && cmake -DCMAKE_BUILD_TYPE="$BUILD_TYPE" .. && cmake --build .)

# Helper: link sample_series to cpp/input if missing
if [ ! -e "$ROOT/cpp/input" ] && [ -d "$ROOT/sample_series" ]; then
  ln -s ../sample_series "$ROOT/cpp/input"
  echo "Linked sample_series -> cpp/input"
fi

echo "-- C# build (fo-dicom CLI + tests) --"
require_cmd dotnet
(cd "$ROOT/cs" && dotnet restore)
(cd "$ROOT/cs" && dotnet build DicomTools.sln)

echo "-- Java build (dcm4che-tests) --"
require_cmd mvn
(cd "$ROOT/java/dcm4che-tests" && mvn -B -DskipTests package)

echo "-- JS install (viewer-gateway) --"
require_cmd npm
(cd "$ROOT/js/viewer-gateway" && npm ci)

echo "Done. Binaries/artifacts:"
echo "  Rust:     $ROOT/rust/target/release/dicom-tools"
echo "  C++:      $ROOT/cpp/build/DicomTools"
echo "  Python:   installed editable package dicom-tools"
echo "  C#:       $ROOT/cs/DicomTools.Cli/bin"
echo "  Java:     $ROOT/java/dcm4che-tests/target/dcm4che-tests.jar"
echo "  JS build: deps installed under js/viewer-gateway/node_modules"
