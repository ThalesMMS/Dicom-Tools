# Rust Tasks
- Alinhamento do contrato: info/anonymize/to_image/transcode/validate/echo/dump/stats/histogram já cobertos; avaliar `--json` opcional para info/dump.
- Testes: suite atual cobre histogram/transcode; restantes ignoram PACS (echo/push) — adicionar mocks ou variáveis de ambiente para testar PACS quando disponível.
- Empacotamento: gerar binário release determinístico e integrá-lo ao script de distribuição (`scripts/package_all.sh` já copia).
