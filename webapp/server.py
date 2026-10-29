"""Small, dependency-free HTTP server for Railway and Telegram Mini Apps."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import logging
import os
from pathlib import Path
import threading
from urllib.parse import urlsplit


LOGGER = logging.getLogger(__name__)
WEBAPP_DIR = Path(__file__).resolve().parent
ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


class MiniAppHandler(BaseHTTPRequestHandler):
    server_version = "SAVVY"
    sys_version = ""

    def do_GET(self):
        self._serve(head_only=False)

    def do_HEAD(self):
        self._serve(head_only=True)

    def do_POST(self):
        self._send(405, "Method not allowed", "text/plain; charset=utf-8", extra={"Allow": "GET, HEAD"})

    def _serve(self, head_only):
        try:
            path = urlsplit(self.path).path
        except ValueError:
            return self._send(400, "Bad request", "text/plain; charset=utf-8")

        if path == "/health":
            return self._send(200, "ok", "text/plain; charset=utf-8", head_only=head_only)

        asset = ASSETS.get(path)
        if asset is None:
            return self._send(404, "Not found", "text/plain; charset=utf-8")

        filename, content_type = asset
        try:
            body = (WEBAPP_DIR / filename).read_bytes()
        except OSError:
            LOGGER.exception("Unable to read Mini App asset")
            return self._send(500, "App unavailable", "text/plain; charset=utf-8")

        self._send(200, body, content_type, head_only=head_only)

    def _send(self, status, body, content_type, head_only=False, extra=None):
        payload = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Strict-Transport-Security", "max-age=31536000")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' https://telegram.org; "
            "style-src 'self'; img-src 'self' data:; connect-src 'self'; "
            "base-uri 'none'; form-action 'self'; "
            "frame-ancestors 'self' https://*.telegram.org",
        )
        for name, value in (extra or {}).items():
            self.send_header(name, value)
        self.end_headers()
        if not head_only:
            self.wfile.write(payload)

    def log_message(self, _format, *_args):
        # Avoid writing user IPs or request paths to Railway logs.
        return


def start_server():
    host = "0.0.0.0"
    port = int(os.getenv("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), MiniAppHandler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, name="savvy-mini-app", daemon=True)
    thread.start()
    LOGGER.info("Mini App HTTP server listening on %s:%s", host, port)
    return server
