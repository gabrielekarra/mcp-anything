"""Models for the analysis phase output."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Language(str, Enum):
    PYTHON = "python"
    JAVA = "java"
    KOTLIN = "kotlin"
    C = "c"
    CPP = "cpp"
    RUST = "rust"
    GO = "go"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    LUA = "lua"
    RUBY = "ruby"
    GRAPHQL = "graphql"
    PROTOBUF = "protobuf"
    SHELL = "shell"
    OTHER = "other"


class FileInfo(BaseModel):
    """Metadata about a source file."""

    path: str
    language: Language
    size_bytes: int
    line_count: int
    is_entry_point: bool = False
    is_api_surface: bool = False


class IPCType(str, Enum):
    CLI = "cli"
    SOCKET = "socket"
    PYTHON_API = "python-api"
    PROTOCOL = "protocol"
    FILE = "file"


class IPCMechanism(BaseModel):
    """A detected inter-process communication mechanism."""

    ipc_type: IPCType
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    details: dict[str, str] = Field(default_factory=dict)


class ParameterSpec(BaseModel):
    """A parameter for a capability or tool."""

    name: str
    type: str = "string"
    description: str = ""
    required: bool = True
    default: Optional[str] = None
    enum_values: Optional[list[str]] = None
    properties: Optional[list["ParameterSpec"]] = None  # nested fields for object types
    original_type: Optional[str] = None  # original language type name (e.g. "Fruit") for resolution


class Capability(BaseModel):
    """A high-level capability discovered in the application."""

    name: str
    description: str
    category: str = "general"
    parameters: list[ParameterSpec] = Field(default_factory=list)
    return_type: str = "string"
    source_file: str = ""
    source_function: str = ""
    source_class: str = ""
    init_params: list[ParameterSpec] = Field(default_factory=list)
    ipc_type: Optional[IPCType] = None
    http_method: Optional[str] = None  # e.g. "GET", "POST"
    http_path: Optional[str] = None  # e.g. "/api/users/{id}"


class AnalysisResult(BaseModel):
    """Complete output of the analysis phase."""

    app_name: str
    app_description: str = ""
    languages: list[Language] = Field(default_factory=list)
    files: list[FileInfo] = Field(default_factory=list)
    ipc_mechanisms: list[IPCMechanism] = Field(default_factory=list)
    capabilities: list[Capability] = Field(default_factory=list)
    primary_ipc: Optional[IPCType] = None
    entry_points: list[str] = Field(default_factory=list)
    raw_evidence: dict[str, list[str]] = Field(default_factory=dict)
