# Artefatos e Convenções de Saída

Objetivo: manter saídas previsíveis por backend para facilitar depuração, limpeza e integração no contrato CLI/JSON.

## Convenções gerais
- Use `output/` por backend quando não houver caminho explícito na requisição.
- Nomes derivados do input: `<stem>_<op>.<ext>` ou `<stem>.<ext>` quando fizer sentido (ex.: PNG).
- Registre erros em stderr; stdout deve ser legível e curto, ou JSON quando houver `--json`.

## Python (`python/`)
- Preferir `output/` na raiz do repo quando não especificado; scripts atuais já inferem nomes (ex.: `<stem>_anonymized.dcm`, `<stem>.png`).
- Logs: mensagens curtas em stdout; erros/exceções em stderr.
- Operações mapeadas:
  - anonymize → `<stem>_anonymized.dcm`
  - to_image → `<stem>.png`
  - transcode → `<stem>_explicit.dcm`
  - volume → `volume.npy` (+ metadata JSON)
  - nifti → `<stem>.nii.gz`

## Rust (`rust/`)
- Binário `dicom-tools`: seguir saída padrão em stdout; arquivos em caminhos fornecidos. Para operações sem output explícito, usar `output/` na raiz.
- Logs detalhados: manter em stderr (tracing); resumo em stdout.
- Operações mapeadas (padrão): anonymize (`*_anonymized.dcm`), to_image (`*.png`), transcode (`*_explicit.dcm`), volume/nifti usam paths explícitos do caller.

## C++ (`cpp/`)
- Executável `DicomTools`: já usa `-o` para diretório; manter padrão `cpp/output/` se não especificado.
- Arquivos comuns:
  - Dump: `dump.txt`
  - Preview: `preview.pgm`
  - Stats: `pixel_stats.txt`
  - Transcodes: nome do input preservado dentro de `-o`.

## Interface/Contrato (`interface/`)
- Adaptadores inferem `output` quando vazio:
  - Python: usa heurísticas de nome (ex.: `_anonymized`, `.png`, `.nii.gz`).
  - Rust: `_anonymized.dcm`, `.png`, `_explicit.dcm`.
  - C++: diretório `cpp/output/` com nomes padrão (acima).
- Ao adicionar novos backends (Java/C#), usar a mesma convenção: aceitar `output` explícito, senão escrever em `output/<backend>/`.

## Limpeza
- `make clean` remove artefatos Python/C++/interface e `rust/target/`.
- Evite escrever em diretórios fora de `output/` ou paths passados explicitamente.
