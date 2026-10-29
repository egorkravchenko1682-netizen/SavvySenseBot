import pytest
from unittest.mock import patch

from offer.safe_fetch import UnsafePageError, fetch_public_html


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/admin",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/",
        "file:///etc/passwd",
        "https://user:pass@example.com/product",
        "http://example.com:8080/product",
    ],
)
def test_fetch_rejects_unsafe_url_without_network_access(url):
    with pytest.raises(UnsafePageError):
        fetch_public_html(url)


def test_fetch_rejects_hostname_resolving_to_private_address():
    private_dns_answer = [
        (2, 1, 6, "", ("10.20.30.40", 443)),
    ]
    with patch("offer.safe_fetch.socket.getaddrinfo", return_value=private_dns_answer):
        with pytest.raises(UnsafePageError):
            fetch_public_html("https://product.example/item")
