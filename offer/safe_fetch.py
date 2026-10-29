"""Bounded HTTP fetcher that refuses private and local network targets."""

from http.client import HTTPConnection, HTTPSConnection, HTTPException
import ipaddress
import socket
import time
from urllib.parse import urljoin, urlsplit, urlunsplit


MAX_URL_LENGTH = 4096
MAX_PAGE_BYTES = 1_000_000
MAX_REDIRECTS = 3
DEFAULT_TIMEOUT = 8


class UnsafePageError(ValueError):
    """The URL is malformed or resolves to a non-public network address."""


class _PinnedHTTPConnection(HTTPConnection):
    def __init__(self, host, port, address, timeout):
        super().__init__(host=host, port=port, timeout=timeout)
        self._address = address

    def connect(self):
        self.sock = socket.create_connection(
            (self._address, self.port),
            self.timeout,
            self.source_address,
        )


class _PinnedHTTPSConnection(HTTPSConnection):
    def __init__(self, host, port, address, timeout):
        super().__init__(host=host, port=port, timeout=timeout)
        self._address = address

    def connect(self):
        raw_socket = socket.create_connection(
            (self._address, self.port),
            self.timeout,
            self.source_address,
        )
        self.sock = self._context.wrap_socket(
            raw_socket,
            server_hostname=self.host,
        )


def _public_address(host, port):
    try:
        literal = ipaddress.ip_address(host)
        addresses = [str(literal)]
    except ValueError:
        try:
            records = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except OSError as error:
            raise UnsafePageError("Could not resolve page host") from error
        addresses = list(dict.fromkeys(record[4][0] for record in records))

    if not addresses:
        raise UnsafePageError("Page host has no addresses")

    parsed_addresses = []
    for address in addresses:
        try:
            parsed = ipaddress.ip_address(address.split("%", 1)[0])
        except ValueError as error:
            raise UnsafePageError("Page host resolved to an invalid address") from error
        if not parsed.is_global:
            raise UnsafePageError("Private and reserved network addresses are blocked")
        parsed_addresses.append(str(parsed))

    return parsed_addresses[0]


def _parse_public_url(url):
    if not isinstance(url, str) or len(url) > MAX_URL_LENGTH:
        raise UnsafePageError("Invalid page URL")

    try:
        parsed = urlsplit(url.strip())
        port = parsed.port
    except ValueError as error:
        raise UnsafePageError("Invalid page URL") from error

    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise UnsafePageError("Only HTTP and HTTPS pages are allowed")
    if not parsed.hostname or parsed.username or parsed.password:
        raise UnsafePageError("Invalid page host")

    expected_port = 443 if scheme == "https" else 80
    if port not in {None, expected_port}:
        raise UnsafePageError("Non-standard page ports are blocked")

    actual_port = port or expected_port
    address = _public_address(parsed.hostname, actual_port)
    clean_url = urlunsplit((scheme, parsed.netloc, parsed.path or "/", parsed.query, ""))
    return parsed, clean_url, actual_port, address


def fetch_public_html(url, headers=None, timeout=DEFAULT_TIMEOUT):
    """Fetch a public page without proxy use, unsafe redirects, or unbounded bodies.

    Returns ``(final_url, html_text)``. DNS results are validated and the
    connection is pinned to a validated public address to prevent rebinding.
    """

    try:
        timeout = min(max(float(timeout), 0.5), DEFAULT_TIMEOUT)
    except (TypeError, ValueError):
        timeout = DEFAULT_TIMEOUT

    current_url = url
    request_headers = {
        "User-Agent": "SAVVY SENSE product checker",
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.5",
        "Connection": "close",
    }
    for name, value in (headers or {}).items():
        if name.lower() not in {"host", "connection", "proxy-authorization", "proxy-connection"}:
            request_headers[name] = value

    for redirect_count in range(MAX_REDIRECTS + 1):
        parsed, current_url, port, address = _parse_public_url(current_url)
        connection_class = _PinnedHTTPSConnection if parsed.scheme == "https" else _PinnedHTTPConnection
        connection = connection_class(parsed.hostname, port, address, timeout)
        try:
            target = urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
            connection.request("GET", target, headers=request_headers)
            response = connection.getresponse()

            if response.status in {301, 302, 303, 307, 308}:
                location = response.getheader("Location")
                response.close()
                if not location or redirect_count >= MAX_REDIRECTS:
                    raise UnsafePageError("Too many or invalid page redirects")
                current_url = urljoin(current_url, location)
                continue

            if response.status < 200 or response.status >= 300:
                raise UnsafePageError("Page returned an unsuccessful status")

            content_length = response.getheader("Content-Length")
            if content_length:
                try:
                    if int(content_length) > MAX_PAGE_BYTES:
                        raise UnsafePageError("Page is too large")
                except ValueError as error:
                    raise UnsafePageError("Invalid page size") from error

            deadline = time.monotonic() + timeout
            body_parts = []
            total_bytes = 0
            while total_bytes <= MAX_PAGE_BYTES:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise UnsafePageError("Page download timed out")
                connection.sock.settimeout(remaining)
                chunk = response.read(min(64 * 1024, MAX_PAGE_BYTES + 1 - total_bytes))
                if not chunk:
                    break
                body_parts.append(chunk)
                total_bytes += len(chunk)
            if total_bytes > MAX_PAGE_BYTES:
                raise UnsafePageError("Page is too large")
            body = b"".join(body_parts)

            charset = response.headers.get_content_charset() or "utf-8"
            return current_url, body.decode(charset, errors="replace")
        except (OSError, HTTPException, UnicodeError) as error:
            if isinstance(error, UnsafePageError):
                raise
            raise UnsafePageError("Page could not be fetched safely") from error
        finally:
            connection.close()

    raise UnsafePageError("Too many page redirects")
