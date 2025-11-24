# Interface unificada (Tkinter + contrato CLI/JSON)

Este diretório concentra a UI Tkinter e os adaptadores que chamam os backends C++/Python/Rust via subprocesso, trocando requisições/respostas no formato descrito em `CONTRACT.md`.

## Requisitos
- Python 3 instalado.
- Backends compilados/instalados:
  - Python: `pip install -e python` ou usar diretamente `python -m DICOM_reencoder.cli` (cwd `python/`).
  - Rust: `cargo build --release` em `rust/` (gera `rust/target/release/dicom-tools`).
  - C++: `cmake --build .` em `cpp/build` (gera `cpp/build/DicomTools`).

Variáveis de ambiente opcionais para apontar binários:
- `PYTHON_DICOM_TOOLS_CMD` (default `python -m DICOM_reencoder.cli`, cwd `python/`)
- `RUST_DICOM_TOOLS_BIN` (default `rust/target/release/dicom-tools`; fallback `cargo run --release --`)
- `CPP_DICOM_TOOLS_BIN` (default `cpp/build/DicomTools`)
- `CS_DICOM_TOOLS_CMD` (default `cs/bin/Release/net8.0/DicomTools.Cli`)
- `JAVA_DICOM_TOOLS_CMD` (default `java/dcm4che-tests/target/dcm4che-tests.jar` via `java -jar`)

## Usando a UI Tkinter
```bash
python -m interface.app
```
Escolha backend, operação, caminhos de entrada/saída, e (opcional) um JSON de opções. O resultado aparece em JSON no painel inferior.

## Usando o executor headless (sem UI)
```bash
# Com flags
python -m interface.contract_runner --backend python --op info --input /caminho/arquivo.dcm

# Com arquivo JSON
python -m interface.contract_runner --request-file request.json

# Via pipe
echo '{"backend":"rust","op":"dump","input":"file.dcm"}' | python -m interface.contract_runner
```

## Contrato
O formato de requisição/resposta e o mapeamento mínimo de operações estão em `CONTRACT.md`.
