# Repository Guidelines

## Project Structure & Module Organization
- `python/`: DICOM toolkit and CLI (`DICOM_reencoder`). Tests in `python/tests/`.
- `cpp/`: C++ CLI/tests for GDCM, DCMTK, ITK, VTK. Build artifacts in `cpp/build/`.
- `rust/`: Rust CLI/web (`dicom-tools`). Integration tests in `rust/tests/`.
- `interface/`: Tkinter UI + contract adapters (CLI/JSON).
- `cs/`: Forthcoming fo-dicom integration (C#).
- `java/`: dcm4chee integration (tests iniciais prontos).
- `js/`: Cornerstone3D workspace (clonado para avaliação/integração).
- `sample_series/`: Example DICOM data (if present).
- `plano.md`, `STRUCTURE.md`: planning and layout docs.

## Build, Test, and Development Commands
- Python CLI: `pip install -e python` then `python -m DICOM_reencoder.cli --help`.
- Python tests: `cd python && pytest`.
- Rust: `cd rust && cargo build --release` ; tests: `cargo test`.
- C++: `cd cpp && mkdir -p build && cd build && cmake .. && cmake --build .` ; tests (if configured): `ctest`.
- Interface UI: `python -m interface.app` (assumes Python deps installed).
- Contract runner (headless): `python -m interface.contract_runner --backend python --op info --input file.dcm`.

## Coding Style & Naming Conventions
- Python: PEP 8; prefer type hints; keep functions small. Follow existing CLI subcommand names (`info`, `anonymize`, `to_image`, etc.).
- Rust: Rust 2021; run `cargo fmt` and `cargo clippy --all-targets --all-features` before PRs.
- C++: C++17; mirror existing module naming (`gdcm:`, `dcmtk:`, `itk:`, `vtk:`); keep headers/impl split.
- C#: follow standard .NET conventions; use `PascalCase` for public types/members.
- Java: Maven/Gradle conventions; evitar mexer em artefatos gerados; manter pacotes coerentes com dcm4chee.
- JS: seguir padrões do workspace Cornerstone3D (nx/monorepo), npm/yarn scripts.
- Naming: use snake_case for file paths/scripts; keep CLI flags consistent with `CONTRACT.md`.
- Modularização: mantenha lógica em unidades pequenas e reutilizáveis; evite “god files” e acople entre camadas. Adicione pontos de extensão claros (adapters, interfaces) para novos backends.
 - Comunicação entre projetos: alterações no contrato (nomes de operações, opções, formatos) devem sincronizar `interface/CONTRACT.md`, adaptadores em `interface/adapters/*.py`, CLIs nas linguagens e testes de integração.

## Testing Guidelines
- Python: `pytest` in `python/tests`; prefer deterministic outputs; place fixtures under `python/tests/fixtures`.
- Rust: `cargo test`; add integration tests under `rust/tests` for new commands.
- C++: add cases to existing test drivers/ctest; prefer sample data in `sample_series/`.
- C#: `dotnet test` em `cs/DicomTools.Tests` (fo-dicom).
- Java: `mvn test` em `java/dcm4che-tests` (quando ativo).
- UI/contract: add integration tests invoking `interface.contract_runner` to validate responses and outputs.
- JS: seguir scripts do workspace Cornerstone3D (nx/jest) se aplicável.
- Sugerido: `cd python && pytest`; `cd rust && cargo test`; `cd cpp && ctest` ou `python tests/run_all.py`; `cd interface && pytest`; `dotnet test cs/DicomTools.Tests`; `cd java/dcm4che-tests && mvn test` (quando configurado); scripts npm/nx no `js/` se necessário.
- Artefatos: siga `interface/ARTIFACTS.md` para nomes/diretórios padrão; mantenha stdout curto e use stderr para logs detalhados.

## Commit & Pull Request Guidelines
- Keep commits scoped and descriptive (e.g., `interface: add rust adapter mapping`).
- Include what changed, why, and how to test in PR descriptions; link issues when applicable.
- Add screenshots/gifs only when modifying UI (`interface/app.py`).
- Coordenação: alinhe mudanças cross-projeto (contrato, adaptadores, CLIs, CI). Para `java/`/`cs/`/`js/`, confirme requisitos antes de alterar.
- Comunicação entre projetos: alinhe mudanças de contrato entre `interface/CONTRACT.md`, adaptadores (`interface/adapters/*.py`) e CLIs de cada linguagem; ao alterar o envelope ou nomes de operações, atualize doc, wrappers e testes de integração.
