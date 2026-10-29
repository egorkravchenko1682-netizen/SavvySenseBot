"""Small, dependency-free HTTP server for Railway and Telegram Mini Apps."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import hmac
import json
import logging
import math
import os
from pathlib import Path
import time
import threading
from urllib.parse import parse_qsl, urlsplit


LOGGER = logging.getLogger(__name__)
WEBAPP_DIR = Path(__file__).resolve().parent
_BOT_TOKEN = ""
_SEARCH_CALLBACK = None
_ALLOWED_ORIGIN = ""
_RATE_LOCK = threading.Lock()
_RATE_HISTORY = {}
_RATE_LIMIT = 3
_RATE_WINDOW = 60
_SEARCH_SLOTS = threading.BoundedSemaphore(4)
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
        if urlsplit(self.path).path != "/api/search":
            return self._json(404, {"error": "Not found"})
        if not _BOT_TOKEN or not _SEARCH_CALLBACK:
            return self._json(503, {"error": "Поиск временно недоступен."})
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            return self._json(415, {"error": "Неверный формат запроса."})
        origin = self.headers.get("Origin", "").rstrip("/")
        if _ALLOWED_ORIGIN and origin != _ALLOWED_ORIGIN:
            return self._json(403, {"error": "Источник запроса не разрешён."})
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self._json(400, {"error": "Неверный запрос."})
        if length < 1 or length > 4096:
            return self._json(413, {"error": "Слишком большой запрос."})
        try:
            payload = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._json(400, {"error": "Не удалось прочитать запрос."})
        if not isinstance(payload, dict):
            return self._json(400, {"error": "Неверный запрос."})
        user_id = _validate_init_data(self.headers.get("X-Telegram-Init-Data", ""), _BOT_TOKEN)
        if user_id is None:
            return self._json(401, {"error": "Открой SAVVY через Telegram и повтори поиск."})
        if not self._allow_api_request(user_id):
            return self._json(429, {"error": "Слишком много запросов. Попробуй через минуту."})
        if not _SEARCH_SLOTS.acquire(blocking=False):
            return self._json(503, {"error": "Сейчас много поисков. Попробуй через несколько секунд."})
        try:
            result = _SEARCH_CALLBACK(user_id, payload)
        except ValueError as error:
            return self._json(400, {"error": str(error)[:180]})
        except RuntimeError as error:
            return self._json(429, {"error": str(error)[:180]})
        except Exception:
            # Keep search terms, URLs and provider exception content out of logs.
            LOGGER.error("Mini App search failed")
            return self._json(500, {"error": "Поиск не завершился. Попробуй ещё раз."})
        finally:
            _SEARCH_SLOTS.release()
        return self._json(200, result)

    @staticmethod
    def _allow_api_request(user_id):
        now = time.monotonic()
        with _RATE_LOCK:
            history = [stamp for stamp in _RATE_HISTORY.get(user_id, []) if now - stamp < _RATE_WINDOW]
            if len(history) >= _RATE_LIMIT:
                _RATE_HISTORY[user_id] = history
                return False
            history.append(now)
            _RATE_HISTORY[user_id] = history
            if len(_RATE_HISTORY) > 5000:
                for key in list(_RATE_HISTORY):
                    if not _RATE_HISTORY[key] or now - _RATE_HISTORY[key][-1] >= _RATE_WINDOW:
                        _RATE_HISTORY.pop(key, None)
            return True

    def _json(self, status, value):
        return self._send(status, json.dumps(_json_safe(value), ensure_ascii=False, allow_nan=False), "application/json; charset=utf-8")

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


def configure_api(bot_token, search_callback, origin=""):
    """Configure the authenticated, in-process Mini App API."""
    global _BOT_TOKEN, _SEARCH_CALLBACK, _ALLOWED_ORIGIN
    _BOT_TOKEN = str(bot_token or "")
    _SEARCH_CALLBACK = search_callback
    _ALLOWED_ORIGIN = str(origin or "").rstrip("/")


def _validate_init_data(raw, bot_token):
    """Verify Telegram Web App initData; never trust initDataUnsafe or client user IDs."""
    if not raw or len(raw) > 2048 or not bot_token:
        return None
    try:
        pairs = parse_qsl(raw, keep_blank_values=True, strict_parsing=True)
        values = dict(pairs)
        if len(values) != len(pairs):
            return None
        received_hash = values.pop("hash", "")
        auth_date = int(values.get("auth_date", "0"))
        now = time.time()
        if not received_hash or now - auth_date > 900 or auth_date > now + 30:
            return None
        check_string = "\n".join(f"{key}={value}" for key, value in sorted(values.items()))
        secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
        expected_hash = hmac.new(secret_key, check_string.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(received_hash, expected_hash):
            return None
        user = json.loads(values.get("user", "{}"))
        user_id = user.get("id") if isinstance(user, dict) else None
        return user_id if isinstance(user_id, int) and not isinstance(user_id, bool) and user_id > 0 else None
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def _json_safe(value):
    """Reject non-finite numeric values and reduce arbitrary objects to text."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(key)[:100]: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value[:10_000]]
    return str(value)[:500]
