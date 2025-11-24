# Plano de Integração (Opção A – CLI/JSON + UI Tkinter)

Legenda: [ ] pendente | [x] concluído

1. [x] Inventário inicial e limpeza: CLIs mapeados (Python entry_points, Rust clap, C++ módulos), dataset `sample_series/` presente para testes, `.gitignore` cobrindo artefatos/outputs.
2. [x] Contrato CLI/JSON consolidado (`interface/CONTRACT.md`): envelope, operações canônicas, mapeamento mínimo de backends, env vars de binários.
3. [x] Estrutura do monorepo confirmada: layout `cpp/`, `rust/`, `python/`, `interface/`, `cs/`, `java/`, scripts auxiliares (ver `STRUCTURE.md`).
4. [x] Toolchains e builds reprodutíveis: Makefile raiz com builds/tests por linguagem, BUILD.md com requisitos e uso de `cpp/scripts/build_deps.sh`, orientação para pin (pip-compile) e cache de deps.
5. [x] Padronizar CLIs para o contrato: mapeamentos atualizados no contrato e adaptador C++ cobrindo transcode (j2k/rle/jpegls) e fallback de validate.
6. [x] Wrappers do contrato (subprocesso): `interface/adapters/*.py` chamando CLIs C++/Rust/Python, com `RunResult` padronizado.
7. [x] UI Tkinter inicial: `interface/app.py` usando o contrato, campos básicos e retorno em JSON.
8. [x] Artefatos e logging: convenção de nomes de saída documentada em `interface/ARTIFACTS.md` (outputs por backend, defaults, limpeza, stdout/stderr).
9. [x] Testes unitários/funcionais por backend: Rust `cargo test` ok; Python `pytest` ok (com deps instaladas); C++ `python tests/run_all.py` ok após build; interface `pytest` ok.
10. [x] Testes de integração via contrato: suíte pytest em `interface/tests/test_contract_runner.py` (usa sample_series e backends buildados).
11. [ ] Empacotamento e distribuição: wheels Python, binários Rust/C++, script `scripts/setup_all.sh`.
12. [ ] CI/CD unificado: pipeline com build/lint/test de todos e testes de integração do contrato.
13. [ ] (Antipenúltima) Testar tudo: checklist completo de funcionalidades expostas, comparação entre backends quando aplicável, validação manual da UI.
14. [ ] (Penúltima) Integrar Java (dcm4chee) no contrato: CLI/REST fino + wrapper `interface/adapters/java_cli.py` (testes iniciais já rodados em `java/dcm4che-tests`).
15. [ ] (Última) Integrar C# (fo-dicom) no contrato: implementar CLI/JSON no projeto `cs/`, adicionar wrapper `interface/adapters/csharp_cli.py`, cobrir nos testes (projeto de testes inicial existe em `cs/DicomTools.Tests`).
