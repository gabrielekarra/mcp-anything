"""Models for the design phase output."""

from typing import Optional

from pydantic import BaseModel, Field

from mcp_anything.models.analysis import IPCType, ParameterSpec


class ToolImpl(BaseModel):
    """How to actually call the underlying application for this tool."""

    strategy: str = "stub"  # "cli_subcommand", "cli_function", "python_call", "http_call", "protocol_call", "stub"
    # For cli_subcommand: the subcommand name to pass to the app binary
    cli_subcommand: str = ""
    # For cli_function: the source file + function that wraps into a CLI call
    cli_entry: str = ""
    # For python_call: module path and function to import and call directly
    python_module: str = ""
    python_function: str = ""
    python_import_path: str = ""
    python_class: str = ""  # For instance methods: class to instantiate
    python_init_params: list[ParameterSpec] = Field(default_factory=list)  # __init__ params for auto-instantiation
    # For http_call: HTTP method and path
    http_method: str = ""  # GET, POST, PUT, DELETE, PATCH
    http_path: str = ""    # e.g. /api/users/{id}
    # For gRPC protocol_call tools: service class, RPC method, and stub module
    grpc_service: str = ""       # e.g. "UserService"
    grpc_method: str = ""        # e.g. "GetUser"
    grpc_proto_module: str = ""  # stem of the .proto file, e.g. "user"
    # Mapping of tool param names to CLI argument forms
    # e.g. {"input_path": {"position": 0}, "format": {"flag": "--format"}}
    arg_mapping: dict[str, dict] = Field(default_factory=dict)


class ToolSpec(BaseModel):
    """Specification for a single MCP tool."""

    name: str
    description: str
    parameters: list[ParameterSpec] = Field(default_factory=list)
    return_type: str = "string"
    module: str = ""
    ipc_type: Optional[IPCType] = None
    implementation_hint: str = ""
    generation_status: str = "ready"  # "ready", "proxy", "scaffolded", "stubbed"
    generation_notes: str = ""
    manual_steps: list[str] = Field(default_factory=list)
    impl: ToolImpl = Field(default_factory=ToolImpl)


class PromptSpec(BaseModel):
    """Specification for a server-delivered MCP prompt (skill)."""

    name: str
    description: str
    arguments: list[ParameterSpec] = Field(default_factory=list)
    template: str = ""  # The prompt template text


class ResourceSpec(BaseModel):
    """Specification for a single MCP resource."""

    uri: str
    name: str
    description: str
    mime_type: str = "application/json"
    resource_type: str = "generic"  # "status", "commands", "config", "docs", "generic"


class AuthConfig(BaseModel):
    """Authentication configuration for HTTP backends.

    All secrets are read from environment variables at runtime.
    """

    auth_type: str = ""  # "api_key", "bearer", "basic", or ""
    # For api_key: where to send the key
    api_key_header: str = ""  # e.g. "X-API-Key", "Authorization"
    api_key_query: str = ""   # e.g. "api_key" (query param name)
    # Env var names for secrets (values read at runtime, never stored)
    env_var_token: str = ""   # env var holding the token/key
    env_var_username: str = ""  # env var for basic auth username
    env_var_password: str = ""  # env var for basic auth password


class BackendConfig(BaseModel):
    """Configuration for the communication backend."""

    backend_type: IPCType
    host: str = "localhost"
    port: int = 0
    socket_path: str = ""
    command: str = ""
    command_args: list[str] = Field(default_factory=list)
    env_vars: dict[str, str] = Field(default_factory=dict)
    codebase_path: str = ""  # absolute path to the target app
    auth: AuthConfig = Field(default_factory=AuthConfig)


class ServerDesign(BaseModel):
    """Complete design for the generated MCP server."""

    server_name: str
    server_description: str = ""
    tools: list[ToolSpec] = Field(default_factory=list)
    resources: list[ResourceSpec] = Field(default_factory=list)
    prompts: list[PromptSpec] = Field(default_factory=list)
    tool_modules: dict[str, list[str]] = Field(default_factory=dict)
    backend: Optional[BackendConfig] = None
    dependencies: list[str] = Field(default_factory=lambda: ["mcp>=1.0"])
    python_requires: str = ">=3.10"
    target_install_hint: str = ""  # pip install instruction for the target app
    transport: str = "stdio"  # "stdio" or "http"
    http_host: str = "0.0.0.0"
    http_port: int = 8000
    enable_telemetry: bool = False
    generate_agents_md: bool = True
