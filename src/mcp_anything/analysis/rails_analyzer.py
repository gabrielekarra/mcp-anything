"""Regex-based analyzer for Ruby on Rails endpoints.

Extracts routes from config/routes.rb and controller actions from
app/controllers/*.rb files.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from mcp_anything.models.analysis import Capability, FileInfo, IPCType, Language, ParameterSpec
from mcp_anything.analysis.route_utils import endpoint_to_tool_name, make_description


# Standard RESTful actions and their HTTP methods
_RESOURCE_ACTIONS = {
    "index": ("GET", ""),
    "show": ("GET", "/{id}"),
    "create": ("POST", ""),
    "update": ("PUT", "/{id}"),
    "destroy": ("DELETE", "/{id}"),
}


@dataclass
class RailsEndpoint:
    """A route extracted from Rails source."""

    http_method: str
    path: str
    action_name: str
    controller: str
    description: str
    parameters: list[ParameterSpec]
    source_file: str


@dataclass
class RailsAnalysisResult:
    """Result of analyzing Ruby files for Rails routes."""

    routes: list[RailsEndpoint] = field(default_factory=list)
    controllers: list[str] = field(default_factory=list)


def _parse_routes_rb(root: Path) -> list[RailsEndpoint]:
    """Parse config/routes.rb for route definitions."""
    routes_file = root / "config" / "routes.rb"
    if not routes_file.exists():
        return []

    try:
        source = routes_file.read_text(errors="replace")
    except OSError:
        return []

    endpoints: list[RailsEndpoint] = []
    namespace_stack: list[str] = []

    # Track namespace/scope nesting
    for line in source.split("\n"):
        stripped = line.strip()

        # namespace :api do
        ns_match = re.match(r"namespace\s+:(\w+)", stripped)
        if ns_match:
            namespace_stack.append(ns_match.group(1))
            continue

        # scope '/api' do or scope :api do
        # Note: scope with variable expressions (e.g. scope MyApp.prefix do) are skipped
        scope_match = re.match(r"scope\s+['\"]/?(\w+)['\"]", stripped)
        if scope_match:
            namespace_stack.append(scope_match.group(1))
            continue

        # scope :api do (symbol form)
        scope_sym_match = re.match(r"scope\s+:(\w+)", stripped)
        if scope_sym_match:
            namespace_stack.append(scope_sym_match.group(1))
            continue

        # scope ... do with variable/expression — push placeholder so 'end' pops it
        if re.match(r"scope\s+\w[\w.]+\s+do", stripped):
            namespace_stack.append("")
            continue

        # end — pop namespace
        if stripped == "end" and namespace_stack:
            namespace_stack.pop()
            continue

        non_empty = [p for p in namespace_stack if p]
        prefix = "/" + "/".join(non_empty) if non_empty else ""

        # resources :users or resources :users, only: [:index, :show]
        res_match = re.match(r"resources?\s+:(\w+)(?:\s*,\s*only:\s*\[([^\]]+)\])?", stripped)
        if res_match:
            resource = res_match.group(1)
            only_str = res_match.group(2)

            if only_str:
                only_actions = [a.strip().strip(":").strip("'\"") for a in only_str.split(",")]
            else:
                only_actions = list(_RESOURCE_ACTIONS.keys())

            for action in only_actions:
                if action not in _RESOURCE_ACTIONS:
                    continue
                http_method, suffix = _RESOURCE_ACTIONS[action]
                path = f"{prefix}/{resource}{suffix}"

                params: list[ParameterSpec] = []
                if "{id}" in path:
                    params.append(ParameterSpec(name="id", type="integer", required=True))

                endpoints.append(RailsEndpoint(
                    http_method=http_method,
                    path=path,
                    action_name=action,
                    controller=f"{resource}_controller",
                    description=make_description(f"{action} {resource}"),
                    parameters=params,
                    source_file="config/routes.rb",
                ))
            continue

        # Explicit routes: get '/path', to: 'controller#action'
        # Also handles hash-rocket syntax: get '/path' => 'controller#action'
        # Controller may be namespaced: 'active_storage/blobs/redirect#show'
        explicit_match = re.match(
            r"(get|post|put|patch|delete)\s+['\"]([^'\"]+)['\"]\s*"
            r"(?:,\s*to:\s*|=>\s*)['\"]([^'\"#]+)[#/](\w+)['\"]",
            stripped,
        )
        if explicit_match:
            http_method = explicit_match.group(1).upper()
            path = prefix + explicit_match.group(2)
            controller = explicit_match.group(3)
            action = explicit_match.group(4)

            # Extract path params like :id
            params = []
            for param_match in re.finditer(r":(\w+)", path):
                param_name = param_match.group(1)
                if param_name != "to":
                    params.append(ParameterSpec(name=param_name, type="string", required=True))

            # Normalize :param to {param}
            normalized_path = re.sub(r":(\w+)", r"{\1}", path)

            endpoints.append(RailsEndpoint(
                http_method=http_method,
                path=normalized_path,
                action_name=action,
                controller=controller,
                description=make_description(f"{action} {controller}"),
                parameters=params,
                source_file="config/routes.rb",
            ))

    return endpoints


def _parse_controller_params(root: Path, controller_name: str) -> dict[str, list[str]]:
    """Extract permitted params from a controller's strong parameters."""
    params_by_action: dict[str, list[str]] = {}

    # Look for controller file
    for controller_file in root.rglob(f"*{controller_name}*.rb"):
        try:
            source = controller_file.read_text(errors="replace")
        except OSError:
            continue

        # params.require(:user).permit(:name, :email, :age)
        for match in re.finditer(
            r"params\.require\s*\(\s*:\w+\s*\)\.permit\s*\(([^)]+)\)",
            source,
        ):
            param_list = re.findall(r":(\w+)", match.group(1))
            # This typically applies to create/update actions
            params_by_action["create"] = param_list
            params_by_action["update"] = param_list

    return params_by_action


