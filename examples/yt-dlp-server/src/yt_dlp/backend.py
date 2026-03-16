"""Socket backend for yt-dlp."""

import asyncio
import json
from typing import Any


class Backend:
    """Communicates with yt-dlp via socket connection."""

    def __init__(self) -> None:
        self.host = "localhost"
        self.port = 0
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def connect(self) -> None:
        """Establish connection to the application."""
        self._reader, self._writer = await asyncio.open_connection(self.host, self.port)

    async def disconnect(self) -> None:
        """Close the connection."""
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()

    async def _ensure_connected(self) -> None:
        if self._writer is None or self._writer.is_closing():
            await self.connect()

    async def execute(self, tool_name: str, **kwargs: Any) -> str:
        """Send a command and receive the response."""
        await self._ensure_connected()
        assert self._reader and self._writer

        request = json.dumps({"method": tool_name, "params": kwargs})
        self._writer.write(request.encode() + b"\n")
        await self._writer.drain()

        response = await self._reader.readline()
        return response.decode().strip()

    async def query(self, uri: str) -> str:
        """Query a resource."""
        return await self.execute("query", uri=uri)
