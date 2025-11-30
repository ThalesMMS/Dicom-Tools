# Contract CLI (TypeScript)

CLI shim que implementa o contrato DICOM Tools, delegando operações para o backend Python (ou outro backend configurado via `BACKING_CMD`).

## Estrutura

- **`index.ts`**: Código fonte TypeScript
- **`index.js`**: Wrapper que chama o código compilado em `dist/index.js`
- **`dist/index.js`**: Código TypeScript compilado (gerado por `npm run build`)
- **`tests/index.test.ts`**: Testes unitários TypeScript

## Build

```bash
npm install
npm run build
```

Isso compila o TypeScript para `dist/index.js`.

## Testes

```bash
npm test
npm run test:watch
npm run test:coverage
```

## Uso

O Tkinter interface usa este CLI através do adapter em `interface/adapters/js_cli.py`, que chama `node js/contract-cli/index.js`.

O `index.js` agora automaticamente usa o código TypeScript compilado, então após fazer mudanças no `index.ts`, execute `npm run build` para atualizar.

## Operações Suportadas

- `info`: Ler metadata básica
- `anonymize`: Anonimizar arquivo DICOM
- `to_image`: Exportar frame para imagem (PNG/JPEG)
- `transcode`: Transcodificar transfer syntax
- `validate`: Validar arquivo DICOM
- `stats`: Estatísticas de pixels
- `dump`: Dump completo do dataset
- `volume`: Construir volume 3D
- `nifti`: Exportar para NIfTI
- `echo`: C-ECHO para PACS

