"""HTTP adapter: the server half of your old ``main.py``.

Deliberately thin. It reads bytes, hands them to an injected ``run`` function
(the per-request flow assembled in ``app.wiring``), and writes bytes back. It
contains no business logic and knows nothing about models or databases.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable, Tuple

Run = Callable[[bytes], Tuple[int, dict]]


def make_handler(run: Run, health_body: dict) -> type:
    """Build a handler class bound to the injected ``run`` and health payload.

    ``http.server`` mandates a class, so this corner is unavoidably OOP -- but
    it stays inside the shell and delegates every decision to ``run``.
    """

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", 0))
            status, body = run(self.rfile.read(length))
            self._reply(status, body)

        def do_GET(self) -> None:  # noqa: N802
            self._reply(200, health_body)

        def _reply(self, status: int, body: dict) -> None:
            encoded = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, *_args) -> None:  # keep demo output clean
            pass

    return Handler


def serve(host: str, port: int, handler_cls: type) -> None:
    """Start the blocking server. All the thinking already happened in pure
    functions; this only does I/O."""
    server = HTTPServer((host, port), handler_cls)
    print(f"Serving on http://{host}:{port}  (POST JSON with an 'applicant_id')")
    server.serve_forever()
