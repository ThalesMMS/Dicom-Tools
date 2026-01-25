"""
Executa requisições do contrato CLI/JSON via linha de comando (sem UI).

Uso:
  python -m interface.contract_runner --backend python --op info --input /caminho/arquivo.dcm
  python -m interface.contract_runner --request-file request.json
  echo '{"backend": "rust", "op": "dump", "input": "file.dcm"}' | python -m interface.contract_runner
"""

import argparse
import json
import sys
from pathlib import Path

from .adapters import get_adapter


def load_request_from_args(args: argparse.Namespace) -> dict:
    if args.request_file:
        return json.loads(Path(args.request_file).read_text())
    if not sys.stdin.isatty():
        # Permite pipe: echo '{...}' | python -m interface.contract_runner
        payload = sys.stdin.read()
        if payload.strip():
            return json.loads(payload)

    # Modo flags individuais
    options = json.loads(args.options) if args.options else {}
    return {
        "backend": args.backend,
        "op": args.op,
        "input": args.input,
        "output": args.output,
        "options": options,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Executor do contrato CLI/JSON (sem UI)")
    parser.add_argument("--request-file", help="Arquivo JSON com a requisição completa")
    parser.add_argument("--backend", help="Backend (python|rust|cpp|java|csharp|js)")
    parser.add_argument("--op", help="Operação (info, anonymize, ...)")
    parser.add_argument("--input", help="Caminho de entrada")
    parser.add_argument("--output", help="Caminho de saída opcional")
    parser.add_argument("--options", help='JSON com options (ex: \'{"frame":0}\')')

    args = parser.parse_args()

    try:
        request = load_request_from_args(args)
    except Exception as exc:
        print(f"Erro lendo request: {exc}", file=sys.stderr)
        return 1

    try:
        adapter = get_adapter(request.get("backend", ""))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    result = adapter.handle(request)
    print(json.dumps(result.as_dict(), indent=2, ensure_ascii=False))
    return 0 if result.ok else (result.returncode or 1)


if __name__ == "__main__":
    sys.exit(main())
