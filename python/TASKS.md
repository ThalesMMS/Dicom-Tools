# Python Tasks
- Resolver avisos de packaging (pyproject: license SPDX, discovery de web_static/web_templates) antes de release.
- Garantir que `python -m DICOM_reencoder.cli` cobre o contrato (info/anonymize/to_image/transcode/validate/echo/volume/nifti) com saídas estáveis; se necessário, adicionar flags `--json`.
- Ampliar testes em `python/tests` para operações de contrato faltantes (volume/nifti/transcode) usando `sample_series` (há skips atuais).
- Incluir dados estáticos (web_static/web_templates) corretamente no pacote; revisar `setup.py`/`MANIFEST.in`.
