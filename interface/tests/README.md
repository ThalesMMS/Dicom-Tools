# Interface Tests

Este diretório contém testes de integração do contrato CLI/JSON. Eles requerem:
- `sample_series/` com DICOM de teste (ex.: `IM-0001-0147.dcm`).
- Backends buildados: `python -m DICOM_reencoder.cli`, `rust/target/release/dicom-tools` (ou `cargo run --release --`), `cpp/build/DicomTools`.

Rodar:
```bash
cd interface
pytest
```

Configuração opcional:
- Ajuste binários via env vars `PYTHON_DICOM_TOOLS_CMD`, `RUST_DICOM_TOOLS_BIN`, `CPP_DICOM_TOOLS_BIN`.
