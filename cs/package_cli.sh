#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SRC="$ROOT/bin/Release/net8.0/publish"
DEST="$ROOT/../artifacts/csharp"

if [[ ! -d "$SRC" ]]; then
  echo "Release publish output not found at $SRC" >&2
  echo "Run: dotnet publish DicomTools.Cli/DicomTools.Cli.csproj -c Release -f net8.0" >&2
  exit 1
fi

mkdir -p "$DEST"
rsync -a --delete "$SRC"/ "$DEST"/
echo "Copied DicomTools.Cli artifacts to $DEST"
