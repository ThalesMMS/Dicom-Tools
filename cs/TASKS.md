# C# Tasks (fo-dicom)
- CLI fo-dicom: garantir que o binário em `cs/bin/Release/net8.0/DicomTools.Cli` implemente o contrato (info/anonymize/to_image/transcode/validate/echo/dump/stats/histogram) e emita JSON quando aplicável (env `CS_DICOM_TOOLS_CMD`).
- Testes: `dotnet test` já passa (21/21); expandir cobertura para validar outputs e JSON para cada operação usando `sample_series`.
- Distribuição: preparar alvo Release e script de empacotamento para copiar o binário para `artifacts/`.
