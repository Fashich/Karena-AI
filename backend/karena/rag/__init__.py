"""Karena RAG package.

Expose commonly used submodules at package level so unit tests and
legacy import paths (e.g. `karena.rag.pipeline.RAGPipeline`) resolve
correctly. Use lazy imports to avoid loading heavy ML deps at import
time in lightweight test runs.
"""

import importlib
from typing import Any

__all__ = [
    "pipeline",
    "embeddings",
    "model_registry",
    "drift",
    "vector_store",
    "reranker",
    "chunking",
]

_submodules = {name: f"karena.rag.{name}" for name in __all__}


def __getattr__(name: str) -> Any:
    if name in _submodules:
        module = importlib.import_module(_submodules[name])
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + __all__)
