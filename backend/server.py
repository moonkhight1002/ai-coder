from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .app import LeetCodeCopilotApp


APP = LeetCodeCopilotApp()


class ApiHandler(BaseHTTPRequestHandler):
    server_version = "LeetBot/0.1"

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self._write_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._send_json(HTTPStatus.OK, APP.health())
            return
        if self.path == "/api/state":
            self._send_json(HTTPStatus.OK, APP.state())
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:
        payload = self._read_json()
        if self.path == "/api/solve":
            try:
                response = APP.solve(payload)
            except Exception as exc:  # pragma: no cover - defensive API surface
                self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})
                return
            self._send_json(HTTPStatus.OK, response)
            return
        if self.path == "/api/stop":
            self._send_json(HTTPStatus.OK, APP.stop())
            return
        if self.path == "/api/settings":
            self._send_json(HTTPStatus.OK, APP.update_settings(payload))
            return
        if self.path == "/api/provider":
            self._send_json(HTTPStatus.OK, APP.configure_provider(payload))
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def log_message(self, format: str, *args) -> None:
        return

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw else {}

    def _send_json(self, status: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self._write_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _write_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def main() -> None:
    host = os.getenv("LEETBOT_HOST", "127.0.0.1")
    port = int(os.getenv("LEETBOT_PORT", "8765"))
    try:
        server = ThreadingHTTPServer((host, port), ApiHandler)
    except OSError as exc:
        print(f"Failed to start backend on http://{host}:{port}")
        print(f"Reason: {exc}")
        print("If the port is already in use, close the old backend or set LEETBOT_PORT to a different port.")
        raise SystemExit(1) from exc

    print(f"LeetCode study copilot backend running on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
