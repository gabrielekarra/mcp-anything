"""Python API backend for imagemagick."""

import sys
from pathlib import Path
from typing import Any


class Backend:
    """Communicates with imagemagick via direct Python API calls."""

    def __init__(self) -> None:
        self.codebase_path = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        # Add the target codebase to sys.path so we can import from it
        path_str = str(self.codebase_path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)

    async def call_function(self, module: str, function: str, **kwargs: Any) -> str:
        """Import and call a function from the target codebase."""
        import importlib
        mod = importlib.import_module(module)
        func = getattr(mod, function)
        result = func(**{k: v for k, v in kwargs.items() if v is not None})
        return str(result)

    async def query(self, uri: str) -> str:
        """Query a resource via API."""
        return await self.call_function("__main__", "query", uri=uri)