def analyze_rails_routes(root: Path) -> Optional[RailsAnalysisResult]:
    """Analyze a Rails project for routes and controllers."""
    routes = _parse_routes_rb(root)
    if not routes:
        return None

    result = RailsAnalysisResult(routes=routes)

    # Enrich with controller params
    seen_controllers: set[str] = set()
    for ep in routes:
        if ep.controller not in seen_controllers:
            seen_controllers.add(ep.controller)
            result.controllers.append(ep.controller)

            # Try to extract strong params
            controller_params = _parse_controller_params(root, ep.controller)
            for route in routes:
                if route.controller == ep.controller and route.action_name in controller_params:
                    existing_names = {p.name for p in route.parameters}
                    for field_name in controller_params[route.action_name]:
                        if field_name not in existing_names:
                            route.parameters.append(ParameterSpec(
                                name=field_name, type="string",
                                required=route.action_name == "create",
                            ))

    return result


def analyze_rails_file(
    root: Path, file_info: FileInfo,
) -> Optional[RailsAnalysisResult]:
    """Analyze a Ruby file for Rails controller actions."""
    if file_info.language != Language.RUBY:
        return None

    try:
        source = (root / file_info.path).read_text(errors="replace")
    except OSError:
        return None

    # Check if it's a controller
    if not re.search(r"class\s+\w+\s*<\s*(?:ApplicationController|ActionController)", source):
        return None

    # Extract controller name
    ctrl_match = re.search(r"class\s+(\w+Controller)", source)
    if not ctrl_match:
        return None

    controller_name = ctrl_match.group(1)
    result = RailsAnalysisResult(controllers=[controller_name])

    # Extract action methods (def index, def show, etc.)
    for match in re.finditer(r"def\s+(\w+)", source):
        action = match.group(1)
        if action.startswith("_") or action in ("initialize", "set_", "params"):
            continue

        # Only extract standard REST actions and custom ones
        if action in _RESOURCE_ACTIONS:
            http_method, suffix = _RESOURCE_ACTIONS[action]
            resource = controller_name.replace("Controller", "").lower()
            path = f"/{resource}{suffix}"

            params: list[ParameterSpec] = []
            if "{id}" in path:
                params.append(ParameterSpec(name="id", type="integer", required=True))

            result.routes.append(RailsEndpoint(
                http_method=http_method,
                path=path,
                action_name=action,
                controller=controller_name,
                description=make_description(f"{action} {resource}"),
                parameters=params,
                source_file=file_info.path,
            ))

    return result if result.routes else None


def rails_results_to_capabilities(
    results: dict[str, RailsAnalysisResult],
) -> list[Capability]:
    """Convert Rails analysis results into Capability objects."""
    capabilities: list[Capability] = []
    seen: set[str] = set()

    for file_path, result in results.items():
        for ep in result.routes:
            tool_name = endpoint_to_tool_name(ep.http_method, ep.path, ep.action_name)
            if tool_name in seen:
                continue
            seen.add(tool_name)

            capabilities.append(Capability(
                name=tool_name,
                description=ep.description,
                category="api",
                parameters=ep.parameters,
                return_type="object",
                source_file=file_path,
                source_function=ep.action_name,
                ipc_type=IPCType.PROTOCOL,
                http_method=ep.http_method,
                http_path=ep.path,
            ))

    return capabilities
