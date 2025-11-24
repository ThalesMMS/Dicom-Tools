# Adapters para cada backend CLI (Python, Rust, C++).
from .python_cli import PythonCliAdapter
from .rust_cli import RustCliAdapter
from .cpp_cli import CppCliAdapter


def get_adapter(backend: str):
    backend = backend.lower()
    if backend == "python":
        return PythonCliAdapter()
    if backend == "rust":
        return RustCliAdapter()
    if backend == "cpp":
        return CppCliAdapter()
    raise ValueError(f"Backend não suportado: {backend}")
