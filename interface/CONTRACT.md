# Contrato de Integração (Opção A – CLI/JSON)

Meta: ter uma interface única (Tkinter) chamando cada backend via executáveis de linha de comando, trocando requisições/respostas em JSON (ou texto) e mantendo a mesma assinatura lógica para C++, Python, Rust (hoje) e Java/C# (futuro).

## Envelope de requisição
```json
{
  "backend": "python | cpp | rust | java | csharp",
  "op": "info | anonymize | to_image | transcode | validate | echo | stats | dump | volume | nifti",
  "input": "/caminho/para/arquivo_ou_diretorio",
  "output": "/caminho/para/saida_opcional",
  "options": { "chave": "valor" }
}
```

## Envelope de resposta
```json
{
  "ok": true,
  "returncode": 0,
  "stdout": "texto do processo",
  "stderr": "avisos/erros",
  "output_files": ["/lista/de/arquivos/gerados"],
  "metadata": { "estrutura_normalizada_ou_none": "..." }
}
```

## Operações canônicas
| op | Descrição | Parâmetros esperados | Saídas esperadas |
| --- | --- | --- | --- |
| info | Ler metadata básica | `input`, `options.verbose?` | `metadata` + `stdout` |
| anonymize | Anonimizar arquivo | `input`, `output?` | arquivo anon. em `output_files` |
| to_image | Exportar imagem/frame | `input`, `output`, `options.format? (png/jpeg)`, `options.frame?` | imagem em `output_files` |
| transcode | Trocar syntax/decodificar | `input`, `output`, `options.syntax` | dicom transcodado em `output_files` |
| validate | Validação básica | `input` | `stdout` com resultado |
| echo | C-ECHO | `options.host`, `options.port` | `stdout` com status |
| stats | Estatística de pixels/histograma | `input`, `options.bins?` | `stdout` (e `metadata` se backend suportar) |
| dump | Dump completo do dataset | `input`, `options.depth?`, `options.max_value_len?` | `stdout` textual |
| volume | Construir volume 3D | `input` (diretório), `output?`, `options.preview?` | `.npy` e metadados |
| nifti | Exportar série para NIfTI | `input` (diretório), `output?`, `options.series_uid?` | `.nii/.nii.gz` + meta |

## Mapeamento (mínimo viável atual)
- **Python** (`python -m DICOM_reencoder.cli`): `info -> summary --json`, `anonymize -> anonymize`, `to_image -> png`, `transcode -> transcode`, `validate -> python -m DICOM_reencoder.validate_dicom`, `echo -> dicom_echo`, `volume -> volume`, `nifti -> nifti`.  
- **Rust** (`rust/target/release/dicom-tools` ou `cargo run --release -- ...`): `info`, `anonymize`, `to_image` (`to-image`), `transcode`, `validate` (`validate`), `echo` (`echo`), `dump` (`dump`), `stats` (`stats`/`histogram`).  
- **C++** (`cpp/build/DicomTools`): `info/dump -> gdcm:dump`, `anonymize -> gdcm:anonymize`, `to_image -> gdcm:preview`, `stats -> gdcm:stats`, `transcode -> gdcm:transcode-j2k|gdcm:transcode-rle|gdcm:jpegls` (mapeado por `options.syntax`), `validate -> gdcm:dump` (proxy até existir comando dedicado).  
- **Java (dcm4chee)**: a ser integrado na etapa penúltima; expectativa é expor um CLI/REST que aceite o mesmo envelope e devolva JSON.  
- **C# (fo-dicom)**: esqueleto de wrapper em `interface/adapters/csharp_cli.py`; exige um CLI em `cs/` que implemente as operações do contrato (nomes equivalentes aos demais backends).

## Binaries e variáveis de ambiente
- `PYTHON_DICOM_TOOLS_CMD` (padrão: `python -m DICOM_reencoder.cli`, cwd=`python/`)
- `RUST_DICOM_TOOLS_BIN` (padrão: `rust/target/release/dicom-tools`; fallback `cargo run --release --`)
- `CPP_DICOM_TOOLS_BIN` (padrão: `cpp/build/DicomTools`)

## Exemplo de requisição
```json
{
  "backend": "rust",
  "op": "to_image",
  "input": "samples/ct.dcm",
  "output": "output/ct.png",
  "options": { "format": "png", "frame": 0, "window_center": -600, "window_width": 1600 }
}
```

## Exemplo de resposta
```json
{
  "ok": true,
  "returncode": 0,
  "stdout": "Saved output/ct.png",
  "stderr": "",
  "output_files": ["output/ct.png"],
  "metadata": null
}
```
