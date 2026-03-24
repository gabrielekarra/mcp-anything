"""HTTP backend for github-scoped."""

import base64
import json
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("github-scoped")

# Configurable via environment variables
_ENV_PREFIX = "GITHUB_SCOPED"
_DEFAULT_TIMEOUT = 30
_DEFAULT_MAX_RETRIES = 3
_RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


class BackendError(Exception):
    """Structured error from the HTTP backend."""

    def __init__(
        self,
        message: str,
        status_code: int = 0,
        method: str = "",
        path: str = "",
        response_body: str = "",
    ) -> None:
        self.status_code = status_code
        self.method = method
        self.path = path
        self.response_body = response_body
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": str(self),
            "status_code": self.status_code,
            "method": self.method,
            "path": self.path,
            "response_body": self.response_body,
        }


class Backend:
    """Communicates with github-scoped via HTTP REST API."""

    def __init__(self) -> None:
        self.base_url = os.environ.get(
            f"{_ENV_PREFIX}_BASE_URL",
            "http://localhost:0",
        )
        self.timeout = float(os.environ.get(
            f"{_ENV_PREFIX}_TIMEOUT", str(_DEFAULT_TIMEOUT),
        ))
        self.max_retries = int(os.environ.get(
            f"{_ENV_PREFIX}_MAX_RETRIES", str(_DEFAULT_MAX_RETRIES),
        ))
        self._client: httpx.AsyncClient | None = None

    def _build_auth_headers(self) -> dict[str, str]:
        """Build authentication headers from environment variables."""
        headers: dict[str, str] = {}
        token = os.environ.get("GITHUB_TOKEN", "")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self._build_auth_headers(),
            )
        return self._client

    def _build_query_auth(self) -> dict[str, str]:
        """Build query parameter authentication if configured."""
        params: dict[str, str] = {}
        return params

    async def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        path_params: dict[str, str] | None = None,
    ) -> str:
        """Make an HTTP request to the target application.

        Retries on transient errors (429, 5xx) with exponential backoff.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH).
            path: URL path, may contain {placeholders}.
            params: Query parameters.
            body: JSON request body.
            path_params: Values for {placeholder} path segments.
        """
        # Substitute path parameters
        if path_params:
            for key, value in path_params.items():
                path = path.replace("{" + key + "}", str(value))

        # Merge query auth params
        query_auth = self._build_query_auth()
        if query_auth:
            params = {**(params or {}), **query_auth}

        client = await self._get_client()
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await client.request(
                    method=method,
                    url=path,
                    params=params,
                    json=body if body else None,
                )

                # Retry on transient HTTP errors
                if response.status_code in _RETRY_STATUS_CODES and attempt < self.max_retries - 1:
                    wait = 2 ** attempt  # 1s, 2s, 4s...
                    logger.warning(
                        "HTTP %s %s returned %d, retrying in %ds (attempt %d/%d)",
                        method, path, response.status_code, wait, attempt + 1, self.max_retries,
                    )
                    import asyncio
                    await asyncio.sleep(wait)
                    continue

                # Non-retryable error
                if response.status_code >= 400:
                    body_text = response.text
                    raise BackendError(
                        f"HTTP {response.status_code} from {method} {path}",
                        status_code=response.status_code,
                        method=method,
                        path=path,
                        response_body=body_text[:1000],
                    )

                # Success — return pretty JSON or raw text
                try:
                    return json.dumps(response.json(), indent=2)
                except Exception:
                    return response.text

            except httpx.TimeoutException:
                last_error = BackendError(
                    f"Request timed out after {self.timeout}s: {method} {path}",
                    method=method,
                    path=path,
                )
                if attempt < self.max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning(
                        "Timeout on %s %s, retrying in %ds (attempt %d/%d)",
                        method, path, wait, attempt + 1, self.max_retries,
                    )
                    import asyncio
                    await asyncio.sleep(wait)
                    continue
                raise last_error

            except httpx.ConnectError:
                last_error = BackendError(
                    f"Cannot connect to {self.base_url}: is the target application running?",
                    method=method,
                    path=path,
                )
                if attempt < self.max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning(
                        "Connection failed for %s %s, retrying in %ds (attempt %d/%d)",
                        method, path, wait, attempt + 1, self.max_retries,
                    )
                    import asyncio
                    await asyncio.sleep(wait)
                    continue
                raise last_error

            except BackendError:
                raise

            except httpx.HTTPError as exc:
                raise BackendError(
                    f"HTTP error on {method} {path}: {exc}",
                    method=method,
                    path=path,
                ) from exc

        # Should not reach here, but just in case
        raise last_error or BackendError(f"Request failed after {self.max_retries} attempts")

    async def execute(self, method: str, **kwargs: Any) -> str:
        """Compatibility shim for scaffolded protocol-style tools on HTTP backends."""
        raise BackendError(
            f"HTTP backend for github-scoped has no protocol mapping for '{method}'. "
            "Generate concrete HTTP routes or implement Backend.execute() manually.",
            method=method,
        )

    async def query(self, uri: str) -> str:
        """Query a resource by URI."""
        return await self.execute("query", uri=uri)
