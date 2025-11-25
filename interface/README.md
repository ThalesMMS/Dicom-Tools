# Interface unificada (Tkinter + contrato CLI/JSON)

Este diretório concentra a UI Tkinter e os adaptadores que chamam os backends C++/Python/Rust via subprocesso, trocando requisições/respostas no formato descrito em `CONTRACT.md`.

## Requisitos
- Python 3 instalado.
- Backends compilados/instalados:
  - Python: `pip install -e python` ou usar diretamente `python -m DICOM_reencoder.cli` (cwd `python/`).
  - Rust: `cargo build --release` em `rust/` (gera `rust/target/release/dicom-tools`).
  - C++: `cmake --build .` em `cpp/build` (gera `cpp/build/DicomTools`).

Optional env vars to point binaries:
- `PYTHON_DICOM_TOOLS_CMD` (default `python -m DICOM_reencoder.cli`, cwd `python/`)
- `RUST_DICOM_TOOLS_CMD` (overrides rust binary) ou `RUST_DICOM_TOOLS_BIN` (default `rust/target/release/dicom-tools`; fallback `cargo run --release --`)
- `CPP_DICOM_TOOLS_BIN` (default `cpp/build/DicomTools`)
- `CS_DICOM_TOOLS_CMD` (default `cs/bin/Release/net8.0/DicomTools.Cli` ou Debug fallback)
- `JAVA_DICOM_TOOLS_CMD` (default `java/dcm4che-tests/target/dcm4che-tests.jar` via `java -jar`)
- `JS_DICOM_TOOLS_CMD` (default `node js/contract-cli/index.js`)

## Usando a UI Tkinter
```bash
python -m interface.app
```
Escolha backend, operação, caminhos de entrada/saída, e (opcional) um JSON de opções. O resultado aparece em JSON no painel inferior.

## Usando o executor headless (sem UI)
```bash
# Com flags
python -m interface.contract_runner --backend python --op info --input /caminho/arquivo.dcm

# Com arquivo JSON
python -m interface.contract_runner --request-file request.json

# Via pipe
echo '{"backend":"rust","op":"dump","input":"file.dcm"}' | python -m interface.contract_runner
```

## Contrato
O formato de requisição/resposta e o mapeamento mínimo de operações estão em `CONTRACT.md`. As respostas do runner incluem sempre `ok`, `returncode`, `stdout/stderr`, `artifacts` (aliases de `output_files`), `metadata`, além de `backend` e `operation` para facilitar depuração.

## Arquitetura reativa da UI
- Event bus + Command pattern (`interface/input/event_bus.py`) mantêm UI e engine desacoplados.
- `ToolManager` centraliza ferramentas (scroll/zoom/pan/WL/ROI/overlay/MPR) e gera `frame_requested` para o render loop.
- `RenderLoop` (`interface/components/render_loop.py`) consome os requests e emite `frame_ready` assim que o core terminar.
- Viewers (`TwoDViewer`, `MPRViewer`, `VolumeViewer`) só reagem a `frame_ready` e renderizam overlays via `OverlayManager`.
- Pipeline alvo: `UI Input → Command → Core → Frame → Viewer → UI`.

O render loop tem proteção contra reentrância: eventos `frame_ready` que disparem novos `frame_requested` são ignorados enquanto um frame está sendo gerado, evitando loops infinitos.

Para uso headless/testável:
```python
from interface.runtime import InterfaceRuntime
from interface.state.frames import Frame

class DummyEngine:
    def render(self, request):
        return Frame(viewer=request.viewer, slice_index=request.slice_index, width=256, height=256)

runtime = InterfaceRuntime.create(DummyEngine())
runtime.inputs.scroll("2d", 1)
```

## Eventos/inputs padronizados
Todos os viewers compartilham os mesmos comandos: `onScroll`, `onZoom`, `onPan`, `onWindowLevel`, `onChangeSeries`, `onToggleOverlay`, `onSelectROI`, `onDrag`, `onRebuildMPR`. Os adapters em `interface/input/adapters.py` cuidam do mapeamento de mouse/teclado/gestos para esses comandos.

## Overlays
`OverlayManager` (`interface/overlays/manager.py`) concentra WL/WW, índice da imagem, localização, espessura, timestamp, nome da série, ferramenta ativa e marcadores de orientação. A UI só chama `overlay.render(context, state)`.

## Estrutura da pasta
- `components/`: viewers reativos + render loop.
- `input/`: event bus, controller unificado, adapters 2D/MPR/Volume, `ToolManager`.
- `overlays/`: `OverlayManager` e overlays padrão.
- `state/`: `UIState`, `ViewerState`, `FrameRequest/Frame`.
- `utils/`: helpers de geometria (pan/zoom/transform, clipping de ROI, bounding boxes).

## Convenções de coordenadas
- Pan/zoom operam em coordenadas de canvas (origem no canto superior esquerdo).
- `window_center/window_width` seguem valores numéricos do frame (sem acoplamento a toolkit gráfico).
- Transformações 2D mantêm matriz 3x3 (translate/scale) em `ViewerState`.

## Testes
```bash
python3 -m pytest interface/tests
```
Cobertura inclui runner do contrato e interações de UI (scroll, zoom, pan, WL, overlays, troca de viewer, rebuild MPR).
