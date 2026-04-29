"""Models for the domain modeling phase (Phase 1)."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class UseCase(BaseModel):
    id: str
    description: str
    actor: str = "agent"
    data_objects: list[str] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    expected_outcome: str = ""


class GlossaryTerm(BaseModel):
    term: str
    definition: str
    aliases: list[str] = Field(default_factory=list)


class DataSource(BaseModel):
    kind: Literal["openapi", "grpc", "graphql", "db_schema", "sdk", "codebase", "other"]
    path: str
    parsed_raw: Optional[dict] = None


class DomainModel(BaseModel):
    server_name: str
    domain_description: str = ""
    use_cases: list[UseCase] = Field(default_factory=list)
    glossary: list[GlossaryTerm] = Field(default_factory=list)
    data_sources: list[DataSource] = Field(default_factory=list)
    domain_entities: list[str] = Field(default_factory=list)
    access_patterns: list[str] = Field(default_factory=list)
    approved: bool = False


class DomainBrief(BaseModel):
    """Input provided by the user to seed domain modeling."""

    server_name: str
    domain_description: str = ""
    use_cases: list[str] = Field(default_factory=list)  # free-text before LLM structuring
    glossary: dict[str, str] = Field(default_factory=dict)  # term → definition
    data_source_path: str = ""
    data_source_kind: Literal["openapi", "grpc", "graphql", "db_schema", "sdk", "codebase", "other"] = "other"
    auth_method: str = ""
    backend_target: Literal["fastmcp", "mcp-use"] = "fastmcp"
    eval_threshold: float = 0.80
