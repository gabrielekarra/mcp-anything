"""IPC mechanism detectors."""

from mcp_anything.analysis.detectors.api_detector import APIDetector
from mcp_anything.analysis.detectors.base import Detector
from mcp_anything.analysis.detectors.cli_detector import CLIDetector
from mcp_anything.analysis.detectors.django_detector import DjangoDetector
from mcp_anything.analysis.detectors.express_detector import ExpressDetector
from mcp_anything.analysis.detectors.file_detector import FileDetector
from mcp_anything.analysis.detectors.flask_fastapi_detector import FlaskFastAPIDetector
from mcp_anything.analysis.detectors.go_web_detector import GoWebDetector
from mcp_anything.analysis.detectors.graphql_detector import GraphQLDetector
from mcp_anything.analysis.detectors.grpc_detector import GRPCDetector
from mcp_anything.analysis.detectors.jaxrs_detector import JaxRSDetector
from mcp_anything.analysis.detectors.micronaut_detector import MicronautDetector
from mcp_anything.analysis.detectors.openapi_detector import OpenAPIDetector
from mcp_anything.analysis.detectors.protocol_detector import ProtocolDetector
from mcp_anything.analysis.detectors.rails_detector import RailsDetector
from mcp_anything.analysis.detectors.rust_web_detector import RustWebDetector
from mcp_anything.analysis.detectors.socket_detector import SocketDetector
from mcp_anything.analysis.detectors.spring_detector import SpringDetector
from mcp_anything.analysis.detectors.zustand_detector import ZustandDetector

ALL_DETECTORS: list[type[Detector]] = [
    CLIDetector,
    SocketDetector,
    APIDetector,
    FlaskFastAPIDetector,
    OpenAPIDetector,
    ProtocolDetector,
    SpringDetector,
    JaxRSDetector,
    MicronautDetector,
    ExpressDetector,
    DjangoDetector,
    GoWebDetector,
    RailsDetector,
    RustWebDetector,
    GraphQLDetector,
    GRPCDetector,
    FileDetector,
    ZustandDetector,
]

__all__ = [
    "Detector",
    "CLIDetector",
    "SocketDetector",
    "APIDetector",
    "FlaskFastAPIDetector",
    "OpenAPIDetector",
    "ProtocolDetector",
    "SpringDetector",
    "JaxRSDetector",
    "MicronautDetector",
    "ExpressDetector",
    "DjangoDetector",
    "GoWebDetector",
    "RailsDetector",
    "RustWebDetector",
    "GraphQLDetector",
    "GRPCDetector",
    "FileDetector",
    "ZustandDetector",
    "ALL_DETECTORS",
]
