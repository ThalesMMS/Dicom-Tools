# C++ Tasks
- Ajustar geração de SEG: hoje escreve placeholder; revisar VR/SeriesNumber para salvar SEG válido usando dcmtk dcmseg.
- Corrigir DICOMDIR: nomes longos causam erro; gerar nomes 8.3 ao copiar para `output/dicomdir_media`.
- Adicionar modo `validate` real (não apenas dump) e opcionalmente `--json` para info.
- Manter cobertura do contrato: transcode (j2k/rle/jpegls), anonymize, dump/info, stats, preview.
- Garantir build/test automatizado: `cmake .. && cmake --build . && ctest` usando `sample_series` (symlink `cpp/input`).
