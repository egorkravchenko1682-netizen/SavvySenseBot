from urllib.parse import urlparse


def parse_url(url: str) -> dict:
    if not url:
        return {
            "type": "url",
            "value": "",
            "valid": False,
        }

    url = url.strip()

    try:
        parsed = urlparse(url)

        valid = (
            parsed.scheme in ("http", "https")
            and bool(parsed.netloc)
        )

    except Exception:
        valid = False

    return {
        "type": "url",
        "value": url,
        "domain": parsed.netloc if valid else None,
        "valid": valid,
    }