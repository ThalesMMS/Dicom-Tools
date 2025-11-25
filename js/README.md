# JS Layer (Cornerstone Gateway & Contract CLI)

Pasta com os artefatos JS do projeto. Inclui o gateway Cornerstone3D usado pelo viewer web e um shim de CLI para o contrato.

## Estrutura
- `viewer-gateway/`: app Vite + gateway para Cornerstone3D (WADO-URI) e testes Vitest.
- `contract-cli/`: shim Node que encaminha chamadas do contrato para o backend Python.
- `new_features.md`: sugestões/estado de testes automatizados.
- `INTEGRATION.md`, `TASKS.md`: notas e tarefas rápidas de integração.

## Pré-requisitos
- Node 18+.
- `sample_series/` na raiz do repo (usada em testes e demo).

## Viewer Gateway
```bash
cd js/viewer-gateway
npm install
npm run dev        # demo Vite; sirva sample_series em http://localhost:8080/sample_series
npm run build      # build de produção
npm test           # Vitest (gateway + MPR/MIP/overlay via sample_series)
```

## Contract CLI
```bash
node js/contract-cli/index.js --op info --input sample_series/IM-0001-0001.dcm --options "{}"
```
- Usa `BACKING_CMD` (env) para redirecionar para outro backend; padrão: `python -m DICOM_reencoder.cli`.

## Notas rápidas
- Tests usam `sample_series` localmente (verifique o caminho ao rodar em CI/containers).
- O gateway constrói `wadouri:` imageIds para séries servidas por HTTP; veja `viewer-gateway/src/imageIds.ts`.
