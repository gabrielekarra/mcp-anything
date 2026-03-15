"""Cross-file dependency resolution for type definitions.

Follows import statements to find type definitions referenced in other files
(e.g., `from models import User` in a FastAPI handler).
"""

import ast
import re
from pathlib import Path
from typing import Optional

from mcp_anything.models.analysis import Language


def resolve_python_import(
    source: str, name: str, root: Path, file_path: str,
) -> Optional[tuple[Path, str]]:
    """Resolve a Python import to a file path and class name.

    Given source code that contains `from X import Y` or `import X.Y`,
    resolve the module path to an actual file relative to root.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                actual_name = alias.asname or alias.name
                if actual_name == name:
                    # Convert module.path to file path
                    module_parts = node.module.split(".")
                    # Try as package: module/path.py
                    candidate = root / Path(*module_parts).with_suffix(".py")
                    if candidate.exists():
                        return (candidate, alias.name)
                    # Try as package/__init__.py
                    candidate = root / Path(*module_parts) / "__init__.py"
                    if candidate.exists():
                        return (candidate, alias.name)
                    # Try relative to file's directory
                    file_dir = (root / file_path).parent
                    candidate = file_dir / Path(*module_parts).with_suffix(".py")
                    if candidate.exists():
                        return (candidate, alias.name)

    return None


def resolve_java_import(
    source: str, class_name: str, root: Path,
) -> Optional[Path]:
    """Resolve a Java import to a file path."""
    pattern = re.compile(
        r"import\s+([\w.]+\." + re.escape(class_name) + r")\s*;"
    )
    match = pattern.search(source)
    if match:
        # Convert com.example.models.User to com/example/models/User.java
        dotted = match.group(1)
        parts = dotted.split(".")
        # Try from src/main/java/ prefix (standard Maven/Gradle layout)
        for prefix in ["src/main/java", "src", ""]:
            candidate = root / prefix / Path(*parts).with_suffix(".java")
            if candidate.exists():
                return candidate

    return None


def resolve_typescript_import(
    source: str, name: str, root: Path, file_path: str,
) -> Optional[Path]:
    """Resolve a TypeScript/JavaScript import to a file path."""
    # import { Name } from './models'
    pattern = re.compile(
        r"import\s*\{[^}]*\b" + re.escape(name) + r"\b[^}]*\}\s*from\s*['\"]([^'\"]+)['\"]"
    )
    match = pattern.search(source)
    if not match:
        # import Name from './models'
        pattern2 = re.compile(
            r"import\s+" + re.escape(name) + r"\s+from\s*['\"]([^'\"]+)['\"]"
        )
        match = pattern2.search(source)

    if match:
        import_path = match.group(1)
        file_dir = (root / file_path).parent

        # Try with various extensions
        for ext in ["", ".ts", ".tsx", ".js", ".jsx", "/index.ts", "/index.js"]:
            candidate = (file_dir / import_path).with_suffix("") if ext.startswith("/") else file_dir / (import_path + ext)
            if ext.startswith("/"):
                candidate = file_dir / import_path / ext.lstrip("/")
            else:
                candidate = file_dir / (import_path + ext)
            candidate = candidate.resolve()
            if candidate.exists():
                return candidate

    return None


def find_type_definition(
    name: str, source: str, root: Path, source_file: str, language: Language,
) -> Optional[tuple[Path, str]]:
    """Find a type definition by following imports.

    Returns (file_path, type_name) if found, None otherwise.
    """
    if language == Language.PYTHON:
        return resolve_python_import(source, name, root, source_file)
    elif language == Language.JAVA:
        result = resolve_java_import(source, name, root)
        if result:
            return (result, name)
    elif language in (Language.TYPESCRIPT, Language.JAVASCRIPT):
        result = resolve_typescript_import(source, name, root, source_file)
        if result:
            return (result, name)
    return None
