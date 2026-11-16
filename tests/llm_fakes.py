"""Fake model servers (Chat Completions and Ollama) for testing mcp_anything.llm offline."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class FakeModelServer:
    """Answers every request with the next scripted text (or `default`), and records the bodies."""

    def __init__(self, *texts, default="{}", status=200, finish="stop"):
        self.texts, self.default, self.status, self.finish = list(texts), default, status, finish
        self.requests = []  # (path, body, headers)
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                server.requests.append((self.path, body, dict(self.headers)))
                text = server.texts.pop(0) if server.texts else server.default
                if server.status != 200:
                    payload = {"error": {"message": text}}
                elif self.path.endswith("/api/chat"):
                    payload = {"message": {"role": "assistant", "content": text}, "done": True}
                else:
                    payload = {"choices": [{"message": {"role": "assistant", "content": text},
                                            "finish_reason": server.finish}]}
                data = json.dumps(payload).encode()
                self.send_response(server.status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self._server.server_port}"
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._server.shutdown()
        self._server.server_close()
