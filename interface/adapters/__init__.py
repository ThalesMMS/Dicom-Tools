# Adapters para cada backend CLI (Python, Rust, C++).
from .python_cli import PythonCliAdapter
from .rust_cli import RustCliAdapter
from .cpp_cli import CppCliAdapter
from .csharp_cli import CSharpCliAdapter
from .java_cli import JavaCliAdapter
from .js_cli import JsCliAdapter


def get_adapter(backend: str):
    backend = backend.lower()
    if backend == "python":
        return PythonCliAdapter()
    if backend == "rust":
        return RustCliAdapter()
    if backend == "cpp":
        return CppCliAdapter()
    if backend in {"csharp", "cs", "dotnet"}:
        return CSharpCliAdapter()
    if backend == "java":
        return JavaCliAdapter()
    if backend == "js":
        return JsCliAdapter()
    raise ValueError(f"Backend não suportado: {backend}")
