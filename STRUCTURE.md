# Estrutura do monorepo

- `cpp/`: CLI e módulos C++ (GDCM, DCMTK, ITK, VTK). Build esperado em `cpp/build/DicomTools`.
- `rust/`: CLI/web em Rust (`dicom-tools`), build em `rust/target/release/dicom-tools`.
- `python/`: Toolkit Python (`DICOM_reencoder`), CLI `python -m DICOM_reencoder.cli`.
- `interface/`: UI Tkinter e adaptadores do contrato CLI/JSON.
- `cs/`: Esqueleto para integração fo-dicom (C#).
- `java/`: Integração dcm4chee (tests iniciais prontos).
- `js/`: Workspace para Cornerstone3D (clonado para testes/integração futura).
- `sample_series/`: Amostras de DICOM para testes locais (se presentes).
- `plano.md`: Plano de integração com status.
