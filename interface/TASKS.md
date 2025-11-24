# Interface Tasks
- UI: melhorar feedback de execução (barra de progresso/logs), preview de imagem para `to_image`, e validação de inputs.
- Contrato: manter adaptadores sincronizados com mudanças de operações/env vars; adicionar tratamento de paths padrão para backends Java/C# assim que os CLIs estiverem prontos.
- Testes: ampliar `interface/tests/test_contract_runner.py` para cobrir transcode/anonymize/errors, usando `sample_series`.
- DX: adicionar atalho de CLI para rodar testes da interface (ex.: target no Makefile ou script).
