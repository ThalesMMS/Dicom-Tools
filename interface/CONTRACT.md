# Contrato de Integração (Opção A – CLI/JSON)

Meta: ter uma interface única (Tkinter) chamando cada backend via executáveis de linha de comando, trocando requisições/respostas em JSON (ou texto) e mantendo a mesma assinatura lógica para C++, Python, Rust (hoje) e Java/C# (futuro).

## Envelope de requisição
```json
{
  "backend": "python | cpp | rust | java | csharp",
  "op": "info | anonymize | to_image | transcode | validate | echo | stats | dump | volume | nifti | to_json | from_json | test_gdcm | test_dcmtk | test_itk | test_vtk_unit | test_utils | test_integration | test_edge_cases | test_validation | run_cpp_tests",
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
| dump | Dump completo do dataset | `input`, `options.depth?`, `options.max_value_len?`, `options.json?` | `stdout` textual ou JSON |
| volume | Construir volume 3D | `input` (diretório), `output?`, `options.preview?` | `.npy` e metadados |
| nifti | Exportar série para NIfTI | `input` (diretório), `output?`, `options.series_uid?` | `.nii/.nii.gz` + meta |
| to_json | Exportar para DICOM JSON | `input`, `output?` | JSON em arquivo/`stdout` |
| from_json | Converter de DICOM JSON para DICOM | `input` (JSON), `output` (DICOM) | arquivo DICOM |
| test_gdcm | Executa binário de teste unitário GDCM (C++) | `input?` (ignorado) | `stdout` com resultado |
| test_dcmtk | Executa binário de teste unitário DCMTK (C++) | `input?` (ignorado) | `stdout` com resultado |
| test_itk | Executa binário de teste unitário ITK (C++) | `input?` (ignorado) | `stdout` com resultado |
| test_vtk_unit | Executa binário de teste unitário VTK (C++) | `input?` (ignorado) | `stdout` com resultado |
| test_utils | Executa binário de testes utilitários C++ | `input?` (ignorado) | `stdout` com resultado |
| test_integration | Executa testes de integração C++ (GDCM/DCMTK) | `input?` (ignorado) | `stdout` |
| test_edge_cases | Executa testes de edge cases C++ | `input?` (ignorado) | `stdout` |
| test_validation | Executa testes de validação C++ | `input?` (ignorado) | `stdout` |
| run_cpp_tests | Executa todos os testes C++ (target run_cpp_tests) | `input?` (ignorado) | `stdout` |

## Mapeamento (mínimo viável atual)
- **Python** (`python -m DICOM_reencoder.cli`): `info -> summary --json`, `anonymize -> anonymize`, `to_image -> png`, `transcode -> transcode`, `validate -> python -m DICOM_reencoder.validate_dicom`, `echo -> dicom_echo`, `volume -> volume`, `nifti -> nifti`.  
- **Rust** (`rust/target/release/dicom-tools` ou `cargo run --release -- ...`): `info [--json]`, `anonymize`, `to_image` (`to-image`), `transcode`, `validate` (`validate`), `echo` (`echo`), `dump [--json]` (`dump`), `stats` (`stats`/`histogram`), `to_json` (`to-json`), `from_json` (`from-json`).  
- **C++** (`cpp/build/DicomTools`): `info/dump -> gdcm:dump`, `anonymize -> gdcm:anonymize`, `to_image -> gdcm:preview`, `stats -> gdcm:stats`, `transcode -> gdcm:transcode-j2k|gdcm:transcode-rle|gdcm:jpegls` (mapeado por `options.syntax`), `validate -> gdcm:dump` (proxy mínima), VTK demos (`vtk_*`), unit/integration tests (`test_gdcm`, `test_dcmtk`, `test_itk`, `test_vtk_unit`, `test_utils`, `test_integration`, `test_edge_cases`, `test_validation`, `run_cpp_tests`).  
- **Java (dcm4chee)**: CLI em `java/dcm4che-tests/target/dcm4che-tests.jar` (`java -jar ...`): `info --json`, `anonymize --output`, `to-image --output [--format] [--frame]`, `transcode --output --syntax`, `validate`, `dump [--max-width]`, `stats --bins [--json|--pretty]`, `echo host:port [--timeout --calling --called]`.  
- **C# (fo-dicom)**: CLI em `cs/bin/(Release|Debug)/net8.0/DicomTools.Cli`: `info --json`, `anonymize --output`, `to-image --output [--frame] [--format]`, `transcode --output --transfer-syntax`, `validate`, `echo host:port`, `dump [--depth --max-value-length]`, `stats --json [--frame]`, `histogram --json [--bins] [--frame]`.
- **JavaScript (shim)**: CLI em `js/contract-cli/index.js` (env `JS_DICOM_TOOLS_CMD` para sobrescrever). Implementa o contrato delegando ao backend Python: `info/anonymize/to_image/transcode/validate/stats/dump/volume/nifti/echo`.

## Binaries e variáveis de ambiente
- `PYTHON_DICOM_TOOLS_CMD` (padrão: `python -m DICOM_reencoder.cli`, cwd=`python/`)
- `RUST_DICOM_TOOLS_BIN` (padrão: `rust/target/release/dicom-tools`; fallback `cargo run --release --`)
- `CPP_DICOM_TOOLS_BIN` (padrão: `cpp/build/DicomTools`)
- `JS_DICOM_TOOLS_CMD` (padrão: `node js/contract-cli/index.js`)

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
