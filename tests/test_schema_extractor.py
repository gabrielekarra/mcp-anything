"""Tests for schema extraction from type definitions."""

from mcp_anything.analysis.schema_extractor import (
    extract_pydantic_fields,
    extract_java_pojo_fields,
    extract_typescript_interface_fields,
)


class TestPydanticExtraction:
    def test_basic_fields(self):
        source = '''
from pydantic import BaseModel

class User(BaseModel):
    name: str
    email: str
    age: int
    is_active: bool = True
'''
        fields = extract_pydantic_fields(source, "User")
        assert len(fields) == 4
        names = {f.name for f in fields}
        assert "name" in names
        assert "email" in names
        assert "age" in names
        age_field = next(f for f in fields if f.name == "age")
        assert age_field.type == "integer"

    def test_optional_fields(self):
        source = '''
from typing import Optional
from pydantic import BaseModel

class Config(BaseModel):
    host: str
    port: int
    debug: Optional[bool] = None
'''
        fields = extract_pydantic_fields(source, "Config")
        debug_field = next(f for f in fields if f.name == "debug")
        assert debug_field.required is False

    def test_field_with_description(self):
        source = '''
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(..., description="The item name")
    price: float = Field(default=0.0, description="Price in USD")
'''
        fields = extract_pydantic_fields(source, "Item")
        name_field = next(f for f in fields if f.name == "name")
        assert name_field.description == "The item name"
        price_field = next(f for f in fields if f.name == "price")
        assert price_field.required is False  # has default


class TestJavaPOJOExtraction:
    def test_basic_fields(self):
        source = '''
public class User {
    private String name;
    private String email;
    private int age;
    private boolean active;
}
'''
        fields = extract_java_pojo_fields(source, "User")
        assert len(fields) == 4
        name_field = next(f for f in fields if f.name == "name")
        assert name_field.type == "string"
        age_field = next(f for f in fields if f.name == "age")
        assert age_field.type == "integer"

    def test_generic_types(self):
        source = '''
public class Response {
    private List<String> items;
    private Map<String, Object> metadata;
}
'''
        fields = extract_java_pojo_fields(source, "Response")
        items_field = next(f for f in fields if f.name == "items")
        assert items_field.type == "array"


class TestTypeScriptExtraction:
    def test_basic_interface(self):
        source = '''
interface User {
  name: string;
  email: string;
  age: number;
  active: boolean;
}
'''
        fields = extract_typescript_interface_fields(source, "User")
        assert len(fields) == 4
        age_field = next(f for f in fields if f.name == "age")
        assert age_field.type == "integer"

    def test_optional_fields(self):
        source = '''
interface Config {
  host: string;
  port: number;
  debug?: boolean;
}
'''
        fields = extract_typescript_interface_fields(source, "Config")
        debug_field = next(f for f in fields if f.name == "debug")
        assert debug_field.required is False
