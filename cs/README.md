# Dicom-Tools (C# / fo-dicom)

CLI e testes em .NET 8 usando fo-dicom e ImageSharp.

## Estrutura
- `DicomTools.Cli/` — CLI fo-dicom (`DicomTools.Cli.dll`).
- `DicomTools.Tests/` — suite xUnit cobrindo rede (C-STORE/C-FIND/C-MOVE), codecs, imaging/window-level/LUT e multi-frame.
- `sample_series/` (raiz do repo) — séries DICOM usadas nos testes.
- `package_cli.sh` — empacotador de binários do CLI.

## Pré-requisitos
- .NET SDK 8 (ou superior com `DOTNET_ROLL_FORWARD=Major`).
- A pasta `sample_series/` deve estar acessível a partir do diretório base dos testes/CLI.

## Build
```bash
dotnet build DicomTools.sln
# ou apenas o CLI
dotnet build DicomTools.Cli/DicomTools.Cli.csproj
```

## Testes
```bash
# se só houver .NET 10 instalado:
DOTNET_ROLL_FORWARD=Major dotnet test DicomTools.Tests/DicomTools.Tests.csproj
# com .NET 8 disponível:
dotnet test DicomTools.Tests/DicomTools.Tests.csproj
```
Cobertura recente inclui:
- SCPs in-memory para C-STORE/C-FIND/C-MOVE e Modality Worklist (SCU↔SCP).
- Validação de multi-frame color (RGB) com round-trip de compressão (RLE) mantendo pixels/frames.
- Stub DICOMweb STOW→DIMSE bridge para validar ingestão via HTTP e recuperação por C-MOVE.

## CLI
```bash
dotnet cs/bin/Debug/net8.0/DicomTools.Cli.dll --help
```
Operações suportadas:
- `info <input> [--json]`
- `anonymize <input> --output <path>`
- `to-image <input> --output <path> [--frame N] [--format png|jpeg]`
- `transcode <input> --output <path> --transfer-syntax <syntax>`
- `validate <input>`
- `echo <host:port>`
- `dump <input> [--depth N] [--max-value-length N]`
- `stats <input> [--frame N] [--json]`
- `histogram <input> [--bins N] [--frame N] [--json]`

## Notas
- Testes de rede usam SCPs in-memory e portas livres; rodar em ambiente local (sem firewalls bloqueando loopback).
- Cobertura de codecs avançados tenta RLE/JPEG2000/JPEG-LS; se ausentes, os testes retornam sem falha.
