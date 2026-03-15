"""Detect GraphQL schema and library patterns."""

import re
from pathlib import Path

from mcp_anything.models.analysis import FileInfo, IPCMechanism, IPCType, Language

from .base import Detector

# (regex, description, confidence, languages or None for all)
GRAPHQL_PATTERNS: list[tuple[str, str, float, set[Language] | None]] = [
    # SDL files (.graphql / .gql)
    (r"type\s+Query\s*\{", "GraphQL Query type definition", 0.95, {Language.GRAPHQL}),
    (r"type\s+Mutation\s*\{", "GraphQL Mutation type definition", 0.95, {Language.GRAPHQL}),
    # Python frameworks
    (r"import\s+graphene", "graphene import", 0.9, {Language.PYTHON}),
    (r"import\s+strawberry", "strawberry import", 0.9, {Language.PYTHON}),
    (r"import\s+ariadne", "ariadne import", 0.9, {Language.PYTHON}),
    # JS/TS frameworks
    (r"require\(['\"]graphql['\"]\)", "graphql require", 0.9, {Language.JAVASCRIPT, Language.TYPESCRIPT}),
    (r"from\s+['\"]graphql['\"]", "graphql import", 0.9, {Language.JAVASCRIPT, Language.TYPESCRIPT}),
    (r"require\(['\"]apollo-server['\"]\)", "apollo-server require", 0.9, {Language.JAVASCRIPT, Language.TYPESCRIPT}),
    (r"from\s+['\"]@apollo/server['\"]", "Apollo Server import", 0.9, {Language.JAVASCRIPT, Language.TYPESCRIPT}),
    (r"buildSchema\s*\(", "buildSchema call", 0.85, {Language.JAVASCRIPT, Language.TYPESCRIPT}),
    (r"makeExecutableSchema\s*\(", "makeExecutableSchema call", 0.9, {Language.JAVASCRIPT, Language.TYPESCRIPT}),
    (r"\btypeDefs\b", "typeDefs reference", 0.75, {Language.JAVASCRIPT, Language.TYPESCRIPT}),
]


class GraphQLDetector(Detector):
    @property
    def name(self) -> str:
        return "GraphQL Detector"

    def detect(self, root: Path, files: list[FileInfo]) -> list[IPCMechanism]:
        evidence: list[str] = []
        max_confidence = 0.0

        for fi in files:
            content = self._read_file(root, fi)
            if not content:
                continue

            for pattern, desc, conf, langs in GRAPHQL_PATTERNS:
                if langs is not None and fi.language not in langs:
                    continue
                if re.search(pattern, content):
                    evidence.append(f"{fi.path}: {desc}")
                    max_confidence = max(max_confidence, conf)

        if not evidence:
            return []

        return [
            IPCMechanism(
                ipc_type=IPCType.PROTOCOL,
                confidence=min(max_confidence, 1.0),
                evidence=evidence,
                details={"protocol": "graphql"},
            )
        ]
