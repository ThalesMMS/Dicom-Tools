# Build & Tooling Guide

Use o `Makefile` na raiz para builds reprodutíveis por linguagem. Ajuste variáveis (`PYTHON`, `CARGO`, `CMAKE`, `BUILD_TYPE`) conforme o ambiente.

## Requisitos gerais
- Python 3.10+ com `pip`.
- Rust toolchain estável (1.75+).
- CMake ≥3.15 e compilador C++17.
- Opcional: .NET SDK para `cs/`, JDK/Gradle/Maven para `java/` (não editar `java/` enquanto outro agente trabalha).

## Comandos principais (Makefile)
- `make python-install` — instala o toolkit Python em modo editável.
- `make python-test` — roda `pytest` em `python/tests`.
- `make rust-build` — compila o binário Rust (`target/release/dicom-tools`).
- `make rust-test` — roda `cargo test`.
- `make cpp-build` — gera `cpp/build/` com CMake e builda o executável `DicomTools`.
- `make cpp-test` — roda `ctest` em `cpp/build` (se configurado).
- `make interface-run` — abre a UI Tkinter (`interface/app.py`).
- `make all` — `python-install`, `rust-build`, `cpp-build`.
- Script único: `scripts/setup_all.sh` (instala Python editável, builda Rust release e C++ release, cria symlink `cpp/input -> sample_series` se houver).
- Interface tests: `cd interface && pytest` (requer backends buildados e `sample_series/` presente).
- Recomendação geral de testes: `cd python && pytest`, `cd rust && cargo test`, `cd cpp/build && ctest`, `cd interface && pytest`.
- Java: `cd java/dcm4che-tests && mvn test` (exige JDK/ Maven e dependências baixadas).
- C#: `cd cs && dotnet test` (exige .NET SDK).
- JS: sem workspace clonado; quando houver projeto npm/nx, use os scripts definidos lá.

## Python (python/)
- Dependências em `requirements.txt` (mínimos). Use `python -m pip install -e .` para dev. Para pin exato, use `pip-compile` gerando um lock (não commitado por padrão).
- Dev/test: `pip install -r python/requirements-dev.txt` para `pytest` e `build`.
- Testes: `pytest`.

## Rust (rust/)
- Build: `cargo build --release`. Tests: `cargo test`. Formatação/lint: `cargo fmt`, `cargo clippy --all-targets --all-features`.

## C++ (cpp/)
- Configure/build: `mkdir -p cpp/build && cd cpp/build && cmake -DCMAKE_BUILD_TYPE=Release .. && cmake --build .`.
- Dependências pesadas (GDCM, DCMTK, ITK, VTK): usar `cpp/scripts/build_deps.sh` para baixar/instalar em `cpp/deps/install` e reusar cache local em builds seguintes.
- Testes: `cd cpp/build && ctest --output-on-failure` (se disponível).

## Interface & Contrato (interface/)
- UI: `python -m interface.app`.
- Executor headless: `python -m interface.contract_runner --backend python --op info --input file.dcm`.
- Ajustes de binários via env vars: `PYTHON_DICOM_TOOLS_CMD`, `RUST_DICOM_TOOLS_BIN`, `CPP_DICOM_TOOLS_BIN`.
- Artefatos/saídas: ver `interface/ARTIFACTS.md` para nomes e diretórios padrão por backend.

## C# (cs/) e Java (java/)
- C#: preparar CLI fo-dicom seguindo contrato CLI/JSON; builds típicos usam `dotnet build` / `dotnet test`.
- Java: integração dcm4chee; testes iniciais estão em `java/dcm4che-tests`.
- JS: integração Cornerstone futura (sem repo clonado no momento).
