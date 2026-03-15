"""Tests for cross-file import resolution."""

from pathlib import Path

from mcp_anything.analysis.import_resolver import (
    resolve_python_import,
    resolve_java_import,
    resolve_typescript_import,
    find_type_definition,
)
from mcp_anything.models.analysis import Language


class TestPythonImportResolution:
    def test_resolves_from_import(self, tmp_path):
        # Create models.py with User class
        models = tmp_path / "models.py"
        models.write_text("class User:\n    pass\n")

        source = "from models import User\n\ndef handler(user: User): pass\n"
        result = resolve_python_import(source, "User", tmp_path, "views.py")
        assert result is not None
        assert result[0] == models
        assert result[1] == "User"

    def test_resolves_nested_import(self, tmp_path):
        # Create app/models.py
        (tmp_path / "app").mkdir()
        models = tmp_path / "app" / "models.py"
        models.write_text("class Item:\n    pass\n")

        source = "from app.models import Item\n"
        result = resolve_python_import(source, "Item", tmp_path, "main.py")
        assert result is not None
        assert result[0] == models

    def test_returns_none_for_missing(self, tmp_path):
        source = "from nonexistent import Foo\n"
        result = resolve_python_import(source, "Foo", tmp_path, "main.py")
        assert result is None

    def test_handles_alias(self, tmp_path):
        models = tmp_path / "models.py"
        models.write_text("class User:\n    pass\n")

        source = "from models import User as UserModel\n"
        result = resolve_python_import(source, "UserModel", tmp_path, "views.py")
        assert result is not None
        assert result[1] == "User"


class TestJavaImportResolution:
    def test_resolves_java_import(self, tmp_path):
        # Create com/example/models/User.java
        pkg = tmp_path / "com" / "example" / "models"
        pkg.mkdir(parents=True)
        user_java = pkg / "User.java"
        user_java.write_text("public class User {}\n")

        source = "import com.example.models.User;\n\npublic class Handler {}\n"
        result = resolve_java_import(source, "User", tmp_path)
        assert result is not None
        assert result == user_java

    def test_returns_none_for_missing(self, tmp_path):
        source = "import com.example.Missing;\n"
        result = resolve_java_import(source, "Missing", tmp_path)
        assert result is None


class TestTypeScriptImportResolution:
    def test_resolves_named_import(self, tmp_path):
        # Create models.ts
        models = tmp_path / "models.ts"
        models.write_text("export interface User { name: string; }\n")

        source = "import { User } from './models';\n"
        result = resolve_typescript_import(source, "User", tmp_path, "handler.ts")
        assert result is not None
        assert result == models.resolve()

    def test_resolves_with_extension(self, tmp_path):
        models = tmp_path / "types.ts"
        models.write_text("export type Config = { port: number; };\n")

        source = "import { Config } from './types';\n"
        result = resolve_typescript_import(source, "Config", tmp_path, "app.ts")
        assert result is not None

    def test_returns_none_for_missing(self, tmp_path):
        source = "import { Foo } from './nonexistent';\n"
        result = resolve_typescript_import(source, "Foo", tmp_path, "app.ts")
        assert result is None


class TestFindTypeDefinition:
    def test_dispatches_python(self, tmp_path):
        models = tmp_path / "models.py"
        models.write_text("class User:\n    pass\n")

        source = "from models import User\n"
        result = find_type_definition("User", source, tmp_path, "views.py", Language.PYTHON)
        assert result is not None
        assert result[1] == "User"

    def test_dispatches_java(self, tmp_path):
        pkg = tmp_path / "com" / "example"
        pkg.mkdir(parents=True)
        user_java = pkg / "User.java"
        user_java.write_text("public class User {}\n")

        source = "import com.example.User;\n"
        result = find_type_definition("User", source, tmp_path, "Handler.java", Language.JAVA)
        assert result is not None

    def test_returns_none_for_unsupported(self, tmp_path):
        result = find_type_definition("Foo", "", tmp_path, "main.rs", Language.RUST)
        assert result is None
